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
