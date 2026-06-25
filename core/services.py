from django.utils import timezone
from .models import (
    Order,
    WhatsAppMessageTemplate,
    WhatsAppMessageQueue,
    TourDay,
    DayActivity,
    ActivityProgress,
)


def get_order_phone(order):
    traveler = order.travelers.exclude(phone="").first()
    if traveler and traveler.phone:
        return traveler.phone

    return ""


def get_order_full_name(order):
    traveler = order.travelers.first()
    if traveler:
        full_name = f"{traveler.first_name} {traveler.last_name}".strip()
        if full_name:
            return full_name

    if order.email:
        return order.email.split("@")[0]

    return "Nomaya gezgini"


def create_whatsapp_message(order, key, context=None, day_activity=None, dedupe_suffix=""):
    context = context or {}

    phone = get_order_phone(order)
    if not phone:
        return None

    template = WhatsAppMessageTemplate.objects.filter(
        key=key,
        is_active=True
    ).first()

    if not template:
        return None

    message = template.render(context)

    if dedupe_suffix:
        dedupe_part = str(dedupe_suffix)
    elif day_activity:
        dedupe_part = str(day_activity.id)
    else:
        dedupe_part = "general"

    dedupe_key = f"{order.id}:{key}:{dedupe_part}"

    existing = WhatsAppMessageQueue.objects.filter(
        dedupe_key=dedupe_key
    ).first()

    if existing:
        return existing

    return WhatsAppMessageQueue.objects.create(
        order=order,
        day_activity=day_activity,
        template=template,
        phone=phone,
        message=message,
        dedupe_key=dedupe_key,
    )


def enqueue_paid_order_message(order):
    return create_whatsapp_message(
        order=order,
        key="order_paid_thank_you",
        context={
            "name": get_order_full_name(order),
            "tour_title": order.tour.title if order.tour else "",
            "tracking_code": order.tracking_code,
            "start_date": order.start_date or "",
            "assistant_url": "https://nomaya.co/nomayaasistan",
        },
        dedupe_suffix="paid",
    )


def get_today_first_pending_activity(order):
    if not order.start_date:
        return None

    today = timezone.localdate()

    if today != order.start_date:
        return None

    tour_day = TourDay.objects.filter(
        tour=order.tour,
        order=1
    ).select_related("day").first()

    if not tour_day:
        return None

    day_activities = DayActivity.objects.filter(
        day=tour_day.day
    ).select_related("activity", "day").order_by("order", "id")

    for da in day_activities:
        progress, _ = ActivityProgress.objects.get_or_create(
            order=order,
            day_activity=da
        )

        if progress.status == ActivityProgress.Status.PENDING:
            return da

    return None


def get_audio_link(order, day_activity, field_name):
    return (
        f"https://nomaya.co/audio/"
        f"{order.tracking_code}/"
        f"{day_activity.id}/"
        f"{field_name}/"
    )


def enqueue_activity_message(order, day_activity, key="tour_started_first_activity"):
    activity = day_activity.activity

    points = activity.points or []
    if isinstance(points, list):
        activity_points = "\n".join(str(p) for p in points)
    else:
        activity_points = str(points)

    return create_whatsapp_message(
        order=order,
        key=key,
        day_activity=day_activity,
        context={
            "name": get_order_full_name(order),
            "tour_title": order.tour.title if order.tour else "",
            "activity_title": activity.title,
            "activity_location": activity.location_text or "",
            "activity_duration": activity.duration_hours or "",
            "activity_points": activity_points,
            "tracking_code": order.tracking_code,
            "audio_on_the_way_url": get_audio_link(order, day_activity, "on-the-way"),
            "audio_at_location_url": get_audio_link(order, day_activity, "at-location"),
        },
        dedupe_suffix=f"activity-{day_activity.id}-{key}",
    )


def enqueue_tour_started_message_if_needed(order):
    if not order.start_date:
        return None

    today = timezone.localdate()

    if today != order.start_date:
        return None

    day_activity = get_today_first_pending_activity(order)

    if not day_activity:
        return None

    return enqueue_activity_message(
        order=order,
        day_activity=day_activity,
        key="tour_started_first_activity",
    )


def enqueue_next_activity_after_skip(order, skipped_day_activity):
    next_activity = DayActivity.objects.filter(
        day=skipped_day_activity.day,
        order__gt=skipped_day_activity.order,
    ).select_related("activity", "day").order_by("order", "id").first()

    if not next_activity:
        return create_whatsapp_message(
            order=order,
            key="tour_no_next_activity",
            context={
                "name": get_order_full_name(order),
                "tour_title": order.tour.title if order.tour else "",
            },
            dedupe_suffix=f"no-next-after-{skipped_day_activity.id}",
        )

    create_whatsapp_message(
        order=order,
        key="activity_skipped_reply",
        day_activity=skipped_day_activity,
        context={
            "name": get_order_full_name(order),
            "activity_title": skipped_day_activity.activity.title,
        },
        dedupe_suffix=f"skip-reply-{skipped_day_activity.id}",
    )

    return enqueue_activity_message(
        order=order,
        day_activity=next_activity,
        key="next_activity",
    )

import os
import shutil
from django.core.files import File
from django.conf import settings

from .models import IntroAudioLibrary, OrderIntroAudio


def normalize_name(name):
    return (name or "").strip().lower()


def create_order_intro_audios_for_name(order, first_name):
    name = normalize_name(first_name)

    if not name:
        return 0

    if order.intro_audios.exists():
        return 0

    library_items = IntroAudioLibrary.objects.filter(
        name=name,
        is_active=True
    )

    created_count = 0

    if library_items.exists():
        for item in library_items:
            with item.audio.open("rb") as f:
                intro = OrderIntroAudio(
                    order=order,
                    title=item.title or f"{first_name} intro",
                    source_name=name,
                    generated=False,
                )

                filename = os.path.basename(item.audio.name)
                intro.audio.save(filename, File(f), save=True)
                created_count += 1

        return created_count

    # Burada ses yoksa fallback placeholder.
    # Gerçek TTS entegrasyonunu sonra buraya bağlayacağız.
    return generate_intro_audio_for_order(order, first_name)


def generate_intro_audio_for_order(order, first_name):
    """
    Buraya sonra ElevenLabs / OpenAI TTS / başka servis bağlanır.
    Şimdilik ses yoksa 0 döndürür.
    """
    return 0
