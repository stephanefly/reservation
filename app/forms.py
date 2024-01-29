from django import forms
from .models import Client

class EventForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'  # Ou spécifiez les champs que vous souhaitez inclure dans le formulaire
        mail = forms.EmailField()
