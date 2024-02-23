# forms.py
from django import forms
from .models import Cost

class CostForm(forms.ModelForm):
    class Meta:
        model = Cost
        fields = ['name_cost', 'type_cost', 'price_cost']
