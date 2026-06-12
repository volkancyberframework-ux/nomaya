from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.db.models import Q
from django.utils.dateparse import parse_date
from .models import Tour
from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from .models import Tour, TourPhoto, TourDay, Day, DayImage, DayFlight, DayTransfer, DayHotel, DayActivity, TourType
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Tour, Order,  Traveler
from .forms import OrderForm
from decimal import Decimal
from django.db.models import Sum
import re
from datetime import datetime
from django.core.paginator import Paginator
from django.shortcuts import render
# core/views.py
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.dateparse import parse_date

from .models import Tour, Country, TourType  # <-- TourType eklendi
# core/views.py
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from .models import Tour, Country, TourType
from typing import Optional
from django.utils.dateparse import parse_date
import re
from typing import Optional
from datetime import date, datetime
from .utils import get_order_for_request_by_public
from .utils import ensure_session, get_order_for_request_by_public
from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, Sum
from decimal import Decimal
from datetime import timedelta
import locale
from django.db.models import Count

from .models import (
    Tour, TourPhoto, TourDay, DayImage, DayFlight,
    DayTransfer, DayHotel, DayActivity
)
from .utils import _parse_dates_param  # eğer ayrı utils'te tanımlıysa
from django.utils import translation


User = get_user_model()

from django.utils import translation
from django.db.models import Prefetch

def tour_booking_detail_public(request, public_id):
    order = get_order_for_request_by_public(request, public_id)
    tour = order.tour

    # Başlangıç günü (opsiyonel)
    try:
        start_day_number = int(request.GET.get("start_day", "1"))
    except (TypeError, ValueError):
        start_day_number = 1

    # Günler + bağlı kayıtlar
    tour_days = (
        TourDay.objects.filter(tour=tour)
        .select_related("day", "day__city", "day__city__country")
        .prefetch_related(
            Prefetch("day__images", queryset=DayImage.objects.order_by("order", "id")),
            Prefetch("day__dayflight_set", queryset=DayFlight.objects.select_related(
                "flight", "flight__airline", "flight__origin", "flight__destination"
            ).order_by("order", "id")),
            Prefetch("day__daytransfer_set", queryset=DayTransfer.objects.select_related(
                "transfer", "transfer__airport", "transfer__hotel", "transfer__hotel__city"
            ).order_by("order", "id")),
            Prefetch("day__dayhotel_set", queryset=DayHotel.objects.select_related(
                "hotel", "hotel__city"
            ).order_by("order", "id")),
            Prefetch("day__dayactivity_set", queryset=DayActivity.objects.select_related(
                "activity"
            ).order_by("order", "id")),
        )
        .order_by("order", "id")
    )

    # Varlık bayrakları
    day_ids = list(tour_days.values_list("day_id", flat=True))
    has_flights    = DayFlight.objects.filter(day_id__in=day_ids).exists()
    has_transfers  = DayTransfer.objects.filter(day_id__in=day_ids).exists()
    has_hotels     = DayHotel.objects.filter(day_id__in=day_ids).exists()
    has_activities = DayActivity.objects.filter(day_id__in=day_ids).exists()

    # Step 2’de yolcu kartları için [1..pax]
    traveler_indices = range(1, (order.pax or 1) + 1)

    ctx = {
        "order": order,
        "tour": tour,
        "tour_days": tour_days,
        "start_day_number": start_day_number,
        "pax": order.pax,
        "per_person": (order.total_price / order.pax) if order.pax else order.total_price,
        "total": order.total_price,
        "has_flights": has_flights,
        "has_transfers": has_transfers,
        "has_hotels": has_hotels,
        "has_activities": has_activities,
        "traveler_indices": traveler_indices,
    }

    # Tarih/ay adları Türkçe görünsün
    with translation.override("tr"):
        return render(request, "tour-booking.html", ctx)

@require_http_methods(["POST"])
def save_travelers_public(request, public_id):
    order = get_order_for_request_by_public(request, public_id)
    count = int(request.POST.get("traveler_count", order.pax) or order.pax)

    # start_day korunacak
    start_day = request.GET.get("start_day") or request.POST.get("start_day")

    ddmmyyyy = re.compile(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/[0-9]{4}$")

    created = []
    for i in range(1, count + 1):
        data = request.POST.get(f"traveler[{i}][first_name]")
        if data is None:
            continue

        title = (request.POST.get(f"traveler[{i}][title]") or "").strip()
        first_name = (request.POST.get(f"traveler[{i}][first_name]") or "").strip()
        last_name  = (request.POST.get(f"traveler[{i}][last_name]") or "").strip()
        passport   = (request.POST.get(f"traveler[{i}][passport_no]") or "").strip()
        phone      = (request.POST.get(f"traveler[{i}][phone]") or "").strip()
        dob_str    = (request.POST.get(f"traveler[{i}][dob]") or "").strip()

        if not ddmmyyyy.match(dob_str):
            messages.error(request, f"Traveler {i}: DoB must be DD/MM/YYYY")
            q = {"step": "2"}
            if start_day: q["start_day"] = start_day
            return redirect(reverse("tour_booking_detail_public", args=[order.public_id]) + "?" + urlencode(q))

        dob = datetime.strptime(dob_str, "%d/%m/%Y").date()

        Traveler.objects.create(
            order=order,
            title=title,
            first_name=first_name,
            last_name=last_name,
            passport_no=passport,
            phone=phone,
            dob=dob,
        )
        created.append(i)

    messages.success(request, f"{len(created)} traveler saved.")
    q = {"step": "3"}
    if start_day: q["start_day"] = start_day
    return redirect(reverse("tour_booking_detail_public", args=[order.public_id]) + "?" + urlencode(q))

def order_success_public(request, public_id):
    order = get_order_for_request_by_public(request, public_id)
    return render(request, "order_success.html", {"order": order})


def tour_list(request):
    qs_all = Tour.objects.all()
    # ... filtrelerin ...
    paginator = Paginator(qs_all, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    # page paramını düşürerek mevcut filtreleri koru
    params = request.GET.copy()
    params.pop("page", None)
    qs_without_page = urlencode(params)

    return render(request, "tour-grid.html", {
        "tours": page_obj.object_list,
        "paginator": paginator,
        "page_obj": page_obj,
        "qs": qs_without_page,   # <-- template’te kullanacağız
    })


@require_http_methods(["GET", "POST"])
def sign_in(request):
    if request.user.is_authenticated:
        # Zaten giriş yaptıysa home'a
        return redirect("home")

    next_url = request.GET.get("next") or request.POST.get("next") or ""

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        remember = request.POST.get("remember") == "on"

        # Email'den kullanıcıyı bul
        user = User.objects.filter(email__iexact=email).first()
        if user:
            # Django backend'ini kullanarak doğrula (username ile)
            auth_user = authenticate(request, username=user.get_username(), password=password)
        else:
            auth_user = None

        if auth_user is not None:
            login(request, auth_user)

            # "Beni hatırla": işaretli değilse tarayıcı kapanınca oturum düşsün
            if not remember:
                request.session.set_expiry(0)  # browser close
            # işaretliyse varsayılan SESSION_COOKIE_AGE geçerli olur

            return redirect(next_url or "home")
        else:
            messages.error(request, "E-posta veya parola hatalı.")

    return render(request, "sign-in.html", {"next": next_url})

@require_http_methods(["GET", "POST"])
def sign_up(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        password2 = request.POST.get("password2") or ""

        errors = {}
        if not email:
            errors["email"] = "E-posta zorunludur."
        elif User.objects.filter(email__iexact=email).exists():
            errors["email"] = "Bu e-posta ile zaten bir hesap var."
        if not password:
            errors["password"] = "Parola zorunludur."
        elif len(password) < 8:
            errors["password"] = "Parola en az 8 karakter olmalıdır."
        if password != password2:
            errors["password2"] = "Parolalar eşleşmiyor."

        if not errors:
            try:
                username_field = getattr(User, "USERNAME_FIELD", "username")
                extra = {}
                if username_field != "email":
                    base = (email.split("@")[0] or "user").replace(" ", "")[:30] or "user"
                    candidate = base
                    n = 0
                    while User.objects.filter(**{username_field: candidate}).exists():
                        n += 1
                        candidate = f"{base}{n}"
                    extra[username_field] = candidate

                user = User.objects.create_user(email=email, password=password, **extra)
                user.is_staff = False
                user.is_superuser = False
                user.is_active = True
                user.save()

                # OTOMATİK GİRİŞ
                login(request, user)

                # Modal tetiklemek için success mesajı (extra tag ile)
                messages.success(
                    request,
                    "Kayıt tamamlandı! Nomaya'ya hoş geldiniz. Girişiniz yapıldı.",
                    extra_tags="signup"
                )

                return redirect("home")

            except IntegrityError:
                errors["genel"] = "Teknik bir hata oluştu. Lütfen tekrar deneyin."

        for _, msg in errors.items():
            messages.error(request, msg)

        return render(request, "sign-up.html", {"prefill": {"email": email}})

    return render(request, "sign-up.html")

def home(request):
    countries = Country.objects.exclude(iso2__iexact="TR").only("id", "name").order_by("name")
    return render(request, "index.html", {"countries": countries})

def about(request):
    return render(request, "about.html")

def booking_confirmation(request):
    return render(request, "booking-confirmation.html")

def services(request):
    return render(request, "join-us.html")


def faqs(request):
    return render(request, "faq.html")

# Çok formatlı tek tarih parse
def _parse_date_any(s: str) -> Optional[date]:
    s = (s or "").strip()
    if not s:
        return None
    # Django'nun parse_date'i ISO (YYYY-MM-DD) için iyidir; önce onu dene
    d = parse_date(s)
    if d:
        return d
    # Alternatif formatlar
    fmts = [
        "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y",
        "%d %b %Y", "%d %B %Y",          # 13 Oct 2025 / 13 October 2025
        "%Y.%m.%d", "%Y/%m/%d",          # y.m.d varyasyonları
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

# Aralıktan GECE sayısı (maks 7)
def _days_from_dates(dates_str: str) -> Optional[int]:
    """
    "YYYY-MM-DD - YYYY-MM-DD" veya "13/10/2025 to 15/10/2025" vb.
    → GECE sayısı (end - start), max 7. Hatalıysa None.
    """
    if not dates_str:
        return None
    s = dates_str.strip()
    # 'to', en-dash (–), em-dash (—) veya normal tire (-) AYRAÇ, etrafında boşluk şart!
    parts = re.split(r"\s(?:to|–|—|-)\s", s, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return None
    start = _parse_date_any(parts[0])
    end   = _parse_date_any(parts[1])
    if not (start and end) or end <= start:
        return None
    nights = (end - start).days      # GECE sayısı
    return max(1, min(nights, 7))    # 1..7

from django.db.models import Count
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.utils import translation

def tour_grid(request):
    country = request.GET.get("country")
    pax = request.GET.get("pax")
    dates = request.GET.get("dates")
    tour_type = request.GET.get("tour_type")
    tour_types = request.GET.getlist("tour_types")

    requested_days = _days_from_dates(dates)

    qs = (
        Tour.objects.filter(is_published=True)
        # 🔧 DISTINCT otel sayısı: Tour -> TourDay -> Day -> DayHotel -> Hotel
        .annotate(hotels_count_distinct=Count("tour_days__day__dayhotel__hotel_id", distinct=True))
        .prefetch_related("photos", "places_covered__country", "tour_types")
        .order_by("-created_at")
        .distinct()
    )

    # --- country filtresi (id veya ad) + country_name ---
    country_name = None
    if country:
        if str(country).isdigit():
            qs = qs.filter(places_covered__country_id=country)
            obj = Country.objects.filter(id=country).only("name").first()
            if obj:
                country_name = obj.name
        else:
            qs = qs.filter(places_covered__country__name__icontains=country)
            country_name = country

    # --- tur tipi filtreleri ---
    if tour_type:
        qs = qs.filter(tour_types__id=tour_type)
    if tour_types:
        qs = qs.filter(tour_types__id__in=tour_types)

    # --- süreye göre öneri ---
    tours_list = list(qs)
    if requested_days is not None:
        tours_list = [t for t in tours_list if (t.total_days or 0) > 0 and t.total_days <= requested_days]
        tours_list.sort(key=lambda t: (t.total_days or 0), reverse=True)

    # --- pagination ---
    paginator = Paginator(tours_list, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    # --- querystring (page hariç) ---
    params = request.GET.copy()
    params.pop("page", None)
    qs_without_page = urlencode(params, doseq=True)

    countries = Country.objects.all().exclude(iso2__iexact="TR").only("id", "name").order_by("name")
    tourtype_opts = TourType.objects.all().only("id", "name").order_by("name")

    context = {
        "pax": pax,
        "country": country,
        "country_name": country_name,
        "dates": dates,
        "requested_days": requested_days,
        "tour_type": tour_type,
        "tour_types_selected": set(tour_types),

        "tours": page_obj.object_list,
        "paginator": paginator,
        "page_obj": page_obj,
        "qs": qs_without_page,

        "countries": countries,
        "tourtype_opts": tourtype_opts,
    }
    with translation.override("tr"):
        return render(request, "tour-grid.html", context)


# views.py
from django.utils.dateparse import parse_date
import re
from datetime import datetime

def _parse_dates_param(value: str):
    """
    Tarih aralığını güvenle parse eder.
    Örnekler:
      2025-10-21+-+2025-10-28
      2025-10-21 - 2025-10-28
      2025-10-21 to 2025-10-28
      (tek tarih de olabilir)
    """
    if not value:
        return None, None

    # '+' -> boşluk, birden çok boşluğu sadeleştir
    s = value.replace('+', ' ').replace('%2B', '+').strip()
    s = re.sub(r'\s+', ' ', s)

    # Ayırıcıyı YALNIZCA çevresinde boşluk varken kabul et (tarihin içindeki '-' zarar görmesin)
    # Öncelik: ' to ' sonra ' - ' sonra ' – ' veya ' — '
    if ' to ' in s:
        a, b = s.split(' to ', 1)
    elif ' - ' in s:
        a, b = s.split(' - ', 1)
    elif ' – ' in s:
        a, b = s.split(' – ', 1)
    elif ' — ' in s:
        a, b = s.split(' — ', 1)
    else:
        # Tek tarih dene
        d = parse_date(s) or _try_strptime(s)
        return d, None

    start = parse_date(a.strip()) or _try_strptime(a.strip())
    end   = parse_date(b.strip()) or _try_strptime(b.strip())
    return start, end

def _try_strptime(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

# Türkçe tarih için locale ayarı
try:
    locale.setlocale(locale.LC_TIME, "tr_TR.UTF-8")
except locale.Error:
    pass


def tour_detail(request, slug):
    """Tur detay sayfası — başlangıç günü + tarihleri gösterir."""

    # --- (1) Gizleme parametreleri ---
    hide_raw = (request.GET.get("hide") or "").lower()
    hide_set = {h.strip() for h in hide_raw.replace(";", ",").split(",") if h.strip()}
    hide_flights    = "flights"    in hide_set
    hide_transfers  = "transfers"  in hide_set
    hide_hotels     = "hotels"     in hide_set
    hide_activities = "activities" in hide_set

    # --- (2) Başlangıç günü parametresi ---
    try:
        start_day_number = int(request.GET.get("start_day", "1"))
    except (TypeError, ValueError):
        start_day_number = 1

    # --- (3) Tur objesi ---
    tour = get_object_or_404(
        Tour.objects.prefetch_related(
            Prefetch("photos", queryset=TourPhoto.objects.order_by("order", "id")),
        ),
        slug=slug, is_published=True,
    )

    # --- (4) Günler ---
    tour_days = (
        TourDay.objects
        .filter(tour=tour)
        .select_related("day", "day__city", "day__city__country")
        .prefetch_related(
            Prefetch("day__images", queryset=DayImage.objects.order_by("order", "id")),
            Prefetch("day__dayflight_set", queryset=DayFlight.objects.select_related(
                "flight", "flight__airline", "flight__origin", "flight__destination"
            ).order_by("order", "id")),
            Prefetch("day__daytransfer_set", queryset=DayTransfer.objects.select_related(
                "transfer", "transfer__airport", "transfer__hotel", "transfer__hotel__city"
            ).order_by("order", "id")),
            Prefetch("day__dayhotel_set", queryset=DayHotel.objects.select_related(
                "hotel", "hotel__city"
            ).order_by("order", "id")),
            Prefetch("day__dayactivity_set", queryset=DayActivity.objects.select_related(
                "activity"
            ).order_by("order", "id")),
        )
        .order_by("order", "id")
    )

    # --- (5) Günlerin fiyat toplamları ---
    day_ids = list(tour_days.values_list("day_id", flat=True))
    flights_total    = DayFlight.objects.filter(day_id__in=day_ids).aggregate(s=Sum("flight__price"))["s"] or Decimal("0.00")
    transfers_total  = DayTransfer.objects.filter(day_id__in=day_ids).aggregate(s=Sum("transfer__price"))["s"] or Decimal("0.00")
    hotels_total     = DayHotel.objects.filter(day_id__in=day_ids).aggregate(s=Sum("hotel__price_per_night"))["s"] or Decimal("0.00")
    activities_total = DayActivity.objects.filter(day_id__in=day_ids).aggregate(s=Sum("activity__price"))["s"] or Decimal("0.00")

    # --- (6) Kullanıcı girdileri ---
    pax = request.GET.get("pax")
    try:
        pax = int(pax) if pax else None
    except (TypeError, ValueError):
        pax = None

    dates_param = request.GET.get("dates") or ""
    dates_start, dates_end = _parse_dates_param(dates_param)  # dates_end istenirse dursun

    # --- (7) Günlük tarih listesi + DOĞRU bitiş tarihi ---
    day_dates = []
    computed_end_date = None
    if dates_start:
        total_days = len(tour_days)
        day_dates = [dates_start + timedelta(days=i) for i in range(total_days)]  # ← date objeleri
        if total_days > 0:
            computed_end_date = dates_start + timedelta(days=total_days - 1)
    else:
        day_dates = [None] * len(tour_days)


    # --- (8) Toplam hesaplaması ---
    gross_total = Decimal("0.00")
    if not hide_flights:    gross_total += flights_total
    if not hide_transfers:  gross_total += transfers_total
    if not hide_hotels:     gross_total += hotels_total
    if not hide_activities: gross_total += activities_total

    per_person = None
    if pax and pax > 0:
        try:
            per_person = (gross_total / Decimal(pax)).quantize(Decimal("0.01"))
        except Exception:
            per_person = None

    # --- (9) Template context ---
    ctx = {
        "tour": tour,
        "tour_days": tour_days,

        # gün numarası ve tarihler
        "start_day_number": start_day_number,
        "day_dates": day_dates,
        "dates": dates_param,
        "dates_start": dates_start,
        "dates_end": dates_end,                 # (opsiyonel) istersen kullanmaya devam et
        "computed_end_date": computed_end_date, # ✅ son günün gerçek tarihi

        # filtre/gizleme ve fiyatlar
        "pax": pax,
        "hide_flights": hide_flights,
        "hide_transfers": hide_transfers,
        "hide_hotels": hide_hotels,
        "flights_total": flights_total,
        "transfers_total": transfers_total,
        "hotels_total": hotels_total,
        "activities_total": activities_total,
        "per_person": per_person,
        "total": gross_total,
    }
    with translation.override("tr"):
        return render(request, "tour-detail.html", ctx)


def book_tour_order(request, slug):
    tour = get_object_or_404(Tour, slug=slug)
    hide_flights = request.GET.get("hide_flights") == "1"
    hide_transfers = request.GET.get("hide_transfers") == "1"
    hide_hotels = request.GET.get("hide_hotels") == "1"
    pax = int(request.GET.get("pax", "0") or "0")
    same_room = request.GET.get("same_room", "1") == "1"

    # Pax veya oda bilgisi eksikse popup’a geri dön
    if pax == 0:
        return redirect(reverse("tour_detail", args=[slug]))

    price = request.GET.get("price")
    # orders/views.py (örnek)
    order = Order.objects.create(
        tour=tour,
        pax=pax,
        email=email,
        hide_flights=hide_flights,
        hide_transfers=hide_transfers,
        hide_hotels=hide_hotels,
        same_room=same_room,
        # fiyat alanlarını modelinizdekine göre adlandırın:
        price=price,     # eğer modelde 'price' varsa
        total=total,     # eğer modelde 'total' varsa
        # currency alanınız varsa ekleyin:
        # currency=currency,
    )
    if price:
        order.total_price = Decimal(price)
    order.compute_total()
    order.save()

    return redirect(reverse("tour_booking", args=[order.id]))

def order_success(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, "order_success.html", {"order": order})


from decimal import Decimal, InvalidOperation  # <-- EKLENDİ

def _to_bool(v: str) -> bool:
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "on", "yes")


@require_http_methods(["POST"])
def tour_booking(request):
    # Formdan gelenler
    tour_id = request.POST.get("tour_id")
    tour = get_object_or_404(Tour, pk=tour_id)

    # pax güvenli aralıkta olsun (1–2)
    try:
        pax = int(request.POST.get("pax", 1))
    except ValueError:
        pax = 1
    pax = 1 if pax < 1 else (2 if pax > 2 else pax)

    email = (request.POST.get("email") or "").strip()

    hide_flights   = _to_bool(request.POST.get("hide_flights"))
    hide_transfers = _to_bool(request.POST.get("hide_transfers"))
    hide_hotels    = _to_bool(request.POST.get("hide_hotels"))

    # same_room boş gelebilir (otel dahil değilse veya pax=1 ise). Varsayılan True.
    same_room_param = request.POST.get("same_room", "")
    same_room = True if same_room_param in ("", None) else _to_bool(same_room_param)

    # Popup'tan gelen kişi başı ve toplam fiyatları AL (seçime göre)
    def _dec(v, default="0"):
        try:
            return Decimal(str(v))
        except (InvalidOperation, TypeError):
            return Decimal(default)

    per_person_sel = _dec(request.POST.get("price"), default=str(tour.price or "0"))
    total_sel      = _dec(request.POST.get("total"))

    # total gönderilmemişse / hatalıysa: kişi başı × pax
    if total_sel <= 0:
        total_sel = (per_person_sel * Decimal(pax))

    # Yuvarlama: sitenin kalanında tam sayı gösteriyorsan tam sayıya indir
    total_sel = total_sel.quantize(Decimal("1"))

    start_date = parse_date(request.POST.get("start_date") or "")
    end_date   = parse_date(request.POST.get("end_date") or "")

    # Order’ı, MODALDAKİ "seçime göre" toplamla oluştur
    ensure_session(request)
    order = Order.objects.create(
            tour=tour,
            pax=pax,
            email=email,
            same_room=same_room,
            hide_flights=hide_flights,
            hide_transfers=hide_transfers,
            hide_hotels=hide_hotels,
            total_price=total_sel,
            session_key=request.session.session_key,

            # ✅ kaydet
            start_date=start_date,
            end_date=end_date,
        )

    # Detay sayfasına gönder
    return redirect("tour_booking_detail_public", public_id=order.public_id)

def tour_booking_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related("tour"), pk=order_id)
    tour = order.tour

    try:
        start_day_number = int(request.GET.get("start_day", "1"))
    except (TypeError, ValueError):
        start_day_number = 1

    tour_days = (
        TourDay.objects.filter(tour=tour)
        .select_related("day", "day__city", "day__city__country")
        .prefetch_related(
            Prefetch("day__images", queryset=DayImage.objects.order_by("order", "id")),
            Prefetch("day__dayflight_set", queryset=DayFlight.objects.select_related(
                "flight", "flight__airline", "flight__origin", "flight__destination"
            ).order_by("order", "id")),
            Prefetch("day__daytransfer_set", queryset=DayTransfer.objects.select_related(
                "transfer", "transfer__airport", "transfer__hotel", "transfer__hotel__city"
            ).order_by("order", "id")),
            Prefetch("day__dayhotel_set", queryset=DayHotel.objects.select_related(
                "hotel", "hotel__city"
            ).order_by("order", "id")),
            Prefetch("day__dayactivity_set", queryset=DayActivity.objects.select_related(
                "activity"
            ).order_by("order", "id")),
        )
        .order_by("order", "id")
    )

    day_ids = list(tour_days.values_list("day_id", flat=True))
    has_flights = DayFlight.objects.filter(day_id__in=day_ids).exists()
    has_transfers = DayTransfer.objects.filter(day_id__in=day_ids).exists()
    has_hotels = DayHotel.objects.filter(day_id__in=day_ids).exists()
    has_activities = DayActivity.objects.filter(day_id__in=day_ids).exists()

    ctx = {
        "order": order,
        "tour": tour,
        "tour_days": tour_days,
        "start_day_number": start_day_number,
        "pax": order.pax,
        "per_person": order.total_price / order.pax if order.pax else order.total_price,
        "total": order.total_price,
        "has_flights": has_flights,
        "has_transfers": has_transfers,
        "has_hotels": has_hotels,
        "has_activities": has_activities,
    }
    with translation.override("tr"):
        return render(request, "tour-booking.html", ctx)

@require_http_methods(["POST"])
def save_travelers(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    count = int(request.POST.get("traveler_count", order.pax) or order.pax)

    start_day = request.GET.get("start_day") or request.POST.get("start_day")

    ddmmyyyy = re.compile(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/[0-9]{4}$")

    created = []
    for i in range(1, count + 1):
        data = request.POST.get(f"traveler[{i}][first_name]")
        if data is None:
            continue

        title = (request.POST.get(f"traveler[{i}][title]") or "").strip()
        first_name = (request.POST.get(f"traveler[{i}][first_name]") or "").strip()
        last_name  = (request.POST.get(f"traveler[{i}][last_name]") or "").strip()
        passport   = (request.POST.get(f"traveler[{i}][passport_no]") or "").strip()
        phone      = (request.POST.get(f"traveler[{i}][phone]") or "").strip()
        dob_str    = (request.POST.get(f"traveler[{i}][dob]") or "").strip()

        if not ddmmyyyy.match(dob_str):
            messages.error(request, f"Traveler {i}: DoB must be DD/MM/YYYY")
            q = {"step": "2"}
            if start_day: q["start_day"] = start_day
            return redirect(reverse("tour_booking_detail", args=[order.id]) + "?" + urlencode(q))

        dob = datetime.strptime(dob_str, "%d/%m/%Y").date()

        Traveler.objects.create(
            order=order,
            title=title,
            first_name=first_name,
            last_name=last_name,
            passport_no=passport,
            phone=phone,
            dob=dob,
        )
        created.append(i)

    messages.success(request, f"{len(created)} traveler saved.")
    q = {"step": "3"}
    if start_day: q["start_day"] = start_day
    return redirect(reverse("tour_booking_detail", args=[order.id]) + "?" + urlencode(q))

from django.views.decorators.http import require_POST
from django.http import JsonResponse
from core.models import Order

@require_POST
def accept_link_payment(request, order_id):
    order = Order.objects.filter(pk=order_id).first()
    if not order:
        return JsonResponse({"error": "Order not found"}, status=404)

    # Kullanıcı link ile ödemeyi onayladı
    order.payment_method = "payment_link"
    order.link_payment_accepted = True
    order.save(update_fields=["payment_method", "link_payment_accepted"])
    return JsonResponse({"success": True})
