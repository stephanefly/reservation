from datetime import datetime, timedelta


FRENCH_WEEKDAYS = ('lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche')
FRENCH_MONTHS = (
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
)


def format_time(value):
    """Return a compact French time label from an HTML time input value."""
    if not value:
        return None

    if isinstance(value, datetime):
        parsed_time = value
    else:
        try:
            parsed_time = datetime.strptime(str(value)[:5], '%H:%M')
        except (TypeError, ValueError):
            return None

    return parsed_time.strftime('%Hh%M')


def format_french_date(value):
    if not value:
        return None

    return f'{FRENCH_WEEKDAYS[value.weekday()]} {value.day} {FRENCH_MONTHS[value.month - 1]} {value.year}'


def build_dashboard_context(event, reference_date=None):
    """Build the useful, client-facing summary displayed above the details."""
    reference_date = reference_date or datetime.now().date()
    details = event.event_details
    product = event.event_product
    option = event.event_option
    template = event.event_template

    preparation_steps = [bool(details.horaire), bool(template.text_template)]
    if product.need_design():
        preparation_steps.append(bool(template.url_modele))
    if product.need_music():
        preparation_steps.append(bool(template.url_music_360))
    if option.MurFloral:
        preparation_steps.append(bool(option.mur_floral_style))

    completed_steps = sum(preparation_steps)
    total_steps = len(preparation_steps)
    missing_steps = total_steps - completed_steps
    completion_percentage = round((completed_steps / total_steps) * 100) if total_steps else 100

    days_until_event = (details.date_evenement - reference_date).days
    if days_until_event < 0:
        event_countdown = 'Événement passé'
    elif days_until_event == 0:
        event_countdown = "C'est aujourd'hui"
    elif days_until_event == 1:
        event_countdown = 'Demain'
    else:
        event_countdown = f'Dans {days_until_event} jours'

    installation_time = None
    end_time = None
    if details.horaire:
        try:
            start_time = datetime.strptime(str(details.horaire)[:5], '%H:%M')
            installation_time = format_time(start_time - timedelta(hours=1))
            if option.duree:
                end_time = format_time(start_time + timedelta(hours=option.duree))
        except (TypeError, ValueError):
            pass

    return {
        'event': event,
        'completion_percentage': completion_percentage,
        'completed_steps': completed_steps,
        'total_steps': total_steps,
        'missing_steps': missing_steps,
        'event_countdown': event_countdown,
        'event_date_display': format_french_date(details.date_evenement),
        'installation_time': installation_time,
        'start_time': format_time(details.horaire),
        'end_time': end_time,
    }
