from django import forms

from .image_storage import IMAGE_FORMATS
from .models import Campaign, Configuration, Template


class HTMLForm(forms.ModelForm):
    requires_html = True

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
        if not html and self.requires_html:
            self.add_error("html", "Saisissez, importez ou sélectionnez un modèle HTML.")
        else:
            data["html"] = html or ""
        return data


class CampaignForm(HTMLForm):
    requires_html = False

    audience = forms.ChoiceField(choices=Campaign.Audience.choices, label="Destinataires", initial="all")
    mode = forms.ChoiceField(choices=[("now", "Dès que possible"), ("later", "Planifié")], label="Envoi", initial="now")
    at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(
        format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
    ), label="Date et heure (Paris)")
    template = forms.ModelChoiceField(
        queryset=Template.objects.order_by("name"), required=False, label="Modèle enregistré"
    )
    name = forms.CharField(max_length=150, label="Nom interne", required=False)
    subject = forms.CharField(max_length=200, label="Objet", required=False)

    class Meta:
        model = Campaign
        fields = ["audience", "name", "subject", "template", "html", "upload", "mode", "at"]

    def clean_subject(self):
        subject = self.cleaned_data["subject"]
        if "\r" in subject or "\n" in subject:
            raise forms.ValidationError("L’objet doit tenir sur une ligne.")
        return subject

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.scheduled_at:
            self.initial.update(mode="later", at=self.instance.scheduled_at)

    def clean(self):
        data = super().clean()
        if data.get("mode") == "later" and not data.get("at") and not self.has_error("at"):
            self.add_error("at", "Indiquez la date et l’heure de l’envoi.")
        self.instance.scheduled_at = data.get("at") if data.get("mode") == "later" else None
        return data


class CampaignImageForm(forms.Form):
    image = forms.FileField(label="Fichier image", widget=forms.ClearableFileInput(
        attrs={"accept": "image/jpeg,image/png,image/webp,image/gif"}
    ))

    def clean_image(self):
        upload = self.cleaned_data["image"]
        if upload.size > 5 * 1024 * 1024:
            raise forms.ValidationError("L’image dépasse 5 Mo.")
        image = forms.ImageField().to_python(upload)
        if image.image.format not in IMAGE_FORMATS:
            raise forms.ValidationError("Utilisez une image JPEG, PNG, WebP ou GIF.")
        if image.image.width * image.image.height > 24_000_000:
            raise forms.ValidationError("L’image dépasse 24 mégapixels.")
        return image


class TemplateForm(HTMLForm):
    class Meta:
        model = Template
        fields = ["name", "html", "upload"]
        labels = {"name": "Nom"}


class CampaignNameForm(forms.Form):
    name = forms.CharField(label="Nom interne", max_length=Campaign._meta.get_field("name").max_length)


class CampaignTestForm(forms.Form):
    campaign = forms.ModelChoiceField(
        queryset=Campaign.objects.exclude(subject="").exclude(html="").order_by("-pk"),
        required=False,
        label="Campagne",
        empty_label="Message de vérification SMTP",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["campaign"].label_from_instance = self.campaign_label

    @staticmethod
    def campaign_label(campaign):
        return f"{campaign.name} · {campaign.subject}"


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
