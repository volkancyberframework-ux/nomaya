from decimal import Decimal

from django.contrib import admin
from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase
from django.utils.html import format_html

from .models import (
    Country, City, Airport, Airline, Flight,
    Tour, TourDay, TourPhoto, Bullet, TourBullet,
    Day, DayImage, Hotel, AirportTransfer,
    Activity, DayFlight, DayTransfer, DayHotel, DayActivity,
    Order, Traveler, TourType, ActivityProgress,IntroAudioLibrary, OrderIntroAudio
)

from .models import LiveLocation

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import UserProfile

from .models import WhatsAppMessageTemplate, WhatsAppMessageQueue

User = get_user_model()



class OrderIntroAudioInline(admin.TabularInline):
    model = OrderIntroAudio
    extra = 1
    fields = ("title", "audio", "source_name", "generated", "created_at")
    readonly_fields = ("created_at",)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    fields = (
        "miles",
        "force_password_change",
        "password_changed_at",
    )
    readonly_fields = ("password_changed_at",)
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    inlines = (UserProfileInline,)

    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "nomaya_miles",
        "force_password_change_status",
        "is_staff",
        "is_active",
    )

    @admin.display(description="Nomaya Milleri")
    def nomaya_miles(self, obj):
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return profile.miles

    @admin.display(description="Parola Değiştirsin mi?")
    def force_password_change_status(self, obj):
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return profile.force_password_change

    force_password_change_status.boolean = True

@admin.register(LiveLocation)
class LiveLocationAdmin(admin.ModelAdmin):
    list_display = ("session_id", "latitude", "longitude", "accuracy", "ip_address", "updated_at")
    search_fields = ("session_id", "ip_address", "user_agent")
    list_filter = ("updated_at",)

# ─────────────────────────────
# Helpers
# ─────────────────────────────
def admin_id(obj):
    return obj.pk
admin_id.short_description = "ID"


# ─────────────────────────────
# Custom Filters
# ─────────────────────────────
class TourFilterForActivity(admin.SimpleListFilter):
    title = "Tour"
    parameter_name = "tour"

    def lookups(self, request, model_admin):
        return [(t.id, f"#{t.id} - {t.title}") for t in Tour.objects.order_by("title")]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(days__tourday__tour_id=self.value()).distinct()
        return queryset


class DayFilterForActivity(admin.SimpleListFilter):
    title = "Day"
    parameter_name = "day"

    def lookups(self, request, model_admin):
        return [
            (d.id, f"#{d.id} - {d.city.name} - Day {d.day_number} - {d.title or d.city.name}")
            for d in Day.objects.select_related("city").order_by("city__name", "day_number")
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(days__id=self.value()).distinct()
        return queryset


class TourFilterForDay(admin.SimpleListFilter):
    title = "Tour"
    parameter_name = "tour"

    def lookups(self, request, model_admin):
        return [(t.id, f"#{t.id} - {t.title}") for t in Tour.objects.order_by("title")]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tourday__tour_id=self.value()).distinct()
        return queryset


# ─────────────────────────────
# Travelers
# ─────────────────────────────
class TravelerInline(admin.TabularInline):
    model = Traveler
    extra = 0
    fields = ("admin_id", "title", "first_name", "last_name", "dob", "passport_no", "phone")
    readonly_fields = ("admin_id",)
    ordering = ("id",)

    def admin_id(self, obj):
        return obj.pk or "New"
    admin_id.short_description = "ID"

class ActivityProgressInline(admin.TabularInline):
    model = ActivityProgress
    extra = 0
    fields = (
        "admin_id",
        "day_activity",
        "activity_title",
        "status",
        "telegram_sent",
        "updated_at",
    )
    readonly_fields = (
        "admin_id",
        "activity_title",
        "updated_at",
    )
    autocomplete_fields = ("day_activity",)
    ordering = ("day_activity__day_id", "day_activity__order")

    def admin_id(self, obj):
        return obj.pk or "New"
    admin_id.short_description = "ID"

    def activity_title(self, obj):
        if obj.day_activity_id and obj.day_activity.activity_id:
            return obj.day_activity.activity.title
        return "-"
    activity_title.short_description = "Activity"

@admin.register(Traveler)
class TravelerAdmin(admin.ModelAdmin):
    list_display = (
        "id", "order", "title", "first_name", "last_name",
        "dob", "passport_no", "phone", "created_at"
    )
    list_filter = ("title", "order__tour", "created_at")
    search_fields = (
        "id", "first_name", "last_name", "passport_no", "phone",
        "order__id", "order__tour__title"
    )
    ordering = ("id",)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "tour", "pax", "email",
        "earned_miles_display",
        "total_possible_miles_display",
        "progress_summary_display",
        "payment_method", "link_payment_status",
        "total_price", "is_paid",
        "tracking_enabled",
        "tracking_code",
        "tracking_code_expires_at",
        "tracking_started_at",
        "tracking_last_seen",
        "start_date", "end_date",
        "created_at",
        "miles_payment_status",
        "custom_intro_audio",
    )

    list_display_links = ("id", "tour")
    ordering = ("-created_at",)
    inlines = [
    TravelerInline,
    ActivityProgressInline,
    OrderIntroAudioInline,
    ]

    list_filter = (
        "is_paid",
        "tracking_enabled",
        "payment_method",
        "link_payment_accepted",
        "same_room",
        "hide_flights",
        "hide_transfers",
        "hide_hotels",
        ("start_date", admin.DateFieldListFilter),
        ("end_date", admin.DateFieldListFilter),
        ("created_at", admin.DateFieldListFilter),
        "tour",
        "miles_payment_requested",
    )

    search_fields = (
        "id", "public_id", "email", "tour__title",
        "tracking_code",
    )

    readonly_fields = (
        "id",
        "public_id",
        "created_at",
        "tracking_started_at",
        "tracking_last_seen",
        "earned_miles_display",
        "total_possible_miles_display",
        "progress_summary_display",
    )

    fieldsets = (
        ("Bağlantı", {
            "fields": ("id", "tour", "public_id", "session_key")
        }),

        ("Müşteri", {
            "fields": ("email", "pax", "same_room")
        }),

        ("Kişisel Ses", {
            "fields": (
                "custom_intro_audio",
            )
        }),

        ("Tarihler", {
            "fields": ("start_date", "end_date")
        }),

        ("Mil / Aktivite Durumu", {
            "fields": (
                "earned_miles_display",
                "total_possible_miles_display",
                "progress_summary_display",
            )
        }),

        ("Konum Takibi", {
            "fields": (
                "tracking_enabled",
                "tracking_code",
                "tracking_code_expires_at",
                "tracking_started_at",
                "tracking_last_seen",
            )
        }),

        ("Görünürlük / Dahiller", {
            "fields": ("hide_flights", "hide_transfers", "hide_hotels")
        }),

        ("Ödeme", {
            "fields": (
                "payment_method",
                "link_payment_accepted",
                "miles_payment_requested",
                "miles_payment_requested_at",
                "total_price",
                "is_paid",
                "created_at",
            )
        }),
    )
    def miles_payment_status(self, obj):
        requested = getattr(obj, "miles_payment_requested", False)

        if obj.payment_method == "miles_payment" or requested:
            if requested:
                return format_html('<b style="color:green;">Talep edildi</b>')
            return format_html('<b style="color:red;">Talep yok</b>')

        return "-"

    miles_payment_status.short_description = "Mil Ödeme Talebi"

    def link_payment_status(self, obj):
        if obj.payment_method == "payment_link":
            color = "green" if obj.link_payment_accepted else "red"
            text = "Evet" if obj.link_payment_accepted else "Hayır"
            return format_html('<b style="color:{}">{}</b>', color, text)
        return "-"
    link_payment_status.short_description = "Link Ödemesi Onaylı mı?"

    def earned_miles_display(self, obj):
        return f"{obj.earned_miles} mil"
    earned_miles_display.short_description = "Kazanılan Mil"

    def total_possible_miles_display(self, obj):
        if not obj.tour_id:
            return "0 mil"
        return f"{obj.tour.total_miles_reward} mil"
    total_possible_miles_display.short_description = "Toplam Kazanılabilir Mil"

    def progress_summary_display(self, obj):
        total = ActivityProgress.objects.filter(order=obj).count()
        completed = ActivityProgress.objects.filter(
            order=obj,
            status=ActivityProgress.Status.COMPLETED
        ).count()
        skipped = ActivityProgress.objects.filter(
            order=obj,
            status=ActivityProgress.Status.SKIPPED
        ).count()

        return f"{completed}/{total} tamamlandı, {skipped} atlandı"
    progress_summary_display.short_description = "Aktivite Durumu"
# ─────────────────────────────
# Tour inlines
# ─────────────────────────────
class TourDayInline(admin.TabularInline):
    model = TourDay
    extra = 0
    fields = ("admin_id", "day", "order", "title")
    readonly_fields = ("admin_id",)
    ordering = ("order", "id")

    def admin_id(self, obj):
        return obj.pk or "New"
    admin_id.short_description = "ID"


class TourPhotoInline(SortableInlineAdminMixin, admin.TabularInline):
    model = TourPhoto
    extra = 1
    max_num = 10
    fields = ("admin_id", "order", "image", "alt_text")
    readonly_fields = ("admin_id",)
    ordering = ("order",)

    def admin_id(self, obj):
        return obj.pk or "New"
    admin_id.short_description = "ID"


class TourBulletInline(SortableInlineAdminMixin, admin.TabularInline):
    model = TourBullet
    extra = 1
    autocomplete_fields = ("bullet",)
    fields = ("admin_id", "section", "bullet", "order")
    readonly_fields = ("admin_id",)
    ordering = ("section", "order")

    def admin_id(self, obj):
        return obj.pk or "New"
    admin_id.short_description = "ID"


# ─────────────────────────────
# Day inlines
# ─────────────────────────────
class DayImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = DayImage
    extra = 1
    max_num = 3
    fields = ("admin_id", "order", "image", "alt_text")
    readonly_fields = ("admin_id",)
    ordering = ("order",)

    def admin_id(self, obj):
        return obj.pk or "New"
    admin_id.short_description = "ID"


class DayFlightInline(SortableInlineAdminMixin, admin.TabularInline):
    model = DayFlight
    extra = 0
    autocomplete_fields = ("flight",)
    fields = ("admin_id", "order", "flight", "flight_price")
    readonly_fields = ("admin_id", "flight_price")
    ordering = ("order",)

    def admin_id(self, obj):
        return obj.pk or "New"
    admin_id.short_description = "ID"

    def flight_price(self, obj):
        f = getattr(obj, "flight", None)
        if not f:
            return "—"
        return f"{f.price} {getattr(f, 'price_currency', '')}".strip()
    flight_price.short_description = "Flight Price"


class DayTransferInline(SortableInlineAdminMixin, admin.TabularInline):
    model = DayTransfer
    extra = 0
    autocomplete_fields = ("transfer",)
    fields = ("admin_id", "order", "transfer", "transfer_price")
    readonly_fields = ("admin_id", "transfer_price")
    ordering = ("order",)

    def admin_id(self, obj):
        return obj.pk or "New"
    admin_id.short_description = "ID"

    def transfer_price(self, obj):
        t = getattr(obj, "transfer", None)
        if not t:
            return "—"
        return f"{t.price} {getattr(t, 'price_currency', '')}".strip()
    transfer_price.short_description = "Transfer Price"


class DayHotelInline(SortableInlineAdminMixin, admin.TabularInline):
    model = DayHotel
    extra = 0
    autocomplete_fields = ("hotel",)
    fields = ("admin_id", "order", "hotel", "hotel_price")
    readonly_fields = ("admin_id", "hotel_price")
    ordering = ("order",)

    def admin_id(self, obj):
        return obj.pk or "New"
    admin_id.short_description = "ID"

    def hotel_price(self, obj):
        h = getattr(obj, "hotel", None)
        if not h:
            return "—"
        return f"{h.price_per_night} {getattr(h, 'price_currency', '')}".strip()
    hotel_price.short_description = "Hotel Price / Night"


class DayActivityInline(SortableInlineAdminMixin, admin.TabularInline):
    model = DayActivity
    extra = 0
    autocomplete_fields = ("activity",)
    fields = ("admin_id", "order", "activity", "activity_price")
    readonly_fields = ("admin_id", "activity_price")
    ordering = ("order",)

    def admin_id(self, obj):
        return obj.pk or "New"
    admin_id.short_description = "ID"

    def activity_price(self, obj):
        a = getattr(obj, "activity", None)
        price = getattr(a, "price", None)
        currency = getattr(a, "price_currency", None)
        return f"{price} {currency}".strip() if price is not None and currency else "—"
    activity_price.short_description = "Activity Price"


# ─────────────────────────────
# Tour admin
# ─────────────────────────────
@admin.register(Tour)
class TourAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = (
        "id", "title", "duration_label", "days_total_for_list",
        "commission", "price", "price_currency", "is_published",
        "allow_flights", "allow_hotels", "allow_transfers"
    )
    list_display_links = ("id", "title")
    list_filter = (
        "is_published",
        "places_covered__country",
        "places_covered",
        "price_currency",
        "tour_types",
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = ("id", "title", "overview", "info", "places_covered__name", "tour_types__name")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("places_covered", "tour_types")

    readonly_fields = ("id", "duration_label", "start_point", "end_point", "days_total_preview",)
    fields = (
        "id",
        "title", "slug", "is_published", "badge_text",

        ("allow_flights", "allow_hotels", "allow_transfers"),

        ("start_date", "end_date"),
        "overview", "info",
        "places_covered",
        "tour_types",
        ("arrival_flight", "departure_flight"),
        ("commission", "price_currency"),
        "days_total_preview",
        "price",
    )
    inlines = [TourDayInline, TourPhotoInline, TourBulletInline]

    def days_total_for_list(self, obj):
        return obj.days_total_amount()
    days_total_for_list.short_description = "Days Total"

    def days_total_preview(self, obj):
        base = obj.days_total_amount() if obj.pk else Decimal("0.00")
        comm = obj.commission or Decimal("1.00")
        try:
            preview = (Decimal(base) * Decimal(comm)).quantize(Decimal("0.01"))
        except Exception:
            preview = base
        return f"Days Total: {base} × Commission ({comm}) → Price = {preview}"
    days_total_preview.short_description = "Computed Price Preview"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.recompute_price()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recompute_price()
        form.instance.recompute_item_counts(save=True)


# ─────────────────────────────
# Day admin
# ─────────────────────────────
@admin.register(Day)
class DayAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ("id", "city", "day_number", "title", "price", "price_currency")
    list_display_links = ("id", "city")
    list_filter = (
        TourFilterForDay,
        "city__country",
        "city",
        "price_currency",
    )
    search_fields = (
        "id",
        "title",
        "description",
        "city__name",
        "city__country__name",
        "tourday__tour__title",
    )
    readonly_fields = ("id", "price",)
    inlines = [DayImageInline, DayFlightInline, DayTransferInline, DayHotelInline, DayActivityInline]


# ─────────────────────────────
# Through / Inline Models Admin
# ─────────────────────────────
@admin.register(TourDay)
class TourDayAdmin(admin.ModelAdmin):
    list_display = ("id", "tour", "day", "order", "title")
    list_display_links = ("id", "tour")
    list_filter = ("tour", "day__city", "day__city__country")
    search_fields = ("id", "tour__title", "day__title", "day__city__name", "title")
    autocomplete_fields = ("tour", "day")
    ordering = ("tour", "order", "id")


@admin.register(DayFlight)
class DayFlightAdmin(admin.ModelAdmin):
    list_display = ("id", "day", "flight", "order")
    list_display_links = ("id", "day")
    list_filter = ("day__city", "day__city__country", "flight__airline")
    search_fields = ("id", "day__title", "day__city__name", "flight__flight_number")
    autocomplete_fields = ("day", "flight")
    ordering = ("day", "order", "id")


@admin.register(DayTransfer)
class DayTransferAdmin(admin.ModelAdmin):
    list_display = ("id", "day", "transfer", "order")
    list_display_links = ("id", "day")
    list_filter = ("day__city", "day__city__country", "transfer__city")
    search_fields = ("id", "day__title", "day__city__name", "transfer__vehicle_type")
    autocomplete_fields = ("day", "transfer")
    ordering = ("day", "order", "id")


@admin.register(DayHotel)
class DayHotelAdmin(admin.ModelAdmin):
    list_display = ("id", "day", "hotel", "order")
    list_display_links = ("id", "day")
    list_filter = ("day__city", "day__city__country", "hotel__city")
    search_fields = ("id", "day__title", "day__city__name", "hotel__name")
    autocomplete_fields = ("day", "hotel")
    ordering = ("day", "order", "id")


@admin.register(DayActivity)
class DayActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "day", "activity", "order", "day_city", "activity_city")
    list_display_links = ("id", "day")
    list_filter = ("day__city", "day__city__country", "activity__city", "activity__city__country")
    search_fields = (
        "id",
        "day__title",
        "day__city__name",
        "activity__title",
        "activity__city__name",
    )
    autocomplete_fields = ("day", "activity")
    ordering = ("day", "order", "id")

    def day_city(self, obj):
        return obj.day.city if obj.day_id else "-"
    day_city.short_description = "Day City"

    def activity_city(self, obj):
        return obj.activity.city if obj.activity_id else "-"
    activity_city.short_description = "Activity City"


# ─────────────────────────────
# Basit modeller
# ─────────────────────────────
@admin.register(Bullet)
class BulletAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "icon", "is_active", "tags")
    list_display_links = ("id", "text")
    list_filter = ("icon", "is_active", "tags")
    search_fields = ("id", "text", "tags")


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "iso2")
    list_display_links = ("id", "name")
    list_filter = ("iso2",)
    search_fields = ("id", "name", "iso2")


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "country")
    list_display_links = ("id", "name")
    list_filter = ("country",)
    search_fields = ("id", "name", "country__name")


@admin.register(TourType)
class TourTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")
    search_fields = ("id", "name")


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("id", "iata", "name", "city")
    list_display_links = ("id", "iata")
    list_filter = ("city__country", "city")
    search_fields = ("id", "iata", "name", "city__name", "city__country__name")


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")
    search_fields = ("id", "name")


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        "id", "flight_number", "airline", "origin", "destination",
        "departure_time", "arrival_time", "duration_minutes",
        "price", "price_currency"
    )
    list_display_links = ("id", "flight_number")
    list_filter = (
        "airline",
        "origin__city__country",
        "origin__city",
        "destination__city__country",
        "destination__city",
        "price_currency",
    )
    search_fields = (
        "id",
        "flight_number",
        "airline__name",
        "origin__iata",
        "destination__iata",
        "origin__name",
        "destination__name",
    )


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "star", "hotel_type", "price_per_night", "price_currency")
    list_display_links = ("id", "name")
    list_filter = ("city__country", "city", "star", "hotel_type", "price_currency")
    search_fields = ("id", "name", "address", "city__name", "city__country__name")


@admin.register(AirportTransfer)
class AirportTransferAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "direction", "airport", "hotel", "vehicle_type", "price", "price_currency")
    list_display_links = ("id", "city")
    list_filter = (
        "city__country",
        "city",
        "direction",
        "vehicle_type",
        "airport",
        "hotel",
        "price_currency",
    )
    search_fields = (
        "id",
        "airport__iata",
        "airport__name",
        "hotel__name",
        "city__name",
        "vehicle_type",
    )


# ─────────────────────────────
# Activity admin
# ─────────────────────────────
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "city", "duration_hours", "price", "price_currency",
        "tour_types_list", "connected_days", "connected_tours"
    )
    list_display_links = ("id", "title")

    list_filter = (
        TourFilterForActivity,
        DayFilterForActivity,
        ("city__country", admin.RelatedOnlyFieldListFilter),
        ("city", admin.RelatedOnlyFieldListFilter),
        "price_currency",
        ("tour_types", admin.RelatedOnlyFieldListFilter),
    )

    search_fields = (
        "id",
        "title",
        "location_text",
        "city__name",
        "city__country__name",
        "tour_types__name",
        "days__title",
        "days__city__name",
        "days__tourday__tour__title",
    )

    autocomplete_fields = ("city",)
    filter_horizontal = ("tour_types",)

    def tour_types_list(self, obj):
        return ", ".join(obj.tour_types.values_list("name", flat=True))
    tour_types_list.short_description = "Tour Types"

    def connected_days(self, obj):
        items = obj.dayactivity_set.select_related("day", "day__city").values_list(
            "id",
            "day__id",
            "day__day_number",
            "day__title",
            "day__city__name",
        ).distinct()

        if not items:
            return "-"

        return ", ".join([
            f"DayActivity #{da_id} | Day #{day_id} | {city} / Day {day_number} - {title or city}"
            for da_id, day_id, day_number, title, city in items
        ])
    connected_days.short_description = "Connected Days"

    def connected_tours(self, obj):
        tours = Tour.objects.filter(
            tour_days__day__dayactivity__activity=obj
        ).distinct()

        if not tours.exists():
            return "-"

        return ", ".join([f"#{t.id} - {t.title}" for t in tours])

    connected_tours.short_description = "Connected Tours"

@admin.register(ActivityProgress)
class ActivityProgressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "tracking_code",
        "tour",
        "day_activity",
        "activity_title",
        "activity_miles",
        "day_title",
        "status",
        "telegram_sent",
        "updated_at",
        "created_at",
    )

    list_display_links = ("id", "order")

    list_filter = (
        "status",
        "telegram_sent",
        "order__tour",
        "day_activity__day__city",
        "updated_at",
        "created_at",
    )

    search_fields = (
        "id",
        "order__tracking_code",
        "order__email",
        "order__tour__title",
        "day_activity__activity__title",
        "day_activity__day__title",
        "day_activity__day__city__name",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "tracking_code",
        "tour",
        "activity_title",
        "activity_miles",
        "day_title",
    )

    autocomplete_fields = (
        "order",
        "day_activity",
    )

    ordering = ("-updated_at",)

    fieldsets = (
        ("Progress", {
            "fields": (
                "id",
                "order",
                "tracking_code",
                "tour",
                "day_activity",
                "activity_title",
                "activity_miles",
                "day_title",
                "status",
                "note",
                "telegram_sent",
            )
        }),
        ("Tarih", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    def tracking_code(self, obj):
        return obj.order.tracking_code if obj.order_id else "-"
    tracking_code.short_description = "Tracking Code"

    def tour(self, obj):
        return obj.order.tour.title if obj.order_id and obj.order.tour_id else "-"
    tour.short_description = "Tour"

    def activity_title(self, obj):
        if obj.day_activity_id and obj.day_activity.activity_id:
            return obj.day_activity.activity.title
        return "-"
    activity_title.short_description = "Activity"

    def activity_miles(self, obj):
        if obj.day_activity_id and obj.day_activity.activity_id:
            return obj.day_activity.activity.miles_reward or 0
        return 0
    activity_miles.short_description = "Mil"

    def day_title(self, obj):
        if obj.day_activity_id and obj.day_activity.day_id:
            return obj.day_activity.day.title or str(obj.day_activity.day)
        return "-"
    day_title.short_description = "Day"

from .models import ActivityProgressLocationLog


@admin.register(ActivityProgressLocationLog)
class ActivityProgressLocationLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tracking_code",
        "order",
        "activity_title",
        "action",
        "latitude",
        "longitude",
        "accuracy",
        "created_at",
    )

    list_filter = (
        "action",
        "created_at",
    )

    search_fields = (
        "tracking_code",
        "order__email",
        "day_activity__activity__title",
        "session_id",
        "ip_address",
    )

    readonly_fields = (
        "order",
        "activity_progress",
        "day_activity",
        "tracking_code",
        "action",
        "latitude",
        "longitude",
        "accuracy",
        "session_id",
        "user_agent",
        "ip_address",
        "created_at",
    )

    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def activity_title(self, obj):
        if obj.day_activity and obj.day_activity.activity:
            return obj.day_activity.activity.title
        return "-"
    activity_title.short_description = "Activity"


@admin.register(WhatsAppMessageTemplate)
class WhatsAppMessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("key", "title", "is_active", "updated_at")
    search_fields = ("key", "title", "body")
    list_filter = ("is_active",)


@admin.register(WhatsAppMessageQueue)
class WhatsAppMessageQueueAdmin(admin.ModelAdmin):
    list_display = (
        "id", "phone", "status", "order", "day_activity",
        "sent_at", "failed_at", "created_at",
    )
    list_filter = ("status", "created_at", "sent_at")
    search_fields = (
        "phone", "chat_id", "message",
        "order__tracking_code", "order__email",
    )
    readonly_fields = (
        "chat_id", "waha_response", "error_message",
        "locked_at", "sent_at", "failed_at", "created_at",
    )

from .models import CustomizedTravelRequest, CustomizedTravelSettings

@admin.register(CustomizedTravelSettings)
class CustomizedTravelSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "stripe_payment_link", "is_active")


@admin.register(CustomizedTravelRequest)
class CustomizedTravelRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "location",
        "days",
        "total_price",
        "payment_clicked",
        "is_paid",
        "created_at",
    )

    list_editable = (
        "is_paid",
    )

    list_filter = (
        "is_paid",
        "payment_clicked",
    )

@admin.register(IntroAudioLibrary)
class IntroAudioLibraryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "title", "audio", "is_active", "created_at")
    list_filter = ("is_active", "name")
    search_fields = ("name", "title")


@admin.register(OrderIntroAudio)
class OrderIntroAudioAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "title", "source_name", "generated", "created_at")
    search_fields = ("order__id", "order__email", "source_name", "title")
    list_filter = ("generated", "source_name", "created_at")
