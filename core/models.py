from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum, Max
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

# ---- JSON uyumluluğu
try:
    from django.db.models import JSONField as BaseJSONField
except Exception:
    from django.contrib.postgres.fields import JSONField as BaseJSONField


# =========================
# Ortak Seçenekler
# =========================

class Currency(models.TextChoices):
    USD = "USD", "USD"
    EUR = "EUR", "EUR"
    TRY = "TRY", "TRY"


# =========================
# Coğrafya
# =========================

class Country(models.Model):
    name = models.CharField(max_length=120, unique=True)
    iso2 = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=120)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="cities")

    class Meta:
        unique_together = ("name", "country")
        ordering = ["country__name", "name"]

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class Airport(models.Model):
    name = models.CharField(max_length=160)
    iata = models.CharField(max_length=3, unique=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="airports")

    class Meta:
        ordering = ["iata"]

    def __str__(self):
        return f"{self.iata} – {self.name}"


# =========================
# Havayolu & Uçuş
# =========================

class Airline(models.Model):
    name = models.CharField(max_length=120, unique=True)
    logo = models.ImageField(upload_to="airlines/logos/", blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Flight(models.Model):
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, related_name="flights")
    flight_number = models.CharField(max_length=12)
    origin = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="departures")
    destination = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="arrivals")

    # SAAT alanları (tarih yok)
    departure_time = models.TimeField(blank=True, null=True)
    arrival_time = models.TimeField(blank=True, null=True)

    duration_minutes = models.PositiveIntegerField(help_text="Toplam uçuş süresi (dakika)")

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)

    class Meta:
        ordering = ["departure_time"]

    def __str__(self):
        return f"{self.flight_number} {self.origin.iata}→{self.destination.iata}"


# =========================
# Tour
# =========================

class Tour(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    overview = models.TextField(blank=True)
    info = models.TextField(blank=True)

    places_covered = models.ManyToManyField(City, blank=True, related_name="tours")
    arrival_flight = models.ForeignKey(
        Flight, on_delete=models.SET_NULL, null=True, blank=True, related_name="as_arrival_for_tours"
    )
    departure_flight = models.ForeignKey(
        Flight, on_delete=models.SET_NULL, null=True, blank=True, related_name="as_departure_for_tours"
    )

    days = models.ManyToManyField(
        "Day",
        through="TourDay",
        blank=True,
        related_name="tours_for",
    )

    flights_count = models.PositiveIntegerField(default=0)
    hotels_count = models.PositiveIntegerField(default=0)
    activities_count = models.PositiveIntegerField(default=0)

    commission = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("1.00")), MaxValueValidator(Decimal("2.00"))],
        help_text="Toplam gün fiyatı ile çarpılacak katsayı (1.00–2.00)"
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    compare_at_currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)

    badge_text = models.CharField(max_length=60, blank=True)

    tour_types = models.ManyToManyField("TourType", blank=True, related_name="tours")

    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    # --- counters ---
    def recompute_item_counts(self, save: bool = True):
        day_ids = list(self.days.values_list("id", flat=True))
        flights = DayFlight.objects.filter(day_id__in=day_ids).count()
        hotels = DayHotel.objects.filter(day_id__in=day_ids).count()
        activities = DayActivity.objects.filter(day_id__in=day_ids).count()

        self.flights_count = flights
        self.hotels_count = hotels
        self.activities_count = activities
        if save:
            self.save(update_fields=["flights_count", "hotels_count", "activities_count"])

    # --- start/end points (Day -> City) ---
    @property
    def start_point(self):
        td = (
            TourDay.objects.filter(tour=self)
            .select_related("day__city")
            .order_by("order", "id")
            .first()
        )
        return td.day.city.name if td and td.day and td.day.city else None

    @property
    def end_point(self):
        td = (
            TourDay.objects.filter(tour=self)
            .select_related("day__city")
            .order_by("-order", "-id")
            .first()
        )
        return td.day.city.name if td and td.day and td.day.city else None

    @property
    def total_days(self):
        td = self.tour_days.count()
        if td:
            return td
        return Day.objects.filter(city__in=self.places_covered.all()).count()

    @property
    def duration_label(self):
        d = self.total_days
        if d <= 0:
            return ""
        nights = max(d - 1, 0)
        return f"{d} Gün / {nights} Gece"

    def days_total_amount(self) -> Decimal:
        # ❗️ in_tours yerine TourDay üzerinden bağlan
        agg = Day.objects.filter(tourday__tour=self).aggregate(total=Sum("price"))
        return Decimal(agg["total"] or 0).quantize(Decimal("0.01"))

    def recompute_price(self, save=True):
        base = self.days_total_amount()
        self.price = (base * (self.commission or Decimal("1.00"))).quantize(Decimal("0.01"))
        if save:
            self.save(update_fields=["price"])

    # --- alt toplam hesaplayıcılar ---
    def flights_total(self) -> Decimal:
        total = (
            Flight.objects.filter(dayflight__day__in=self.days.all())
            .aggregate(t=Sum("price"))
            .get("t")
        )
        return total or Decimal("0.00")

    def transfers_total(self) -> Decimal:
        total = (
            AirportTransfer.objects.filter(daytransfer__day__in=self.days.all())
            .aggregate(t=Sum("price"))
            .get("t")
        )
        return total or Decimal("0.00")

    def hotels_total(self) -> Decimal:
        total = (
            Hotel.objects.filter(dayhotel__day__in=self.days.all())
            .aggregate(t=Sum("price_per_night"))
            .get("t")
        )
        return total or Decimal("0.00")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class TourDay(models.Model):
    tour = models.ForeignKey("Tour", on_delete=models.CASCADE, related_name="tour_days")
    day = models.ForeignKey("Day", on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, db_index=True)
    title = models.CharField("Day Title", max_length=255, blank=True)

    class Meta:
        ordering = ("order", "id")

    def save(self, *args, **kwargs):
        # boş order’a artan değer ata
        if not self.order:
            last = TourDay.objects.filter(tour=self.tour).aggregate(m=Max("order"))["m"] or 0
            self.order = last + 1
        # title boşsa otomatik üret
        if not self.title:
            base = (self.day.title or (self.day.city.name if getattr(self.day, "city", None) else "Program"))
            self.title = f"Day {self.order}: {base}"
        super().save(*args, **kwargs)


class TourPhoto(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="tours/photos/")
    alt_text = models.CharField(max_length=160, blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.tour.title} Photo #{self.pk}"

    def clean(self):
        if self.tour_id and self.tour.photos.exclude(pk=self.pk).count() >= 10:
            raise ValidationError("Bir tur için en fazla 10 fotoğraf yüklenebilir.")


class TourType(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# =========================
# Reusable Bullets & Tour Sections
# =========================

class Bullet(models.Model):
    class Icon(models.TextChoices):
        CHECK = "check", "Check"
        ARROW = "arrow", "Arrow"
        INFO = "info", "Info"

    text = models.CharField(max_length=300, unique=True)
    icon = models.CharField(max_length=12, choices=Icon.choices, default=Icon.CHECK)
    tags = models.CharField(max_length=160, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["text"]

    def __str__(self):
        return self.text


class TourBullet(models.Model):
    class Section(models.TextChoices):
        HIGHLIGHTS = "highlights", "Tour Highlights"
        MORE_ABOUT = "more_about", "More About"

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="tour_bullets")
    bullet = models.ForeignKey(Bullet, on_delete=models.PROTECT, related_name="usages")
    section = models.CharField(max_length=20, choices=Section.choices)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["section", "order", "id"]
        unique_together = ("tour", "bullet", "section")
        indexes = [models.Index(fields=["tour", "section"])]

    def __str__(self):
        return f"{self.tour} · {self.get_section_display()} · {self.bullet.text[:40]}"


# =========================
# Day + Eklenebilir Öğeler
# =========================

class Day(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="days")
    day_number = models.PositiveIntegerField(help_text="Şehir içindeki sıra (1..N)")
    title = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    bullets = BaseJSONField(blank=True, null=True, help_text="List[str] – 5..10 madde (opsiyonel)")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, editable=False)
    price_currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)

    flights = models.ManyToManyField("Flight", through="DayFlight", blank=True, related_name="days")
    transfers = models.ManyToManyField("AirportTransfer", through="DayTransfer", blank=True, related_name="days")
    hotels = models.ManyToManyField("Hotel", through="DayHotel", blank=True, related_name="days")
    activities = models.ManyToManyField("Activity", through="DayActivity", blank=True, related_name="days")

    def recompute_price(self, save=True):
        total = Decimal("0.00")
        total += Decimal(self.dayflight_set.select_related("flight").aggregate(s=Sum("flight__price"))["s"] or 0)
        total += Decimal(self.daytransfer_set.select_related("transfer").aggregate(s=Sum("transfer__price"))["s"] or 0)
        total += Decimal(self.dayhotel_set.select_related("hotel").aggregate(s=Sum("hotel__price_per_night"))["s"] or 0)
        total += Decimal(self.dayactivity_set.select_related("activity").aggregate(s=Sum("activity__price"))["s"] or 0)
        self.price = total.quantize(Decimal("0.01"))
        if save:
            self.save(update_fields=["price"])

    class Meta:
        unique_together = ("city", "day_number")
        ordering = ["city__country__name", "city__name", "day_number"]

    def __str__(self):
        return f"{self.city} – Day {self.day_number}"

    def clean(self):
        if self.bullets is not None:
            if not isinstance(self.bullets, (list, tuple)):
                raise ValidationError({"bullets": "Bullets bir liste olmalıdır."})
            ln = len(self.bullets)
            if ln < 5 or ln > 10:
                raise ValidationError({"bullets": "5 ile 10 arasında madde gereklidir."})


class DayImage(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="days/photos/")
    alt_text = models.CharField(max_length=160, blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.day} Image #{self.pk}"

    def clean(self):
        if self.day_id and self.day.images.exclude(pk=self.pk).count() >= 3:
            raise ValidationError("Bir gün için en fazla 3 fotoğraf yüklenebilir.")


class Hotel(models.Model):
    HOTEL_TYPE_CHOICES = [
        ("hotel", "Hotel"),
        ("hostel", "Hostel"),
    ]
    name = models.CharField(max_length=120)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    star = models.PositiveSmallIntegerField(default=3)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    price_currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)
    hotel_type = models.CharField(max_length=10, choices=HOTEL_TYPE_CHOICES, default="hotel")
    image = models.ImageField(upload_to="hotels/", blank=True, null=True)

    class Meta:
        ordering = ["city__name", "name"]

    def __str__(self):
        return f"{self.name} – {self.city}"


class Order(models.Model):
    tour = models.ForeignKey("Tour", on_delete=models.CASCADE, related_name="orders")
    pax = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    email = models.EmailField(blank=True, null=True, help_text="Customer contact e-mail for this order")

    # Tarihler (kullanıcı seçimi)
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)

    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)

    same_room = models.BooleanField(default=True)
    hide_flights = models.BooleanField(default=False)
    hide_transfers = models.BooleanField(default=False)
    hide_hotels = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def compute_total(self):
        t = self.tour
        try:
            commission = Decimal(str(t.commission)) if t.commission is not None else Decimal("1")
        except Exception:
            commission = Decimal("1")

        flights = Decimal(t.flights_total() or 0) if not self.hide_flights else Decimal("0")
        transfers = Decimal(t.transfers_total() or 0) if not self.hide_transfers else Decimal("0")
        hotels = Decimal(t.hotels_total() or 0) if not self.hide_hotels else Decimal("0")

        activities = Decimal("0")
        if hasattr(t, "days"):
            for d in t.days.all():
                for da in d.dayactivity_set.all():
                    price = getattr(da.activity, "price", None)
                    if price:
                        activities += Decimal(price)

        pax_dec = Decimal(self.pax)
        m_flights = pax_dec
        m_activities = pax_dec
        m_transfers = Decimal("1")
        if self.hide_hotels:
            m_hotels = Decimal("0")
        else:
            if self.pax == 2:
                m_hotels = Decimal("1") if self.same_room else Decimal("2")
            else:
                m_hotels = Decimal("1")

        net_total = (
            flights * m_flights +
            activities * m_activities +
            hotels * m_hotels +
            transfers * m_transfers
        )
        grand = (net_total * commission)
        self.total_price = grand.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return self.total_price

    def mark_paid(self):
        self.is_paid = True
        self.save(update_fields=["is_paid"])

    def __str__(self):
        return f"{self.tour.title} — {self.pax} pax ({'Paid' if self.is_paid else 'Pending'})"


class AirportTransfer(models.Model):
    class Direction(models.TextChoices):
        A2H = "A2H", "Airport → Hotel"
        H2A = "H2A", "Hotel → Airport"

    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="transfers")
    airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="airport_transfers")
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT, related_name="hotel_transfers")
    direction = models.CharField(max_length=3, choices=Direction.choices, default=Direction.A2H)

    vehicle_type = models.CharField(max_length=80, default="Sedan")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    price_currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)

    class Meta:
        ordering = ["city__name", "direction"]

    def __str__(self):
        arrow = "→" if self.direction == self.Direction.A2H else "←"
        return f"{self.city} transfer {self.airport.iata} {arrow} {self.hotel.name}"


class Activity(models.Model):
    title = models.CharField(max_length=180)
    location_text = models.CharField(max_length=160, blank=True)
    points = BaseJSONField(blank=True, null=True, help_text="List[str] – madde listesi")
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cover_image = models.ImageField(upload_to="activities/photos/", blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Traveler(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="travelers")
    title = models.CharField(max_length=10, blank=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    passport_no = models.CharField(max_length=40, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    dob = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.order_id})"


class DayFlight(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE)
    flight = models.ForeignKey(Flight, on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["day", "order"]
        unique_together = ("day", "flight")


class DayTransfer(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE)
    transfer = models.ForeignKey(AirportTransfer, on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["day", "order"]
        unique_together = ("day", "transfer")


class DayHotel(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["day", "order"]
        unique_together = ("day", "hotel")


class DayActivity(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["day", "order"]
        unique_together = ("day", "activity")


# --- Day içindeki through kayıtları değişince Day fiyatını yeniden hesapla
@receiver(post_save, sender=DayFlight)
@receiver(post_delete, sender=DayFlight)
@receiver(post_save, sender=DayTransfer)
@receiver(post_delete, sender=DayTransfer)
@receiver(post_save, sender=DayHotel)
@receiver(post_delete, sender=DayHotel)
@receiver(post_save, sender=DayActivity)
@receiver(post_delete, sender=DayActivity)
def _recalc_day_total_on_components_change(sender, instance, **kwargs):
    day = instance.day
    day.recompute_price()
    # ❗️Bu günü içeren tüm tur id'leri
    tour_ids = (
        TourDay.objects.filter(day=day)
        .values_list("tour_id", flat=True)
        .distinct()
    )
    for tid in tour_ids:
        try:
            Tour.objects.get(pk=tid).recompute_price()
        except Tour.DoesNotExist:
            pass


# --- Bileşenlerin fiyatı değişirse onları kullanan Day’leri güncelle
def _recompute_days_for_qs(qs):
    day_ids = qs.values_list("day_id", flat=True).distinct()
    for day in Day.objects.filter(pk__in=day_ids):
        day.recompute_price()
        tour_ids = (
            TourDay.objects.filter(day=day)
            .values_list("tour_id", flat=True)
            .distinct()
        )
        for tid in tour_ids:
            try:
                Tour.objects.get(pk=tid).recompute_price()
            except Tour.DoesNotExist:
                pass


@receiver(post_save, sender=Flight)
def _recalc_when_flight_price_changes(sender, instance, **kwargs):
    qs = DayFlight.objects.filter(flight=instance)
    _recompute_days_for_qs(qs)


@receiver(post_save, sender=AirportTransfer)
def _recalc_when_transfer_price_changes(sender, instance, **kwargs):
    qs = DayTransfer.objects.filter(transfer=instance)
    _recompute_days_for_qs(qs)


@receiver(post_save, sender=Hotel)
def _recalc_when_hotel_price_changes(sender, instance, **kwargs):
    qs = DayHotel.objects.filter(hotel=instance)
    _recompute_days_for_qs(qs)


@receiver(post_save, sender=Activity)
def _recalc_when_activity_price_changes(sender, instance, **kwargs):
    qs = DayActivity.objects.filter(activity=instance)
    _recompute_days_for_qs(qs)


# ------------- SIGNAL YARDIMCILARI -------------

def _recompute_for_day(day_id: int):
    tour_ids = (
        TourDay.objects
        .filter(day_id=day_id)
        .values_list("tour_id", flat=True)
        .distinct()
    )
    for tid in tour_ids:
        try:
            tour = Tour.objects.get(pk=tid)
            tour.recompute_item_counts(save=True)
        except Tour.DoesNotExist:
            pass


# ------------- SIGNAL’LAR -------------

@receiver([post_save, post_delete], sender=TourDay)
def _tourday_changed(sender, instance, **kwargs):
    instance.tour.recompute_item_counts(save=True)


@receiver([post_save, post_delete], sender=DayFlight)
def _dayflight_changed(sender, instance, **kwargs):
    if instance.day_id:
        _recompute_for_day(instance.day_id)


@receiver([post_save, post_delete], sender=DayHotel)
def _dayhotel_changed(sender, instance, **kwargs):
    if instance.day_id:
        _recompute_for_day(instance.day_id)


@receiver([post_save, post_delete], sender=DayActivity)
def _dayactivity_changed(sender, instance, **kwargs):
    if instance.day_id:
        _recompute_for_day(instance.day_id)
