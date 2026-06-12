from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def qs_without(context, *exclude_keys):
    """
    Mevcut GET parametrelerini kopyalar, verilen anahtarları (örn: 'page') çıkarır
    ve yeniden urlencode eder. Kullanım: {% qs_without 'page' as qs %}
    """
    request = context["request"]
    params = request.GET.copy()
    for k in exclude_keys:
        params.pop(k, None)
    return urlencode(params)
