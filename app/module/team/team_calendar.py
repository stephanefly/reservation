import json
from django.shortcuts import render
from app.models import Event  # adapte l'import si besoin


def get_stock_machines():
    """Retourne le stock global de machines."""
    return {
        "photobooth": 3,
        "miroirbooth": 2,
        "videobooth": 2,
        "voguebooth": 2,
        "ipadbooth": 1,
        "airbooth": 1,
    }


def get_stock_options():
    """Retourne le stock global de chaque option."""
    return {
        "Mur floral": 2,
        "Phonebooth": 2,
        "Livre d'or": 2,
        "Fond 360": 2,
        "Panneau de bienvenue": 2,
        "Photographe Voguebooth": 2,
        "Impression Voguebooth": 2,
        "Décor Voguebooth": 2,
        "Holo 3D": 2,
        "Panneau Fontaine": 2,
        "Vidéo livre d'or": 2,
        "Magnets": 2,
    }


def get_event_statuses():
    """Retourne les QuerySets des événements par statut."""
    return {
        "events_ok_data": Event.objects.filter(status="Acompte OK"),
        "events_presta_fini_data": Event.objects.filter(status="Presta FINI"),
        "events_post_presta_data": Event.objects.filter(status="Post Presta"),
    }


def build_event_data(event_statuses):
    """
    Applique transform_event_data à chaque QuerySet et
    retourne des listes Python prêtes à être utilisées.
    """
    return {
        key: transform_event_data(qs)
        for key, qs in event_statuses.items()
    }


def group_events_by_date(full_events, stock_machines, stock_options):
    """
    Regroupe tous les événements par date et calcule :
    - machines_used / machines_available
    - options_used / options_available
    Retourne un dict { "YYYY-MM-DD": { ... } }
    """
    grouped = {}

    for e in full_events:
        date_str = e["date"]

        # Initialisation pour cette date
        if date_str not in grouped:
            grouped[date_str] = {
                "events": [],
                "machines_used": {m: 0 for m in stock_machines},
                "options_used": {o: 0 for o in stock_options},
            }

        grouped[date_str]["events"].append(e)

        # Machines utilisées
        for machine_name, is_used in e["machines"].items():
            if is_used:
                grouped[date_str]["machines_used"][machine_name] += 1

        # Options utilisées : on cherche les noms dans la chaîne options
        options_string = (e.get("options") or "").lower()
        for opt_label in stock_options:
            if opt_label.lower() in options_string:
                grouped[date_str]["options_used"][opt_label] += 1

    # Calcul des disponibilités machines et options
    for date_str, info in grouped.items():
        info["machines_available"] = {
            m: stock_machines[m] - info["machines_used"][m]
            for m in stock_machines
        }
        info["options_available"] = {
            o: stock_options[o] - info["options_used"][o]
            for o in stock_options
        }

    return grouped


def calendar(request):
    # 1) Récupérer les événements bruts par statut
    event_statuses = get_event_statuses()

    # 2) Transformer en listes Python prêtes pour le JSON
    event_data = build_event_data(event_statuses)

    # 3) Récupérer les stocks
    stock_machines = get_stock_machines()
    stock_options = get_stock_options()

    # 4) Fusionner tous les événements pour le calcul par jour
    full_events = (
        event_data["events_ok_data"]
        + event_data["events_presta_fini_data"]
        + event_data["events_post_presta_data"]
    )

    # 5) Groupement par date + calcul des dispos machines/options
    grouped_by_date = group_events_by_date(
        full_events,
        stock_machines,
        stock_options
    )

    # 6) Envoi au template (ici seulement json.dumps pour JS)
    context = {
        # Pour colorer les jours dans le calendrier
        "events_ok_data": json.dumps(event_data["events_ok_data"]),
        "events_presta_fini_data": json.dumps(event_data["events_presta_fini_data"]),
        "events_post_presta_data": json.dumps(event_data["events_post_presta_data"]),

        # Pour afficher le détail du jour
        "calendar_data": json.dumps(grouped_by_date),
    }

    return render(request, "app/team/calendar.html", context)


def transform_event_data(events):
    data = []

    for event in events:
        products = getattr(event, "event_product", None)
        options = getattr(event, "event_option", None)

        machines = {
            "photobooth": bool(getattr(products, "photobooth", False)),
            "miroirbooth": bool(getattr(products, "miroirbooth", False)),
            "videobooth": bool(getattr(products, "videobooth", False)),
            "voguebooth": bool(getattr(products, "voguebooth", False)),
            "ipadbooth": bool(getattr(products, "ipadbooth", False)),
            "airbooth": bool(getattr(products, "airbooth", False)),
        }

        data.append({
            "date": event.event_details.date_evenement.strftime("%Y-%m-%d"),
            "title": event.client.nom,
            "product": products.get_selected_booths() if products else "",
            "ville": event.event_details.ville_evenement,
            "code_postal": event.event_details.code_postal_evenement,
            "machines": machines,
            "options": options.get_selected_options() if options else "",
        })

    return data
