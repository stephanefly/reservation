from django.db import migrations, models
import django.db.models.deletion


PRODUCTS = [
    ("photobooth", "Photobooth", 400),
    ("miroirbooth", "Miroirbooth", 500),
    ("videobooth", "360 Booth", 450),
    ("voguebooth", "Vogue Booth", 550),
    ("airbooth", "360 Airbooth", 450),
    ("ipadbooth", "iPad Booth", 250),
]
OPTIONS = [
    ("MurFloral", "Mur floral", 50),
    ("Phonebooth", "Phonebooth audio", 50),
    ("LivreOr", "Livre d'or", 70),
    ("Fond360", "Fond 360", 100),
    ("PanneauBienvenue", "Panneau de bienvenue", 70),
    ("Holo3D", "Hologramme 3D", 50),
    ("PanneauFontaine", "Panneau Fontaine", 200),
    ("VideoLivreOr", "Livre d'or video", 200),
    ("PhotographeVoguebooth", "Photographe Vogue", 150),
    ("ImpressionVoguebooth", "Impressions Vogue", 100),
    ("DecorVoguebooth", "Decor Vogue", 50),
    ("PorteCles", "Porte-cles photo (unite)", 2),
    ("magnets", "Magnets (unite)", 2),
    ("MagnetsSimple", "Magnets simples (unite)", 2),
]
PACKS = [
    ("souvenirs", "Pack Souvenirs", 600, ["photobooth"], ["Phonebooth"], {"PorteCles": 100}),
    ("immersion-360", "Pack Immersion 360", 700, ["videobooth"], ["VideoLivreOr", "Fond360"], {}),
    ("signature", "Pack Signature", 800, ["miroirbooth"], ["VideoLivreOr", "PanneauFontaine"], {}),
    ("duo-vip", "Pack Duo VIP", 850, ["miroirbooth", "videobooth"], ["Phonebooth", "MurFloral"], {}),
    ("vogue-premium", "Pack Vogue Premium", 700, ["voguebooth"], ["PhotographeVoguebooth", "ImpressionVoguebooth"], {}),
    ("mariage-prestige", "Pack Mariage Prestige", 1200, ["miroirbooth", "videobooth", "voguebooth"], ["Fond360", "MurFloral"], {}),
]


def seed_catalog(apps, schema_editor):
    Entry = apps.get_model("quote_control", "CatalogEntry")
    for code, name, price in PRODUCTS:
        Entry.objects.get_or_create(
            code=code, defaults={"kind": "product", "name": name, "price": price},
        )
    for code, name, price in OPTIONS:
        Entry.objects.get_or_create(
            code=code, defaults={"kind": "option", "name": name, "price": price},
        )
    for code, name, price, products, options, quantities in PACKS:
        Entry.objects.get_or_create(
            code=code, defaults={
                "kind": "pack", "name": name, "price": price,
                "product_codes": products, "option_codes": options,
                "quantities": quantities,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("quote_control", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="autoquotesettings",
            name="catalog_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="CatalogEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[
                    ("product", "Machine / prestation"), ("option", "Option"), ("pack", "Pack"),
                ], max_length=12)),
                ("code", models.SlugField(max_length=60, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("price", models.PositiveIntegerField(default=0, help_text="Prix TTC en euros")),
                ("active", models.BooleanField(default=True)),
                ("auto_enabled", models.BooleanField(
                    default=False, help_text="Autoriser en devis auto, seulement si le mode catalogue est active",
                )),
                ("product_codes", models.JSONField(blank=True, default=list)),
                ("option_codes", models.JSONField(blank=True, default=list)),
                ("quantities", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["kind", "name", "code"], "verbose_name": "Entree de catalogue",
                     "verbose_name_plural": "Catalogue commercial"},
        ),
        migrations.RunPython(seed_catalog, migrations.RunPython.noop),
    ]
