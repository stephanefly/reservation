from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = '__all__'  # Ou spécifiez les champs que vous souhaitez inclure dans le formulaire
        mail = forms.EmailField()
