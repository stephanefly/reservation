from django.db import migrations, models


OPTION_CONTENT = {
    "MurFloral": ("Décor photo premium pour obtenir un rendu plus chic sur les photos et vidéos.", "/static/img/allmur.jpg"),
    "Phonebooth": ("Livre d’or audio rétro pour enregistrer les messages vocaux des invités.", "/static/img/phonebooth.jpg"),
    "LivreOr": ("Support physique pour coller les tirages et conserver les messages des invités.", "/static/img/Livre-dor.jpg"),
    "Fond360": ("Fond lumineux pour améliorer le rendu visuel des vidéos 360 Booth.", "/static/img/fond360.jpg"),
    "PanneauBienvenue": ("Panneau personnalisé pour guider les invités et renforcer la décoration.", "/static/img/Welcomeboard.jpg"),
    "Holo3D": ("Animation visuelle originale pour donner un effet moderne à votre événement.", "/static/img/3dHolo.jpg"),
    "PanneauFontaine": ("Accueil élégant et visible pour l’entrée de salle, les mariages et les grands événements.", "/static/img/Panneau-fontaine.jpg"),
    "VideoLivreOr": ("Capture de messages vidéo pour garder des souvenirs plus vivants et émotionnels.", "/static/img/livre-dor-video.jpg"),
    "PhotographeVoguebooth": ("Photographe dédié pour obtenir des clichés plus propres et mieux cadrés.", "/static/img/photographe-voguebooth.jpg"),
    "ImpressionVoguebooth": ("Ajout d’impressions instantanées pour offrir un souvenir physique aux invités.", "/static/img/impression-voguebooth.jpg"),
    "DecorVoguebooth": ("Décoration spécifique pour améliorer l’effet studio et l’expérience photo.", "/static/img/decoration-voguebooth.jpg"),
    "PorteCles": ("Photo personnalisée intégrée dans un porte-clés souvenir à offrir aux invités.", "/static/img/PorteCles.png"),
    "magnets": ("Support magnétique rigide avec photo intégrée et protection plastifiée.", "/static/img/magnets.png"),
    "MagnetsSimple": ("Tirage photo classique avec magnet collé au dos. Simple, efficace et économique.", "/static/img/MagnetsSimple.png"),
}


def publish_existing_options(apps, schema_editor):
    Entry = apps.get_model("quote_control", "CatalogEntry")
    for entry in Entry.objects.filter(kind="option"):
        description, image_url = OPTION_CONTENT.get(entry.code, (entry.description, ""))
        entry.public_enabled = True
        if not entry.description and description:
            entry.description = description
        if not entry.image_url and image_url:
            entry.image_url = image_url
        entry.save(update_fields=["public_enabled", "description", "image_url"])

    # Exemples d’offres en brouillon : elles restent invisibles jusqu’à validation.
    Entry.objects.get_or_create(
        code="photobooth-ia",
        defaults={
            "kind": "option", "name": "Photobooth IA",
            "description": "Une expérience photo créative avec des portraits transformés par intelligence artificielle.",
            "price": 0, "active": False, "public_enabled": False,
        },
    )
    Entry.objects.get_or_create(
        code="mosaique-participative",
        defaults={
            "kind": "option", "name": "Mosaïque participative",
            "description": "Les photos des invités composent ensemble une grande image souvenir.",
            "price": 0, "active": False, "public_enabled": False,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("quote_control", "0002_catalogue")]

    operations = [
        migrations.AddField(
            model_name="catalogentry",
            name="public_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="catalogentry",
            name="image_url",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.RunPython(publish_existing_options, migrations.RunPython.noop),
    ]
