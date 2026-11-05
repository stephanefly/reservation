"""Simulation d'une demande fictive, sans creation d'Event, d'email ou de PDF."""
from datetime import date

from django import forms

from app.models import Client, EventDetails, EventOption, EventProduct
from app.module.data_bdd.event_pricing import OPTION_NAMES

from .catalog import PRODUITS
from .engine import analyse_quote


# Les options correspondent uniquement aux champs EventOption existants.
SIM_OPTIONS = (
    ("Phonebooth", "Phonebooth audio"),
    ("LivreOr", "Livre d'or"),
    ("MurFloral", "Mur floral"),
    ("Fond360", "Fond LED 360"),
    ("VideoLivreOr", "Livre d'or video"),
    ("PanneauFontaine", "Panneau Fontaine"),
    ("PhotographeVoguebooth", "Photographe Vogue"),
    ("ImpressionVoguebooth", "Impressions Vogue"),
    ("DecorVoguebooth", "Decor Vogue"),
    ("PanneauBienvenue", "Panneau de bienvenue"),
    ("Holo3D", "Hologramme 3D"),
)
SOURCE_CHOICES = (
    ("INSTAGRAM", "Instagram"),
    ("SITE INTERNET", "Site internet"),
    ("LINKEDIN", "LinkedIn"),
    ("LEBONCOIN", "Leboncoin"),
    ("RECOMMENDATION", "Recommandation (manuel)"),
)


class QuoteSimulationForm(forms.Form):
    """Saisir une demande type avec les memes gardes-fous que le moteur reel."""

    products = forms.MultipleChoiceField(
        choices=PRODUITS,
        widget=forms.CheckboxSelectMultiple,
        label="Machines souhaitees",
        required=True,
        initial=["photobooth"],
    )
    duration = forms.TypedChoiceField(
        choices=((3, "3 heures"), (5, "5 heures")),
        coerce=int,
        initial=5,
        label="Duree",
    )
    source = forms.ChoiceField(
        choices=SOURCE_CHOICES,
        initial="INSTAGRAM",
        label="Origine de la demande",
    )
    postal_code = forms.RegexField(
        regex=r"^[0-9]{5}$",
        initial="75001",
        label="Code postal de l'evenement",
        error_messages={"invalid": "Saisissez un code postal a 5 chiffres."},
    )
    options = forms.MultipleChoiceField(
        choices=SIM_OPTIONS,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Options souhaitees",
    )
    portecles = forms.IntegerField(
        required=False, min_value=0, max_value=1000,
        initial=0, label="Porte-cles (quantite)",
    )
    client_name = forms.CharField(
        required=False, max_length=120, label="Nom du client",
    )
    company_name = forms.CharField(
        required=False, max_length=120, label="Nom de l'entreprise",
    )
    business = forms.BooleanField(
        required=False, label="Demande d'entreprise (traitement manuel)",
    )

    def simulate(self, settings):
        """Utiliser le vrai moteur sur des instances Django *non sauvegardees*."""
        if not self.is_valid():
            raise ValueError("La demande de simulation est invalide.")

        data = self.cleaned_data
        selection = set(data["products"])
        selected_options = set(data["options"])

        # Ces objets n'ont pas de PK ; aucune operation save n'est appelee.
        event = type("SimulatedEvent", (), {})()
        event.client = Client(
            nom=data.get("client_name") or "Simulation",
            how_find=data["source"],
            raison_sociale=data.get("company_name") or data["business"],
        )
        event.event_product = EventProduct(**{
            key: key in selection for key, _ in PRODUITS
        })
        event.event_option = EventOption(
            duree=data["duration"],
            PorteCles=data.get("portecles") or 0,
            **{key: key in selected_options for key in OPTION_NAMES},
        )
        event.event_details = EventDetails(
            date_evenement=date.today(), adresse_evenement="Simulation",
            ville_evenement="Simulation",
            code_postal_evenement=int(data["postal_code"]),
        )

        result = analyse_quote(event, settings, preview=True)
        # Utiliser les remises exactement calculees par le moteur de devis.
        # Le total avant remise inclut options et deplacement eventuels.
        price_detail = None
        if result.get("eligible"):
            calculation = result["calculation"]
            product_discount = max(0, int(calculation.get("reduc_product") or 0))
            pack_discount = max(0, int(calculation.get("reduc_all") or 0))
            price_detail = {
                "reference": result["amount"] + product_discount + pack_discount,
                "product_discount": product_discount,
                "pack_discount": pack_discount,
                "discount": product_discount + pack_discount,
                "final": result["amount"],
            }
        return {
            "analysis": result,
            "client_name": data.get("client_name") or "",
            "company_name": data.get("company_name") or "",
            "price_detail": price_detail,
            "products": [label for key, label in PRODUITS if key in selection],
            "options": [label for key, label in SIM_OPTIONS if key in selected_options],
            "duration": data["duration"],
            "postal_code": data["postal_code"],
            "quantity": data.get("portecles") or 0,
        }
