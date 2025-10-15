from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["pax", "same_room"]
        widgets = {
            "pax": forms.NumberInput(attrs={"min": 1, "class": "form-control"}),
            "same_room": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "pax": "Kişi Sayısı",
            "same_room": "Aynı odada mı kalınacak?",
        }
