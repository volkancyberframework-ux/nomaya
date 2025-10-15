# admin.py
from decimal import Decimal

from django import forms
from django.contrib import admin
from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase

from .models import (
    Country, City, Airport, Airline, Flight,
    Tour, TourDay, TourPhoto, Bullet, TourBullet,
    Day, DayImage, Hotel, AirportTransfer,
    Activity, DayFlight, DayTransfer, DayHotel, DayActivity,
    Order, Traveler, TourType
)


# ─────────────────────────────
# Travelers
# ─────────────────────────────
class TravelerInline(admin.TabularInline):
    model = Traveler
    extra = 0
    fields = ("title", "first_name", "last_name", "dob", "passport_no", "phone")
    ordering = ("id",)

@admin.register(Traveler)
class TravelerAdmin(admin.ModelAdmin):
    list_display = (
        "id", "order", "title", "first_name", "last_name",
        "dob", "passport_no", "phone", "created_at"
    )
    list_filter = ("order",)
    search_fields = (
        "first_name", "last_name", "passport_no", "phone",
        "order__id", "order__tour__title"
    )
    ordering = ("id",)


# ─────────────────────────────
# Orders
# ─────────────────────────────
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "tour", "pax", "email",
        "start_date", "end_date",      # tarihler
        "total_price", "is_paid", "created_at",
    )
    list_display_links = ("id", "tour")
    ordering = ("-created_at",)
    inlines = [TravelerInline]

    list_filter = (
        "is_paid",
        "hide_flights", "hide_transfers", "hide_hotels",
        ("start_date", admin.DateFieldListFilter),
        ("end_date", admin.DateFieldListFilter),
        "tour",
    )
    search_fields = ("public_id", "email", "tour__title")

    readonly_fields = ("public_id", "created_at",)
    fieldsets = (
        ("Bağlantı", {"fields": ("tour", "public_id", "session_key")}),
        ("Müşteri", {"fields": ("email", "pax", "same_room")}),
        ("Tarihler", {"fields": ("start_date", "end_date")}),
        ("Görünürlük / Dahiller", {
            "fields": ("hide_flights", "hide_transfers", "hide_hotels")
        }),
        ("Ödeme", {"fields": ("total_price", "is_paid", "created_at")}),
    )

    # (opsiyonel) tek sütunda aralık göstermek istersen:
    def date_range(self, obj):
        if obj.start_date and obj.end_date:
            return f"{obj.start_date:%d %b} – {obj.end_date:%d %b %Y}"
        return ""
    date_range.short_description = "Tarih Aralığı"


# ─────────────────────────────
# Tour inlines
# ─────────────────────────────
class TourDayInline(admin.TabularInline):  # SortableInlineAdminMixin kullanıyorsan: inherit et
    model = TourDay
    extra = 0
    fields = ("day", "order", "title")     # ❗️date/note yok
    readonly_fields = ()
    ordering = ("order", "id")


class TourPhotoInline(SortableInlineAdminMixin, admin.TabularInline):
    model = TourPhoto
    extra = 1
    max_num = 10
    fields = ("order", "image", "alt_text")
    ordering = ("order",)


class TourBulletInline(SortableInlineAdminMixin, admin.TabularInline):
    model = TourBullet
    extra = 1
    autocomplete_fields = ("bullet",)
    fields = ("section", "bullet", "order")
    ordering = ("section", "order")


# ─────────────────────────────
# Day inlines (medya ve fiyat gösterimleri)
# ─────────────────────────────
class DayImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = DayImage
    extra = 1
    max_num = 3
    fields = ("order", "image", "alt_text")
    ordering = ("order",)


class DayFlightInline(SortableInlineAdminMixin, admin.TabularInline):
    model = DayFlight
    extra = 0
    autocomplete_fields = ("flight",)
    fields = ("order", "flight", "flight_price")
    readonly_fields = ("flight_price",)
    ordering = ("order",)

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
    fields = ("order", "transfer", "transfer_price")
    readonly_fields = ("transfer_price",)
    ordering = ("order",)

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
    fields = ("order", "hotel", "hotel_price")
    readonly_fields = ("hotel_price",)
    ordering = ("order",)

    def hotel_price(self, obj):
        h = getattr(obj, "hotel", None)
        if not h:
            return "—"
        return f"{h.price_per_night} {getattr(h, 'price_currency', '')}".strip()
    hotel_price.short_description = "Hotel Price (per night)"


class DayActivityInline(SortableInlineAdminMixin, admin.TabularInline):
    model = DayActivity
    extra = 0
    autocomplete_fields = ("activity",)
    fields = ("order", "activity", "activity_price")
    readonly_fields = ("activity_price",)
    ordering = ("order",)

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
        "title", "duration_label", "days_total_for_list",
        "commission", "price", "price_currency", "is_published"
    )
    list_filter = ("is_published", "places_covered__country", "price_currency", "tour_types")
    search_fields = ("title", "overview", "info")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("places_covered", "tour_types")

    readonly_fields = ("duration_label", "start_point", "end_point", "days_total_preview",)
    fields = (
        "title", "slug", "is_published", "badge_text",
        ("start_date", "end_date"),             # Tour modelinde varsa göster
        "overview", "info",
        "places_covered",
        "tour_types",
        ("arrival_flight", "departure_flight"),
        ("commission", "price_currency"),
        "days_total_preview",
        "price",
    )
    inlines = [TourDayInline, TourPhotoInline, TourBulletInline]

    # Liste görünümünde toplam gün fiyatını göster
    def days_total_for_list(self, obj):
        return obj.days_total_amount()
    days_total_for_list.short_description = "Days Total"

    # Detay sayfasında readonly özet
    def days_total_preview(self, obj):
        base = obj.days_total_amount() if obj.pk else Decimal("0.00")
        comm = obj.commission or Decimal("1.00")
        try:
            preview = (Decimal(base) * Decimal(comm)).quantize(Decimal("0.01"))
        except Exception:
            preview = base
        return f"Days Total: {base} × Commission ({comm}) → Price = {preview}"
    days_total_preview.short_description = "Computed Price Preview"

    # Kaydederken tur fiyatını yeniden hesapla
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
    list_display = ("city", "day_number", "title", "price", "price_currency")
    list_filter = ("city__country", "city", "price_currency")
    search_fields = ("title", "description")
    readonly_fields = ("price",)
    inlines = [DayImageInline, DayFlightInline, DayTransferInline, DayHotelInline, DayActivityInline]


# ─────────────────────────────
# Basit modeller
# ─────────────────────────────
@admin.register(Bullet)
class BulletAdmin(admin.ModelAdmin):
    list_display = ("text", "icon", "is_active", "tags")
    list_filter = ("icon", "is_active")
    search_fields = ("text", "tags")

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "iso2")
    search_fields = ("name", "iso2")

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
    list_filter = ("country",)
    search_fields = ("name",)

@admin.register(TourType)
class TourTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("iata", "name", "city")
    list_filter = ("city__country",)
    search_fields = ("iata", "name")

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        "flight_number", "airline", "origin", "destination",
        "departure_time", "arrival_time", "duration_minutes",
        "price", "price_currency"
    )
    list_filter = ("airline", "origin__city__country", "destination__city__country", "price_currency")
    search_fields = ("flight_number",)

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "star", "price_per_night", "price_currency")
    list_filter = ("city__country", "city", "star", "price_currency")
    search_fields = ("name", "address")

@admin.register(AirportTransfer)
class AirportTransferAdmin(admin.ModelAdmin):
    list_display = ("city", "direction", "airport", "hotel", "vehicle_type", "price", "price_currency")
    list_filter = ("city__country", "city", "direction", "vehicle_type", "price_currency")
    search_fields = ("airport__iata", "hotel__name")

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "location_text", "duration_hours")
    search_fields = ("title", "location_text")
