from django import forms
from .catalog import (
    SOURCES, PRODUITS, PACKS, default_pack_prices, default_product_prices,
)


class QuoteControlForm(forms.Form):
    enabled = forms.BooleanField(required=False, label="Activer les devis automatiques")
    sources = forms.MultipleChoiceField(
        choices=SOURCES, required=False, widget=forms.CheckboxSelectMultiple,
    )
    products = forms.MultipleChoiceField(
        choices=PRODUITS, required=False, widget=forms.CheckboxSelectMultiple,
    )
    packs = forms.MultipleChoiceField(
        choices=[(p[0], p[1]) for p in PACKS], required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    confirm_activation = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        config = kwargs.pop("config", None)
        super().__init__(*args, **kwargs)
        for key, label in PRODUITS:
            self.fields["product_" + key] = forms.IntegerField(
                required=True, min_value=250, max_value=10000,
                label=label + " (5 h TTC)",
            )
        for key, label, *_ in PACKS:
            self.fields["pack_" + key] = forms.IntegerField(
                required=True, min_value=350, max_value=10000,
                label=label + " (€ TTC)",
            )

        if config and not self.is_bound:
            self.initial = {
                "enabled": config.enabled,
                "sources": config.sources,
                "products": config.products,
                "packs": config.packs,
                **{"product_" + k: config.product_prices.get(k, value)
                   for k, value in default_product_prices().items()},
                **{"pack_" + k: config.pack_prices.get(k, value)
                   for k, value in default_pack_prices().items()},
            }

    def clean(self):
        data = super().clean()
        if data.get("enabled") and not data.get("confirm_activation"):
            self.add_error(
                "confirm_activation",
                "Confirmez que les prix et l'envoi des e-mails ont été testés.",
            )
        return data

    def save_to_config(self, config):
        if not self.is_valid():
            raise ValueError("La configuration contient des erreurs.")
        config.enabled = self.cleaned_data["enabled"]
        config.sources = self.cleaned_data["sources"]
        config.products = self.cleaned_data["products"]
        config.packs = self.cleaned_data["packs"]
        config.product_prices = {
            key: self.cleaned_data["product_" + key] for key, _ in PRODUITS
        }
        config.pack_prices = {
            pack[0]: self.cleaned_data["pack_" + pack[0]] for pack in PACKS
        }
        config.save()
        return config
