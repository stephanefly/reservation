from django import forms
from .models import Cost
import datetime


class CostForm(forms.ModelForm):
    # Calculer la date par défaut (3 jours avant aujourd'hui)
    default_date = datetime.date.today() - datetime.timedelta(days=3)

    # Définir la date par défaut pour le champ created_at
    created_at = forms.DateField(
        initial=default_date,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Cost
        fields = ['name_cost', 'type_cost', 'price_cost', 'created_at']
