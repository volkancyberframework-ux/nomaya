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
from .models import LiveLocation, ActivityProgressLocationLog
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import re
from datetime import datetime
from django.core.paginator import Paginator
from django.shortcuts import render
import stripe
from django.conf import settings
from django.urls import reverse
# core/views.py
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.dateparse import parse_date
from .models import Order, TourDay, DayActivity, ActivityProgress
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
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from .models import (
    Tour, TourPhoto, TourDay, DayImage, DayFlight,
    DayTransfer, DayHotel, DayActivity
)
from .utils import _parse_dates_param  # eğer ayrı utils'te tanımlıysa
from django.utils import translation
from .models import ActivityProgressLocationLog
import os
import subprocess
from django.core.files.base import ContentFile
from django.conf import settings

User = get_user_model()

def send_telegram_message(message: str) -> bool:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "") or ""

    if not token or not chat_id:
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        urllib.request.urlopen(req, timeout=3)
        return True

    except Exception:
        return False


def tg(v):
    return html.escape(str(v or "-"))


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "-")


def order_telegram_text(order, title="🆕 Yeni Order Oluştu"):
    return (
        f"<b>{title}</b>\n\n"
        f"<b>Order ID:</b> {tg(order.id)}\n"
        f"<b>Tur:</b> {tg(order.tour.title if order.tour else '-')}\n"
        f"<b>E-posta:</b> {tg(order.email)}\n"
        f"<b>Kişi:</b> {tg(order.pax)}\n"
        f"<b>Tutar:</b> {tg(order.total_price)}\n"
        f"<b>Tarih:</b> {tg(order.start_date)} → {tg(order.end_date)}\n"
        f"<b>Payment:</b> {tg(order.payment_method)}\n"
        f"<b>Paid:</b> {tg(order.is_paid)}\n"
        f"<b>Flights hidden:</b> {tg(order.hide_flights)}\n"
        f"<b>Transfers hidden:</b> {tg(order.hide_transfers)}\n"
        f"<b>Hotels hidden:</b> {tg(order.hide_hotels)}\n"
        f"<b>Tracking Code:</b> {tg(order.tracking_code)}"
    )

from django.utils import translation
from django.db.models import Prefetch
import json
import urllib.request
import html
from django.conf import settings
from django.db import IntegrityError

def tour_booking_detail_public(request, public_id):
    order = get_order_for_request_by_public(request, public_id)
    tour = order.tour

    if not tour.allow_flights:
        order.hide_flights = True

    if not tour.allow_transfers:
        order.hide_transfers = True

    if not tour.allow_hotels:
        order.hide_hotels = True

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

        traveler = Traveler.objects.create(
            order=order,
            title=title,
            first_name=first_name,
            last_name=last_name,
            passport_no=passport,
            phone=phone,
            dob=dob,
        )

        if i == 1:
            from .services import create_order_intro_audios_for_name
            create_order_intro_audios_for_name(order, first_name)
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
        profile = getattr(request.user, "nomaya_profile", None)

        if profile and profile.force_password_change:
            return render(request, "sign-in.html", {
                "show_password_modal": True,
            })

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

            if not remember:
                request.session.set_expiry(0)

            profile = getattr(auth_user, "nomaya_profile", None)

            if profile and profile.force_password_change:
                return render(request, "sign-in.html", {
                    "next": next_url,
                    "show_password_modal": True,
                })

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
    countries = Country.objects.only("id", "name").order_by("name")
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

    countries = Country.objects.all().only("id", "name").order_by("name")
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

    if not tour.allow_flights:
        hide_flights = True

    if not tour.allow_transfers:
        hide_transfers = True

    if not tour.allow_hotels:
        hide_hotels = True

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
        "allow_flights": tour.allow_flights,
        "allow_hotels": tour.allow_hotels,
        "allow_transfers": tour.allow_transfers,
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


    if not tour.allow_flights:
        hide_flights = True

    if not tour.allow_transfers:
        hide_transfers = True

    if not tour.allow_hotels:
        hide_hotels = True

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
    send_telegram_message(order_telegram_text(order))

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
    send_telegram_message(order_telegram_text(order, title="💳 Payment Link Seçildi"))
    return JsonResponse({"success": True})


import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import LiveLocation

from django.shortcuts import render

def nomaya_asistan(request):
    if not request.session.session_key:
        request.session.create()

    return render(request, "core/nomaya_asistan.html")

def geo(request):
    if not request.session.session_key:
        request.session.create()
    return render(request, "core/geo.html")

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import LiveLocation

from django.shortcuts import render
from django.http import JsonResponse
from .models import LiveLocation

def superuser_required(user):
    return user.is_authenticated and user.is_active and user.is_staff and user.is_superuser


@user_passes_test(superuser_required, login_url="/admin/login/")
def live_map(request):
    return render(request, "core/live_map.html")

def live_locations_api(request):
    locations = LiveLocation.objects.all().order_by("-updated_at")

    data = []
    for loc in locations:
        data.append({
            "session_id": loc.session_id or "Unknown",
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "accuracy": loc.accuracy,
            "updated_at": loc.updated_at.strftime("%d.%m.%Y %H:%M:%S"),
        })

    return JsonResponse(data, safe=False)

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import Order


@csrf_exempt
def verify_tracking_code(request):
    if request.method != "POST":
        return JsonResponse({"valid": False, "message": "method_not_allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"valid": False, "message": "invalid_json"}, status=400)

    code = str(data.get("code", "")).strip().upper()

    if not code:
        return JsonResponse({"valid": False, "message": "empty_code"}, status=400)

    try:
        order = Order.objects.select_related("tour").get(
            tracking_code=code,
            is_paid=True,
            tracking_enabled=True,
        )
    except Order.DoesNotExist:
        return JsonResponse({"valid": False, "message": "invalid_code"}, status=404)

    if timezone.now() > order.tracking_code_expires_at:
        return JsonResponse({"valid": False, "message": "expired"}, status=403)

    first_start = not bool(order.tracking_started_at)

    if first_start:
        order.tracking_started_at = timezone.now()

    order.tracking_last_seen = timezone.now()
    order.save(update_fields=["tracking_started_at", "tracking_last_seen"])

    if first_start:
        send_telegram_message(
            f"<b>📍 Tracking İlk Kez Başladı</b>\n\n"
            f"<b>Order ID:</b> {tg(order.id)}\n"
            f"<b>Tur:</b> {tg(order.tour.title if order.tour else '-')}\n"
            f"<b>E-posta:</b> {tg(order.email)}\n"
            f"<b>Tracking Code:</b> {tg(order.tracking_code)}\n"
            f"<b>IP:</b> {tg(get_client_ip(request))}"
        )

    return JsonResponse({
        "valid": True,
        "message": "ok",
        "order_id": order.id,
        "tour": order.tour.title,
        "expires_at": order.tracking_code_expires_at.isoformat(),
    })

@csrf_exempt
def update_location(request):
    if request.method != "POST":
        return JsonResponse({"success": False}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "message": "invalid_json"}, status=400)

    code = str(data.get("session_id", "")).strip().upper()

    try:
        order = Order.objects.get(
            tracking_code=code,
            is_paid=True,
            tracking_enabled=True,
        )
    except Order.DoesNotExist:
        return JsonResponse({"success": False, "message": "invalid_code"}, status=404)

    if timezone.now() > order.tracking_code_expires_at:
        return JsonResponse({"success": False, "message": "expired"}, status=403)

    today = timezone.localdate()

    if order.start_date and today < order.start_date:
        return JsonResponse({
            "success": False,
            "message": "travel_not_started",
            "detail": "Seyahat günü gelmedi.",
            "start_date": str(order.start_date),
            "today": str(today),
        }, status=403)

    if order.end_date and today > order.end_date:
        return JsonResponse({
            "success": False,
            "message": "travel_finished",
            "detail": "Seyahat günü sona erdi.",
            "end_date": str(order.end_date),
            "today": str(today),
        }, status=403)

    order.tracking_last_seen = timezone.now()
    order.save(update_fields=["tracking_last_seen"])

    first_location = not LiveLocation.objects.filter(session_id=code).exists()

    LiveLocation.objects.update_or_create(
        session_id=code,
        defaults={
            "name": order.email or code,
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "accuracy": data.get("accuracy"),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "ip_address": request.META.get("HTTP_CF_CONNECTING_IP")
            or request.META.get("HTTP_TRUE_CLIENT_IP")
            or request.META.get("REMOTE_ADDR"),
            "updated_at": timezone.now(),
        }
    )

    if first_location:
        from .services import enqueue_tour_started_message_if_needed
        enqueue_tour_started_message_if_needed(order)

    return JsonResponse({
        "success": True,
        "first_location": first_location,
        "today": str(today),
        "start_date": str(order.start_date) if order.start_date else None,
        "end_date": str(order.end_date) if order.end_date else None,
    })
from django.http import JsonResponse
from django.utils import timezone
from .models import Order, TourDay


def order_itinerary(request, code):
    try:
        order = Order.objects.select_related("tour").get(
            tracking_code=code.upper(),
            tracking_enabled=True,
            tracking_code_expires_at__gte=timezone.now()
        )
    except Order.DoesNotExist:
        return JsonResponse({
            "valid": False,
            "message": "Geçersiz veya süresi dolmuş kod"
        }, status=404)

    tour = order.tour

    tour_days = (
        TourDay.objects
        .filter(tour=tour)
        .select_related("day", "day__city")
        .order_by("order", "id")
    )

    days_data = []

    for td in tour_days:
        day = td.day

        activities = []
        for da in day.dayactivity_set.select_related("activity").order_by("order"):
            activity = da.activity
            activities.append({
                "title": activity.title,
                "location": activity.location_text,
                "points": activity.points or [],
                "duration_hours": str(activity.duration_hours) if activity.duration_hours else None,
            })

        hotels = []
        for dh in day.dayhotel_set.select_related("hotel", "hotel__city").order_by("order"):
            hotel = dh.hotel
            hotels.append({
                "name": hotel.name,
                "city": hotel.city.name,
                "star": hotel.star,
                "type": hotel.hotel_type,
            })

        flights = []
        for df in day.dayflight_set.select_related(
            "flight",
            "flight__origin",
            "flight__destination",
            "flight__airline"
        ).order_by("order"):
            flight = df.flight
            flights.append({
                "airline": flight.airline.name,
                "flight_number": flight.flight_number,
                "origin": flight.origin.iata,
                "destination": flight.destination.iata,
                "departure_time": str(flight.departure_time) if flight.departure_time else None,
                "arrival_time": str(flight.arrival_time) if flight.arrival_time else None,
            })

        transfers = []
        for dt in day.daytransfer_set.select_related(
            "transfer",
            "transfer__airport",
            "transfer__hotel"
        ).order_by("order"):
            transfer = dt.transfer
            transfers.append({
                "direction": transfer.get_direction_display(),
                "vehicle_type": transfer.vehicle_type,
                "airport": transfer.airport.iata,
                "hotel": transfer.hotel.name,
            })

        days_data.append({
            "order": td.order,
            "title": td.title,
            "city": day.city.name,
            "day_number": day.day_number,
            "description": day.description,
            "bullets": day.bullets or [],
            "activities": activities,
            "hotels": hotels if not order.hide_hotels else [],
            "flights": flights if not order.hide_flights else [],
            "transfers": transfers if not order.hide_transfers else [],
        })

    return JsonResponse({
        "valid": True,
        "tour": {
            "title": tour.title,
            "duration": tour.duration_label,
            "start_point": tour.start_point,
            "end_point": tour.end_point,
            "overview": tour.overview,
        },
        "order": {
            "tracking_code": order.tracking_code,
            "start_date": str(order.start_date) if order.start_date else None,
            "end_date": str(order.end_date) if order.end_date else None,
            "pax": order.pax,
        },
        "days": days_data,
    })

@csrf_exempt
def today_plan(request, code):
    try:
        order = Order.objects.select_related("tour").get(
            tracking_code=code.upper(),
            is_paid=True,
            tracking_enabled=True,
            tracking_code_expires_at__gte=timezone.now()
        )
    except Order.DoesNotExist:
        return JsonResponse({
            "valid": False,
            "message": "Geçersiz veya süresi dolmuş kod"
        }, status=404)

    tour = order.tour

    tour_days = (
        TourDay.objects
        .filter(tour=tour)
        .select_related("day", "day__city")
        .order_by("order", "id")
    )

    if not tour_days.exists():
        return JsonResponse({
            "valid": False,
            "message": "Bu tur için gün planı bulunamadı"
        }, status=404)

    # Bugünün hangi tur günü olduğunu hesapla
    selected_tour_day = None

    if order.start_date:
        today = timezone.localdate()
        day_index = (today - order.start_date).days + 1

        if day_index < 1:
            day_index = 1

        selected_tour_day = tour_days.filter(order=day_index).first()

    if selected_tour_day is None:
        selected_tour_day = tour_days.first()

    day = selected_tour_day.day

    day_activities = (
        DayActivity.objects
        .filter(day=day)
        .select_related("activity")
        .order_by("order", "id")
    )

    activities = []

    for da in day_activities:
        progress, _ = ActivityProgress.objects.get_or_create(
            order=order,
            day_activity=da
        )

        activity = da.activity

        activities.append({
            "day_activity_id": da.id,
            "activity_id": activity.id,
            "title": activity.title,
            "location": activity.location_text,
            "points": activity.points or [],
            "duration_hours": str(activity.duration_hours) if activity.duration_hours else None,
            "status": progress.status,
        })

    return JsonResponse({
        "valid": True,
        "tour": {
            "title": tour.title,
        },
        "order": {
            "tracking_code": order.tracking_code,
            "start_date": str(order.start_date) if order.start_date else None,
            "end_date": str(order.end_date) if order.end_date else None,
        },
        "day": {
            "tour_day_order": selected_tour_day.order,
            "title": selected_tour_day.title,
            "city": day.city.name,
            "description": day.description,
            "bullets": day.bullets or [],
        },
        "activities": activities,
    })


def telegram_activity_hook(order, day_activity, status):
    if status not in ["completed", "skipped"]:
        return False

    icon = "✅" if status == "completed" else "⏭️"

    return send_telegram_message(
        f"<b>{icon} Activity {tg(status).upper()}</b>\n\n"
        f"<b>Order ID:</b> {tg(order.id)}\n"
        f"<b>Tur:</b> {tg(order.tour.title if order.tour else '-')}\n"
        f"<b>E-posta:</b> {tg(order.email)}\n"
        f"<b>Tracking Code:</b> {tg(order.tracking_code)}\n"
        f"<b>Aktivite:</b> {tg(day_activity.activity.title if day_activity.activity else '-')}\n"
        f"<b>Gün:</b> {tg(day_activity.day.title if day_activity.day else '-')}\n"
        f"<b>Status:</b> {tg(status)}\n"
        f"<b>Miles:</b> {tg(day_activity.activity.miles_reward if day_activity.activity else 0)}"
    )

@csrf_exempt
def update_activity_progress(request):
    if request.method != "POST":
        return JsonResponse({
            "valid": False,
            "message": "method_not_allowed"
        }, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({
            "valid": False,
            "message": "invalid_json"
        }, status=400)

    code = str(data.get("code", "")).strip().upper()
    day_activity_id = data.get("day_activity_id")
    status = str(data.get("status", "")).strip()

    if status not in ["pending", "completed", "skipped"]:
        return JsonResponse({
            "valid": False,
            "message": "invalid_status"
        }, status=400)

    try:
        order = Order.objects.get(
            tracking_code=code,
            is_paid=True,
            tracking_enabled=True,
            tracking_code_expires_at__gte=timezone.now()
        )
    except Order.DoesNotExist:
        return JsonResponse({
            "valid": False,
            "message": "Geçersiz veya süresi dolmuş kod"
        }, status=404)

    try:
        day_activity = DayActivity.objects.select_related(
            "activity", "day"
        ).get(id=day_activity_id)
    except DayActivity.DoesNotExist:
        return JsonResponse({
            "valid": False,
            "message": "Aktivite bulunamadı"
        }, status=404)

    belongs_to_tour = TourDay.objects.filter(
        tour=order.tour,
        day=day_activity.day
    ).exists()

    if not belongs_to_tour:
        return JsonResponse({
            "valid": False,
            "message": "Bu aktivite bu tura ait değil"
        }, status=403)

    progress, _ = ActivityProgress.objects.get_or_create(
        order=order,
        day_activity=day_activity
    )

    old_status = progress.status

    progress.status = status
    progress.save(update_fields=["status", "updated_at"])

    last_location = LiveLocation.objects.filter(
        session_id=order.tracking_code
    ).order_by("-updated_at").first()

    ActivityProgressLocationLog.objects.create(
        order=order,
        activity_progress=progress,
        day_activity=day_activity,
        tracking_code=order.tracking_code,
        action=status,
        latitude=last_location.latitude if last_location else None,
        longitude=last_location.longitude if last_location else None,
        accuracy=last_location.accuracy if last_location else None,
        session_id=order.tracking_code,
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        ip_address=request.META.get("HTTP_CF_CONNECTING_IP")
        or request.META.get("HTTP_TRUE_CLIENT_IP")
        or request.META.get("REMOTE_ADDR"),
    )

    ActivityProgressLocationLog.prune_if_needed()

    if status in ["completed", "skipped"] and old_status != status:
        sent = telegram_activity_hook(order, day_activity, status)
        if sent:
            progress.telegram_sent = True
            progress.save(update_fields=["telegram_sent", "updated_at"])

        if status == "skipped":
            from .services import enqueue_next_activity_after_skip
            enqueue_next_activity_after_skip(order, day_activity)

        if status == "completed":
            from .services import enqueue_activity_message, create_whatsapp_message

            next_activity = DayActivity.objects.filter(
                day=day_activity.day,
                order__gt=day_activity.order,
            ).select_related("activity", "day").order_by("order", "id").first()

            if next_activity:
                enqueue_activity_message(
                    order=order,
                    day_activity=next_activity,
                    key="next_activity"
                )
            else:
                create_whatsapp_message(
                    order=order,
                    key="tour_no_next_activity",
                    context={
                        "name": order.travelers.first().first_name if order.travelers.exists() else "Nomaya gezgini",
                        "tour_title": order.tour.title if order.tour else "",
                    },
                    dedupe_suffix=f"completed-no-next-after-{day_activity.id}",
                )

    earned_miles = day_activity.activity.miles_reward if status == "completed" else 0

    return JsonResponse({
        "valid": True,
        "day_activity_id": day_activity.id,
        "activity_title": day_activity.activity.title,
        "status": progress.status,
        "earned_miles": earned_miles,
        "order_total_miles": order.earned_miles,
    })
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Order


@require_POST
def request_miles_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    order.payment_method = "miles_payment"
    order.miles_payment_requested = True
    order.miles_payment_requested_at = timezone.now()
    order.save(update_fields=[
        "payment_method",
        "miles_payment_requested",
        "miles_payment_requested_at",
    ])

    send_telegram_message(order_telegram_text(order, title="🪙 Miles ile Ödeme Talebi"))

    return JsonResponse({"success": True})

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Order


@require_POST
def request_bank_transfer(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    order.payment_method = "bank_transfer"
    order.save(update_fields=["payment_method"])

    try:
        send_telegram_message(
            f"🏦 Banka transferi seçildi\n\n"
            f"Order: #{order.id}\n"
            f"Tur: {order.tour.title if order.tour else '-'}\n"
            f"E-posta: {order.email or '-'}\n"
            f"Kişi: {order.pax}\n"
            f"Tutar: {order.total_price} {getattr(order.tour, 'price_currency', '')}\n"
            f"Tracking Code: {order.tracking_code or '-'}"
        )
    except Exception:
        pass

    return JsonResponse({"success": True})

from django.http import FileResponse, HttpResponseForbidden, Http404

def secure_audio_stream(request, tracking_code, day_activity_id, audio_type):
    order = get_object_or_404(
        Order,
        tracking_code=tracking_code.upper(),
        is_paid=True,
        tracking_enabled=True,
    )

    if timezone.now() > order.tracking_code_expires_at:
        return HttpResponseForbidden("Bu ses kaydının süresi dolmuş.")

    day_activity = get_object_or_404(
        DayActivity.objects.select_related("activity", "day"),
        id=day_activity_id,
    )

    belongs_to_tour = TourDay.objects.filter(
        tour=order.tour,
        day=day_activity.day
    ).exists()

    if not belongs_to_tour:
        return HttpResponseForbidden("Bu aktivite bu tura ait değil.")

    activity = day_activity.activity

    if audio_type == "on-the-way":
        audio_file = activity.audio_on_the_way
    elif audio_type == "at-location":
        audio_file = activity.audio_at_location
    else:
        raise Http404("Ses tipi bulunamadı.")

    if not audio_file:
        raise Http404("Ses kaydı bulunamadı.")

    try:
        final_audio = build_combined_audio(
            order=order,
            day_activity=day_activity,
            audio_type=audio_type,
            main_audio_file=audio_file,
        )
    except Exception:
        final_audio = audio_file.open("rb")

    return FileResponse(
        final_audio,
        content_type="audio/mpeg"
    )

from decimal import Decimal, ROUND_HALF_UP
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.dateparse import parse_date
import re

from .models import CustomizedTravelRequest, CustomizedTravelSettings


def _custom_days_from_dates(dates_str):
    """
    2026-07-01 - 2026-07-03 => 3 gün
    """
    if not dates_str:
        return None, None, 1

    parts = re.split(r"\s(?:to|–|—|-)\s", dates_str.strip(), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return None, None, 1

    start = parse_date(parts[0].strip())
    end = parse_date(parts[1].strip())

    if not start or not end or end < start:
        return None, None, 1

    days = (end - start).days + 1
    return start, end, max(days, 1)


@require_http_methods(["GET", "POST"])
def order_customized(request):
    price_per_day = Decimal("9.99")

    if request.method == "POST":
        location = (request.POST.get("location") or "").strip()
        dates = (request.POST.get("dates") or "").strip()
        travel_style = (request.POST.get("travel_style") or "").strip()
        notes = (request.POST.get("notes") or "").strip()

        if request.user.is_authenticated:
            email = (request.user.email or "").strip()
            phone = (request.POST.get("phone") or "").strip()
        else:
            email = (request.POST.get("email") or "").strip()
            phone = (request.POST.get("phone") or "").strip()

            if not email or not phone:
                messages.error(request, "Ödeme öncesi e-posta ve telefon zorunludur.")
                return render(request, "order-customized.html", {
                    "price_per_day": price_per_day,
                    "prefill": request.POST,
                })

        start, end, days = _custom_days_from_dates(dates)
        total_price = (price_per_day * Decimal(days)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        settings_obj = CustomizedTravelSettings.objects.filter(
            is_active=True
        ).order_by("-id").first()

        stripe_link = settings_obj.stripe_payment_link if settings_obj else ""

        obj = CustomizedTravelRequest.objects.create(
            email=email,
            phone=phone,
            location=location,
            dates=dates,
            travel_style=travel_style,
            notes=notes,
            days=days,
            price_per_day=price_per_day,
            total_price=total_price,
            stripe_payment_link=stripe_link,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        send_telegram_message(
            f"<b>🧭 Yeni Kişiye Özel Nomaya Talebi</b>\n\n"
            f"<b>ID:</b> {tg(obj.id)}\n"
            f"<b>E-posta:</b> {tg(obj.email)}\n"
            f"<b>Telefon:</b> {tg(obj.phone)}\n"
            f"<b>Konum:</b> {tg(obj.location)}\n"
            f"<b>Tarih:</b> {tg(obj.dates)}\n"
            f"<b>Gün:</b> {tg(obj.days)}\n"
            f"<b>Tarz:</b> {tg(obj.travel_style)}\n"
            f"<b>Tutar:</b> ${tg(obj.total_price)}\n"
            f"<b>Not:</b> {tg(obj.notes)}"
        )

        return redirect(
                "order_customized_detail",
                public_id=obj.public_id
            )

    return render(request, "order-customized.html", {
        "price_per_day": price_per_day,
    })

def order_customized_detail(request, public_id):
    obj = get_object_or_404(
        CustomizedTravelRequest,
        public_id=public_id
    )

    return render(
        request,
        "order-customized-detail.html",
        {"obj": obj}
    )
@require_http_methods(["POST"])
def order_customized_pay(request, public_id):
    obj = get_object_or_404(
        CustomizedTravelRequest,
        public_id=public_id,
    )

    obj.payment_clicked = True
    obj.save(update_fields=["payment_clicked"])

    stripe.api_key = settings.STRIPE_SECRET_KEY

    amount_cents = int(obj.total_price * 100)

    success_url = (
        request.build_absolute_uri(
            reverse("order_customized_detail", kwargs={"public_id": obj.public_id})
        )
        + "?payment=success&session_id={CHECKOUT_SESSION_ID}"
    )

    cancel_url = (
        request.build_absolute_uri(
            reverse("order_customized_detail", kwargs={"public_id": obj.public_id})
        )
        + "?payment=cancel"
    )

    checkout_session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=obj.email,
        client_reference_id=str(obj.public_id),
        metadata={
            "customized_request_id": str(obj.id),
            "public_id": str(obj.public_id),
            "location": obj.location,
            "dates": obj.dates,
            "travel_style": obj.travel_style,
        },
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": "Kişiye Özel Nomaya Deneyimi",
                        "description": f"{obj.location} • {obj.dates} • {obj.travel_style}",
                    },
                },
                "quantity": 1,
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
    )

    send_telegram_message(
        f"<b>💳 Stripe Checkout Oluşturuldu</b>\n\n"
        f"<b>ID:</b> {tg(obj.id)}\n"
        f"<b>Konum:</b> {tg(obj.location)}\n"
        f"<b>Tutar:</b> ${tg(obj.total_price)}\n"
        f"<b>Checkout:</b> {tg(checkout_session.id)}"
    )

    return redirect(checkout_session.url)

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

def stripe_checkout_order(request, public_id):
    order = get_object_or_404(
        Order,
        public_id=public_id
    )

    amount_cents = int(order.total_price * 100)

    session = stripe.checkout.Session.create(
        mode="payment",

        customer_email=order.email,

        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": order.tour.title,
                    },
                },
                "quantity": 1,
            }
        ],

        success_url=request.build_absolute_uri(
            reverse(
                "order_success_public",
                kwargs={"public_id": order.public_id}
            )
        ),

        cancel_url=request.build_absolute_uri(
            reverse(
                "tour_booking_detail_public",
                kwargs={"public_id": order.public_id}
            )
        ),
    )

    return redirect(session.url)

import random

def build_combined_audio(order, day_activity, audio_type, main_audio_file):
    """
    Order intro + activity audio birleşik MP3 üretir.
    Cache mantığı: aynı dosya varsa yeniden üretmez.
    """

    intro_obj = order.intro_audios.order_by("?").first()

    if intro_obj and intro_obj.audio:
        intro_audio = intro_obj.audio
    elif order.custom_intro_audio:
        intro_audio = order.custom_intro_audio
    else:
        return main_audio_file

    combined_dir = os.path.join(settings.MEDIA_ROOT, "orders", "combined_audio")
    os.makedirs(combined_dir, exist_ok=True)

    intro_id = intro_obj.id if intro_obj else "legacy"
    output_name = f"order_{order.id}_intro_{intro_id}_activity_{day_activity.id}_{audio_type}.mp3"
    output_path = os.path.join(combined_dir, output_name)

    if os.path.exists(output_path):
        return open(output_path, "rb")

    intro_path = intro_audio.path
    main_path = main_audio_file.path

    list_path = os.path.join(combined_dir, f"concat_{order.id}_{day_activity.id}_{audio_type}.txt")

    with open(list_path, "w") as f:
        f.write(f"file '{intro_path}'\n")
        f.write(f"file '{main_path}'\n")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            output_path,
        ],
        check=True,
    )

    return open(output_path, "rb")
from django.contrib.auth import update_session_auth_hash

@login_required
@require_http_methods(["POST"])
def update_forced_password(request):
    profile = request.user.nomaya_profile

    if not profile.force_password_change:
        return redirect("home")

    password1 = request.POST.get("password1", "")
    password2 = request.POST.get("password2", "")

    if password1 != password2:
        messages.error(request, "Parolalar eşleşmiyor.")
        return render(request, "sign-in.html", {
            "show_password_modal": True,
        })

    if len(password1) < 8:
        messages.error(request, "Parola en az 8 karakter olmalıdır.")
        return render(request, "sign-in.html", {
            "show_password_modal": True,
        })

    request.user.set_password(password1)
    request.user.save()
    update_session_auth_hash(request, request.user)

    profile.force_password_change = False
    profile.password_changed_at = timezone.now()
    profile.save(update_fields=["force_password_change", "password_changed_at"])


    messages.success(request, "Giriş başarılı. Parolanız güncellendi.")

    return redirect("home")
