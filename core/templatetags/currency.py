from django import template
register = template.Library()

_SYMBOLS = {"USD": "$", "EUR": "€", "TRY": "₺"}

@register.filter(name="currency_symbol")
def currency_symbol(code: str) -> str:
    return _SYMBOLS.get((code or "").upper(), "")
