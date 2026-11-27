from django import forms
from django.utils import timezone

from .models import Campaign, Configuration, Template


class AudienceForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["audience"]
        labels = {"audience": "Destinataires"}


class HTMLForm(forms.ModelForm):
    html = forms.CharField(widget=forms.Textarea, required=False, label="Code HTML", max_length=500000)
    upload = forms.FileField(required=False, label="Fichier HTML")

    def clean(self):
        data = super().clean()
        uploaded = data.get("upload")
        html = data.get("html")
        if uploaded:
            if uploaded.size > 500000:
                self.add_error("upload", "Le fichier dépasse 500 Ko.")
            else:
                try:
                    html = uploaded.read().decode("utf-8-sig")
                except UnicodeError:
                    self.add_error("upload", "Le fichier doit être encodé en UTF-8.")
        if not html and data.get("template"):
            html = data["template"].html
        if not html or not html.strip():
            self.add_error("html", "Saisissez, importez ou sélectionnez un modèle HTML.")
        else:
            data["html"] = html
        return data


class ContentForm(HTMLForm):
    template = forms.ModelChoiceField(
        queryset=Template.objects.order_by("name"), required=False, label="Modèle enregistré"
    )
    name = forms.CharField(max_length=150, label="Nom interne")
    subject = forms.CharField(max_length=200, label="Objet")

    class Meta:
        model = Campaign
        fields = ["name", "subject", "template", "html", "upload"]

    def clean_subject(self):
        subject = self.cleaned_data["subject"]
        if "\r" in subject or "\n" in subject:
            raise forms.ValidationError("L’objet doit tenir sur une ligne.")
        return subject


class TemplateForm(HTMLForm):
    class Meta:
        model = Template
        fields = ["name", "html", "upload"]
        labels = {"name": "Nom"}


class ScheduleForm(forms.Form):
    mode = forms.ChoiceField(choices=[("now", "Dès que possible"), ("later", "Planifié")], label="Envoi")
    at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(
        format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
    ), label="Date et heure (Paris)")

    def clean(self):
        data = super().clean()
        if data.get("mode") == "now":
            data["at"] = None
        elif data.get("mode") == "later" and (not data.get("at") or data["at"] <= timezone.now()):
            self.add_error("at", "Choisissez une date et une heure futures.")
        return data


class TestForm(forms.Form):
    email = forms.EmailField(label="Adresse de test")


class ConfigurationForm(forms.ModelForm):
    class Meta:
        model = Configuration
        fields = ["enabled", "sender", "hourly_limit"]
        labels = {"enabled": "Activer les campagnes", "sender": "Adresse d’expédition",
                  "hourly_limit": "Limite d’envoi par heure"}

    def clean(self):
        data = super().clean()
        if data.get("enabled") and not data.get("sender"):
            self.add_error("sender", "Indiquez l’adresse d’expédition.")
        return data
