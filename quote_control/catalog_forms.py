"""Saisie du catalogue. Les codes existants ne sont jamais renommes."""
from django import forms

from app.module.data_bdd.price import PRIX_PRODUITS
from .catalog import PRODUCT_KEYS
from .models import CatalogEntry

# Correspond aux vrais champs EventOption ; les autres options sont manuelles.
BOOL_OPTIONS = (
    "MurFloral", "Phonebooth", "LivreOr", "Fond360", "PanneauBienvenue",
    "Holo3D", "PanneauFontaine", "VideoLivreOr", "PhotographeVoguebooth",
    "ImpressionVoguebooth", "DecorVoguebooth",
)
QUANTITY_OPTIONS = ("PorteCles", "magnets", "MagnetsSimple")


class CatalogEntryForm(forms.ModelForm):
    product_codes = forms.MultipleChoiceField(required=False, label="Machines incluses",
                                               help_text="Cochez les machines de ce pack.",
                                               widget=forms.CheckboxSelectMultiple)
    option_codes = forms.MultipleChoiceField(required=False, label="Options incluses",
                                              help_text="Cochez les options comprises dans le tarif.",
                                              widget=forms.CheckboxSelectMultiple)
    quantity_PorteCles = forms.IntegerField(min_value=0, max_value=10000, required=False, initial=0,
                                            label="Porte-cles inclus")
    quantity_magnets = forms.IntegerField(min_value=0, max_value=10000, required=False, initial=0,
                                          label="Magnets inclus")
    quantity_MagnetsSimple = forms.IntegerField(min_value=0, max_value=10000, required=False, initial=0,
                                                label="Magnets simples inclus")

    class Meta:
        model = CatalogEntry
        fields = ("kind", "code", "name", "description", "price",
                  "active", "auto_enabled")
        labels = {
            "kind": "Type d'offre", "code": "Code unique", "name": "Nom commercial",
            "description": "Description", "price": "Prix TTC (€)",
            "active": "Visible et disponible", "auto_enabled": "Éligible aux devis automatiques",
        }
        help_texts = {
            "kind": "Machine, option ou pack.",
            "code": "Identifiant sans espace, par exemple ipadbooth. Non modifiable ensuite.",
            "name": "Nom utilisé dans le catalogue CRM.",
            "description": "Facultative. Décrivez l'offre en une phrase.",
            "price": "Machines et packs déjà présents : affiché sur Tarifs et Brochure.",
            "active": "Décochez pour retirer l'offre de la vente. Les anciens devis restent intacts.",
            "auto_enabled": "N'envoie aucun e-mail seul. Nécessite les autorisations dans Catalogue > Paramètres et simulation.",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        products = CatalogEntry.objects.filter(kind="product").order_by("name")
        options = CatalogEntry.objects.filter(kind="option").order_by("name")
        self.fields["product_codes"].choices = [(x.code, x.name) for x in products]
        self.fields["option_codes"].choices = [(x.code, x.name) for x in options]
        if self.instance and self.instance.pk:
            self.fields["kind"].disabled = True
            self.fields["code"].disabled = True
            if not self.is_bound:
                self.initial["product_codes"] = self.instance.product_codes
                self.initial["option_codes"] = self.instance.option_codes
                for code in QUANTITY_OPTIONS:
                    self.initial["quantity_" + code] = self.instance.quantities.get(code, 0)

    def clean(self):
        values = super().clean()
        kind = values.get("kind")
        code = values.get("code")
        price = values.get("price")
        active = values.get("active")
        auto = values.get("auto_enabled")
        products = values.get("product_codes") or []
        options = values.get("option_codes") or []
        quantities = {
            code: values.get("quantity_" + code, 0) or 0
            for code in QUANTITY_OPTIONS
        }
        if price is not None and price > 100000:
            self.add_error("price", "Prix hors limite de securite (100 000 euros).")
        if kind == "pack" and not products:
            self.add_error("product_codes", "Un pack doit contenir au moins une machine.")
        if kind != "pack" and (products or options or any(quantities.values())):
            self.add_error("kind", "La composition est reservee aux packs.")
        if auto:
            if not active:
                self.add_error("auto_enabled", "Une offre inactive ne peut pas etre automatique.")
            if price is not None and price < 350:
                self.add_error("price", "Tarif automatique inferieur au seuil de 350 euros.")
            if kind == "option":
                self.add_error("auto_enabled", "Prix d'option : calcul historique du PDF conserve. Automatisation impossible ici.")
            elif kind == "product":
                if code not in PRODUCT_KEYS:
                    self.add_error("auto_enabled", "Nouvelle machine sans champ EventProduct : devis manuel uniquement.")
                elif price is not None and price > PRIX_PRODUITS[code]:
                    self.add_error("price", "Le tarif automatique depasse le prix brut du PDF existant.")
            elif kind == "pack":
                if not set(products).issubset(PRODUCT_KEYS):
                    self.add_error("auto_enabled", "Pack avec machine non geree par le formulaire de devis.")
                if not set(options).issubset(BOOL_OPTIONS):
                    self.add_error("auto_enabled", "Pack avec option non geree par le calcul existant.")
                # Les quantites gerees sont strictement celles du modele EventOption.
        return values

    def save(self, commit=True):
        item = super().save(commit=False)
        if item.kind == "pack":
            item.product_codes = self.cleaned_data.get("product_codes", [])
            item.option_codes = self.cleaned_data.get("option_codes", [])
            item.quantities = {
                code: self.cleaned_data.get("quantity_" + code, 0) or 0
                for code in QUANTITY_OPTIONS
                if self.cleaned_data.get("quantity_" + code, 0)
            }
        else:
            item.product_codes = []
            item.option_codes = []
            item.quantities = {}
        if commit:
            item.save()
        return item
