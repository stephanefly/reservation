from django.db import models
from .catalog import default_sources, default_products, default_pack_prices, default_product_prices


class AutoQuoteSettings(models.Model):
    """Réglages du devis automatique, une seule ligne connue (pk=1)."""

    enabled = models.BooleanField(default=False)
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
