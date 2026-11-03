from django.db import migrations, models
import django.db.models.deletion
import quote_control.catalog


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AutoQuoteSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=False)),
                ("sources", models.JSONField(default=quote_control.catalog.default_sources)),
                ("products", models.JSONField(default=quote_control.catalog.default_products)),
                ("packs", models.JSONField(default=list)),
                ("product_prices", models.JSONField(default=quote_control.catalog.default_product_prices)),
                ("pack_prices", models.JSONField(default=quote_control.catalog.default_pack_prices)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Paramètres de devis automatique",
                "verbose_name_plural": "Paramètres des devis automatiques",
            },
        ),
        migrations.CreateModel(
            name="AutoQuoteLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_id", models.PositiveIntegerField(db_index=True)),
                ("source", models.CharField(blank=True, max_length=80)),
                ("outcome", models.CharField(choices=[
                    ("sent", "Devis envoyé"),
                    ("manual", "Traitement manuel"),
                    ("error", "Erreur d'envoi"),
                ], db_index=True, max_length=8)),
                ("amount", models.PositiveIntegerField(blank=True, null=True)),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"], "verbose_name": "Historique devis automatique"},
        ),
        migrations.AddIndex(
            model_name="autoquotelog",
            index=models.Index(fields=["-created_at"], name="autodevis_recent_idx"),
        ),
    ]
