# apps.py'de ready() içinde import etmeyi unutma
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender=TourDay)
def renumber_titles(sender, instance, **kwargs):
    qs = TourDay.objects.filter(tour=instance.tour).order_by("order", "id")
    for idx, td in enumerate(qs, start=1):
        # mevcut başlığın “Day X:” kısmını güncelle
        base = td.title.split(":", 1)[1].strip() if ":" in (td.title or "") else (
            td.day.title or (td.day.city.name if getattr(td.day, "city", None) else "Program")
        )
        new_title = f"Day {idx}: {base}"
        if td.title != new_title:
            TourDay.objects.filter(pk=td.pk).update(title=new_title)

# core/signals.py

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from core.utils.telegram import send_telegram_message


@receiver(user_logged_in)
def admin_login_notification(sender, request, user, **kwargs):
    if user.is_staff or user.is_superuser:
        ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "-"))
        user_agent = request.META.get("HTTP_USER_AGENT", "-")

        send_telegram_message(
            f"🔐 <b>Admin Login</b>\n\n"
            f"Kullanıcı: {user.email or user.username}\n"
            f"Staff: {user.is_staff}\n"
            f"Superuser: {user.is_superuser}\n"
            f"IP: {ip}\n"
            f"User-Agent: {user_agent[:250]}"
        )
