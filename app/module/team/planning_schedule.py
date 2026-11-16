from datetime import datetime, timedelta


PLANNED_PRODUCT_FIELDS = (
    'photobooth',
    'miroirbooth',
    'videobooth',
    'voguebooth',
    'ipadbooth',
    'airbooth',
)

PLANNED_OPTION_FIELDS = (
    'MurFloral',
    'Phonebooth',
    'LivreOr',
    'Fond360',
    'PanneauBienvenue',
    'PhotographeVoguebooth',
    'ImpressionVoguebooth',
    'DecorVoguebooth',
    'Holo3D',
    'PanneauFontaine',
    'VideoLivreOr',
    'panneaux_xxl',
    'magnets',
    'PorteCles',
    'MagnetsSimple',
    'livraison',
)


def get_team_planning_values(event):
    """Move the team start earlier and extend its duration per selected item."""
    details = getattr(event, 'event_details', None)
    option = getattr(event, 'event_option', None)
    horaire = getattr(details, 'horaire', None)
    duree = getattr(option, 'duree', None)
    product = getattr(event, 'event_product', None)

    item_count = sum(bool(getattr(product, field, False)) for field in PLANNED_PRODUCT_FIELDS)
    item_count += sum(bool(getattr(option, field, False)) for field in PLANNED_OPTION_FIELDS)
    extra_minutes = 30 * item_count

    team_start = horaire
    if horaire:
        try:
            start_time = datetime.strptime(str(horaire).strip()[:5], '%H:%M')
            team_start = start_time - timedelta(minutes=extra_minutes)
            team_start = team_start.strftime('%Hh%M') if team_start.minute else team_start.strftime('%Hh')
        except (TypeError, ValueError):
            pass

    team_duration = None
    if duree is not None:
        total_minutes = int(duree * 60) + extra_minutes
        team_duration = f'{total_minutes // 60}h'
        if total_minutes % 60:
            team_duration += f'{total_minutes % 60:02d}'

    return team_start, team_duration
