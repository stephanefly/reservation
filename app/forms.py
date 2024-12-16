from django import forms
from .models import Cost, EventAcompte, EventDetails
import datetime


class CostForm(forms.ModelForm):
    # Calculer la date par défaut (3 jours avant aujourd'hui)
    default_date = datetime.date.today() - datetime.timedelta(days=2)

    # Définir la date par défaut pour le champ created_at
    created_at = forms.DateField(
        initial=default_date,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Cost
        fields = ['type_cost', 'price_cost', 'created_at', 'frecency']


class ValidationForm(forms.ModelForm):

    date_payement = forms.DateField(
        initial=datetime.date.today(),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    MONTANT_CHOICES = [
        (50, '50 euros'),
        (100, '100 euros'),
        ('autre_montant', 'Autre montant'),
    ]

    montant_acompte = forms.ChoiceField(choices=MONTANT_CHOICES, required=True)
    autre_montant = forms.IntegerField(min_value=0, required=False)

    def clean(self):
        cleaned_data = super().clean()
        montant = cleaned_data.get("montant_acompte")
        autre = cleaned_data.get("autre_montant")

        if montant == 'autre_montant' and autre is not None:
            # Remplacez la valeur de 'montant_acompte' par la valeur de 'autre_montant'
            cleaned_data['montant_acompte'] = autre

        return cleaned_data

    class Meta:
        model = EventAcompte
        fields = ['montant_acompte', 'mode_payement', 'date_payement']


class CommentaireForm(forms.ModelForm):
    class Meta:
        model = EventDetails
        fields = ['comment_client']


class HoraireForm(forms.ModelForm):
    class Meta:
        model = EventDetails
        fields = ['horaire']
