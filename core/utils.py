from django.shortcuts import get_object_or_404
from .models import Order

def ensure_session(request):
    if not request.session.session_key:
        request.session.save()  # session yaratır

def get_order_for_request_by_public(request, public_id):
    """
    Aynı kullanıcıya (login ise user, değilse session_key) ait public_id'li Order'ı getir.
    """
    qs = Order.objects.select_related("tour").filter(public_id=public_id)
    if request.user.is_authenticated:
        qs = qs.filter(  # login ise ek olarak e-mail eşleşmesi yerine kullanıcıya bağlamak istiyorsan user FK ekleyip filtreleyebilirsin
            # örn: user=request.user   (modelde user alanı yoksa bunu atla)
        )
    else:
        ensure_session(request)
        qs = qs.filter(session_key=request.session.session_key)

    return get_object_or_404(qs)

from django.utils.dateparse import parse_date
import re
from datetime import datetime

def _parse_dates_param(value: str):
    """
    URL'den gelen tarih aralıklarını yakalar.
    Örnekler:
      2025-10-08+-+2025-10-22
      2025-10-08 - 2025-10-22
      2025-10-08 to 2025-10-22
    Dönüş: (start_date, end_date)
    """
    if not value:
        return None, None

    # '+' işaretlerini boşlukla değiştir
    s = value.replace('+', ' ').replace('%2B', '+').strip()

    # Fazla boşlukları tek boşluğa indir
    s = re.sub(r'\s+', ' ', s)

    # Ayırıcılar: to, -, en dash, em dash
    parts = re.split(r'\s*(?:to|–|—|-)\s*', s, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        a, b = parts
        # Önce Django parse_date ile dene (YYYY-MM-DD)
        start = parse_date(a.strip())
        end = parse_date(b.strip())
        # Eğer None dönerse, datetime.strptime ile ikinci şans
        if not start:
            try:
                start = datetime.strptime(a.strip(), "%Y-%m-%d").date()
            except ValueError:
                start = None
        if not end:
            try:
                end = datetime.strptime(b.strip(), "%Y-%m-%d").date()
            except ValueError:
                end = None
        return start, end

    # Tek tarih varsa:
    d = parse_date(s.strip())
    if not d:
        try:
            d = datetime.strptime(s.strip(), "%Y-%m-%d").date()
        except ValueError:
            d = None
    return d, None
