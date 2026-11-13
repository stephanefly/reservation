from django.db import models
from .catalog import default_sources, default_products, default_pack_prices, default_product_prices


class AutoQuoteSettings(models.Model):
    """Réglages du devis automatique, une seule ligne connue (pk=1)."""

    enabled = models.BooleanField(default=False)
    catalog_enabled = models.BooleanField(default=False)  # Basculer sur les tarifs du catalogue apres validation
    sources = models.JSONField(default=default_sources)
    products = models.JSONField(default=default_products)
    packs = models.JSONField(default=list)
    product_prices = models.JSONField(default=default_product_prices)
    pack_prices = models.JSONField(default=default_pack_prices)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paramètres de devis automatique"
        verbose_name_plural = "Paramètres des devis automatiques"


class AutoQuoteLog(models.Model):
    OUTCOMES = [
        ("sent", "Devis envoyé"),
        ("manual", "Traitement manuel"),
        ("error", "Erreur d'envoi"),
    ]
    event_id = models.PositiveIntegerField(db_index=True)
    source = models.CharField(max_length=80, blank=True)
    outcome = models.CharField(max_length=8, choices=OUTCOMES, db_index=True)
    amount = models.PositiveIntegerField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Historique devis automatique"
        indexes = [models.Index(fields=["-created_at"], name="autodevis_recent_idx")]


class CatalogEntry(models.Model):
    """Catalogue commercial editable, sans modifier les devis ou l'historique."""

    KINDS = (
        ("product", "Machine / prestation"),
        ("option", "Option"),
        ("pack", "Pack"),
    )
    kind = models.CharField(max_length=12, choices=KINDS)
    code = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField(default=0, help_text="Prix TTC en euros")
    active = models.BooleanField(default=True)
    public_enabled = models.BooleanField(default=False)
    image_url = models.CharField(max_length=500, blank=True)
    auto_enabled = models.BooleanField(
        default=False, help_text="Autoriser en devis auto, seulement si le mode catalogue est active"
    )
    # Codes commerciaux ; les champs hors du modele Event restent manuels.
    product_codes = models.JSONField(default=list, blank=True)
    option_codes = models.JSONField(default=list, blank=True)
    quantities = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["kind", "name", "code"]
        verbose_name = "Entree de catalogue"
        verbose_name_plural = "Catalogue commercial"

    def __str__(self):
        return f"{self.name} ({self.code})"
