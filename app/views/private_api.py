import os
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from app.models import Event

PARIS_TIME_ZONE = ZoneInfo("Europe/Paris")
CONFIRMED_STATUS_LIST = ["Acompte OK", "Presta FINI", "Post Presta", "Sent Media"]
DONE_STATUS_LIST = ["Presta FINI", "Post Presta", "Sent Media"]
PENDING_STATUS_LIST = ["Initied", "Calculed", "Sended", "Pending"]
PRODUCT_FIELDS = [
    "photobooth",
    "miroirbooth",
    "videobooth",
    "voguebooth",
    "ipadbooth",
    "airbooth",
]
BOOLEAN_OPTION_FIELDS = [
    "MurFloral",
    "Phonebooth",
    "LivreOr",
    "Fond360",
    "PanneauBienvenue",
    "PhotographeVoguebooth",
    "ImpressionVoguebooth",
    "DecorVoguebooth",
    "Holo3D",
    "PanneauFontaine",
    "VideoLivreOr",
]
QUANTITY_OPTION_FIELDS = [
    "magnets",
    "PorteCles",
    "MagnetsSimple",
]


def _now_paris():
    return timezone.now().astimezone(PARIS_TIME_ZONE)


def _today_paris():
    return _now_paris().date()


def _json_error(message, status=400):
    return JsonResponse(
        {
            "status": "error",
            "message": message,
        },
        status=status,
        json_dumps_params={"ensure_ascii": False},
    )


def _get_private_api_token():
    token = os.environ.get("PRIVATE_API_TOKEN")

    if token:
        return token

    return getattr(settings, "PRIVATE_API_TOKEN", None)


def _check_private_token(request):
    expected_token = _get_private_api_token()

    if not expected_token:
        return False, _json_error(
            "PRIVATE_API_TOKEN n'est pas configuré côté serveur.",
            status=500,
        )

    received_token = request.GET.get("token") or request.headers.get("X-Private-Api-Token")

    if received_token != expected_token:
        return False, _json_error("Token invalide ou manquant.", status=403)

    return True, None


def _safe_int(value):
    if value is None:
        return 0

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_text(value):
    if value is None:
        return ""

    return str(value)


def _selected_products(event_product):
    if event_product is None:
        return ""

    try:
        value = event_product.get_selected_booths()
    except Exception:
        value = ""

    return _safe_text(value)


def _selected_options(event_option):
    if event_option is None:
        return ""

    try:
        value = event_option.get_selected_options()
    except Exception:
        value = ""

    return _safe_text(value)


def _team_members(event):
    try:
        return [member.name for member in event.event_team_members.all()]
    except Exception:
        return []


def _base_event_queryset():
    return Event.objects.select_related(
        "client",
        "event_details",
        "event_product",
        "event_option",
        "event_acompte",
        "event_template",
        "event_post_presta",
    )


def _event_queryset_with_team():
    return _base_event_queryset().prefetch_related("event_team_members")


def _get_limit_and_days(request):
    limit = _safe_int(request.GET.get("limit")) or 20
    days = _safe_int(request.GET.get("days")) or 90

    if limit < 1:
        limit = 20
    if limit > 100:
        limit = 100
    if days < 1:
        days = 90
    if days > 730:
        days = 730

    return limit, days


def _parse_date_param(value, default_value):
    if not value:
        return default_value, None

    try:
        return date.fromisoformat(value), None
    except ValueError:
        return None, _json_error(
            "Format de date invalide. Utilise le format YYYY-MM-DD.",
            status=400,
        )


def _percent(part, total):
    if not total:
        return 0

    return round((part / total) * 100, 1)


def _average(total, count):
    if not count:
        return 0

    return round(total / count, 2)


def _new_period_stats():
    return {
        "events": 0,
        "events_confirmes": 0,
        "events_termines": 0,
        "ca_total_valide": 0,
        "ca_confirme": 0,
        "acompte_total_confirme": 0,
        "reste_a_payer_confirme": 0,
    }


def _add_count(counter, key, increment=1):
    key = _safe_text(key).strip()

    if not key:
        key = "Non renseigné"

    counter[key] = counter.get(key, 0) + increment


def _add_period_stats(period_stats, key, event, is_confirmed, is_done):
    if key not in period_stats:
        period_stats[key] = _new_period_stats()

    stats = period_stats[key]
    acompte = event.event_acompte
    prix_valided = _safe_int(event.prix_valided)

    stats["events"] += 1
    stats["ca_total_valide"] += prix_valided

    if is_confirmed:
        stats["events_confirmes"] += 1
        stats["ca_confirme"] += prix_valided
        stats["acompte_total_confirme"] += _safe_int(acompte.montant_acompte if acompte else 0)
        stats["reste_a_payer_confirme"] += _safe_int(acompte.montant_restant if acompte else 0)

    if is_done:
        stats["events_termines"] += 1


def _sorted_counter(counter):
    return dict(
        sorted(
            counter.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )


def _sorted_period_stats(period_stats):
    ordered_stats = {}

    for key in sorted(period_stats.keys()):
        stats = period_stats[key].copy()
        stats["taux_conversion_confirme_percent"] = _percent(
            stats["events_confirmes"],
            stats["events"],
        )
        stats["panier_moyen_confirme"] = _average(
            stats["ca_confirme"],
            stats["events_confirmes"],
        )
        ordered_stats[key] = stats

    return ordered_stats


def _event_to_dict(event):
    client = event.client
    details = event.event_details
    acompte = event.event_acompte
    template = event.event_template
    post_presta = event.event_post_presta

    return {
        "id": event.id,
        "num_devis": event.num_devis,
        "status": _safe_text(event.status),
        "client": _safe_text(client.nom if client else ""),
        "date_evenement": details.date_evenement.isoformat() if details and details.date_evenement else None,
        "horaire": _safe_text(details.horaire if details else ""),
        "adresse": _safe_text(details.adresse_evenement if details else ""),
        "ville": _safe_text(details.ville_evenement if details else ""),
        "code_postal": details.code_postal_evenement if details else None,
        "commentaire_interne": _safe_text(details.comment if details else ""),
        "commentaire_client": _safe_text(details.comment_client if details else ""),
        "prestations": _selected_products(event.event_product),
        "options": _selected_options(event.event_option),
        "prix_brut": _safe_int(event.prix_brut),
        "prix_proposed": _safe_int(event.prix_proposed),
        "prix_valided": _safe_int(event.prix_valided),
        "acompte": _safe_int(acompte.montant_acompte if acompte else 0),
        "reste_a_payer": _safe_int(acompte.montant_restant if acompte else 0),
        "mode_paiement_acompte": _safe_text(acompte.mode_payement if acompte else ""),
        "date_paiement_acompte": acompte.date_payement.isoformat() if acompte and acompte.date_payement else None,
        "template_ok": bool(template.statut) if template else False,
        "template_directory": _safe_text(template.directory_name if template else ""),
        "post_media_sent": bool(post_presta.sent) if post_presta else False,
        "post_client_paid": bool(post_presta.client_paid) if post_presta else False,
        "post_members_paid": bool(post_presta.members_paid) if post_presta else False,
        "equipe": _team_members(event),
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "signer_at": event.signer_at.isoformat() if event.signer_at else None,
    }


@require_GET
def private_api_ping(request):
    is_allowed, error_response = _check_private_token(request)
    if not is_allowed:
        return error_response

    now_paris = _now_paris()

    return JsonResponse(
        {
            "status": "ok",
            "message": "API privée active",
            "server_date": now_paris.isoformat(),
            "timezone": "Europe/Paris",
        },
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def private_api_crm_summary(request):
    is_allowed, error_response = _check_private_token(request)
    if not is_allowed:
        return error_response

    today = _today_paris()
    month_start = today.replace(day=1)

    events = _base_event_queryset()
    confirmed_events = events.filter(status__in=CONFIRMED_STATUS_LIST)

    total_events = events.count()
    upcoming_events = events.filter(event_details__date_evenement__gte=today).count()
    upcoming_confirmed_events = confirmed_events.filter(event_details__date_evenement__gte=today).count()
    month_events = events.filter(event_details__date_evenement__gte=month_start).count()
    month_confirmed_events = confirmed_events.filter(event_details__date_evenement__gte=month_start).count()
    done_events = events.filter(status__in=DONE_STATUS_LIST).count()
    pending_events = events.filter(status__in=PENDING_STATUS_LIST).count()

    ca_total_valide = events.aggregate(total=Sum("prix_valided")).get("total") or 0
    ca_confirme = confirmed_events.aggregate(total=Sum("prix_valided")).get("total") or 0
    ca_mois = events.filter(event_details__date_evenement__gte=month_start).aggregate(total=Sum("prix_valided")).get("total") or 0
    ca_mois_confirme = confirmed_events.filter(event_details__date_evenement__gte=month_start).aggregate(total=Sum("prix_valided")).get("total") or 0
    reste_total = confirmed_events.aggregate(total=Sum("event_acompte__montant_restant")).get("total") or 0
    impayes_count = confirmed_events.filter(event_acompte__montant_restant__gt=0).count()

    media_non_envoyes = confirmed_events.filter(
        status__in=["Presta FINI", "Post Presta"],
        event_post_presta__sent=False,
    ).count()

    return JsonResponse(
        {
            "status": "ok",
            "date_reference": today.isoformat(),
            "timezone": "Europe/Paris",
            "total_events": total_events,
            "events_a_venir": upcoming_events,
            "events_confirmes_a_venir": upcoming_confirmed_events,
            "events_ce_mois_et_apres": month_events,
            "events_confirmes_ce_mois_et_apres": month_confirmed_events,
            "events_termines": done_events,
            "events_en_attente": pending_events,
            "ca_total_valide": ca_total_valide,
            "ca_total_confirme": ca_confirme,
            "ca_mois_et_apres": ca_mois,
            "ca_mois_confirme_et_apres": ca_mois_confirme,
            "reste_a_payer_total_confirme": reste_total,
            "impayes_confirmes_count": impayes_count,
            "media_non_envoyes_count": media_non_envoyes,
        },
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def private_api_stats_since_2025(request):
    is_allowed, error_response = _check_private_token(request)
    if not is_allowed:
        return error_response

    today = _today_paris()
    start_date, error_response = _parse_date_param(
        request.GET.get("start"),
        date(2025, 1, 1),
    )
    if error_response:
        return error_response

    end_date, error_response = _parse_date_param(request.GET.get("end"), None)
    if error_response:
        return error_response

    events = _event_queryset_with_team().filter(
        event_details__date_evenement__gte=start_date,
    )

    if end_date:
        events = events.filter(event_details__date_evenement__lte=end_date)

    events = events.order_by("event_details__date_evenement", "event_details__horaire")

    total_events = 0
    confirmed_events = 0
    done_events = 0
    pending_events = 0
    ca_total_valide = 0
    ca_confirme = 0
    acompte_total_confirme = 0
    reste_a_payer_total_confirme = 0
    impayes_confirmes_count = 0
    cout_post_presta_total = 0

    by_year = {}
    by_month = {}
    by_status = {}
    by_prestation = {}
    by_option = {}
    by_option_quantity = {}
    by_source = {}
    by_city = {}
    by_team_member = {}

    for event in events:
        details = event.event_details
        client = event.client
        product = event.event_product
        option = event.event_option
        acompte = event.event_acompte
        post_presta = event.event_post_presta

        event_date = details.date_evenement
        status = _safe_text(event.status)
        is_confirmed = status in CONFIRMED_STATUS_LIST
        is_done = status in DONE_STATUS_LIST
        is_pending = status in PENDING_STATUS_LIST

        prix_valided = _safe_int(event.prix_valided)
        acompte_amount = _safe_int(acompte.montant_acompte if acompte else 0)
        reste_amount = _safe_int(acompte.montant_restant if acompte else 0)

        total_events += 1
        ca_total_valide += prix_valided

        if is_confirmed:
            confirmed_events += 1
            ca_confirme += prix_valided
            acompte_total_confirme += acompte_amount
            reste_a_payer_total_confirme += reste_amount

            if reste_amount > 0:
                impayes_confirmes_count += 1

        if is_done:
            done_events += 1

        if is_pending:
            pending_events += 1

        if post_presta:
            cout_post_presta_total += _safe_int(post_presta.charge)
            cout_post_presta_total += _safe_int(post_presta.membre_salary)

        _add_count(by_status, status)
        _add_count(by_source, client.how_find if client else "")
        _add_count(by_city, details.ville_evenement if details else "")

        if product:
            for field in PRODUCT_FIELDS:
                if getattr(product, field, False):
                    _add_count(by_prestation, field)

        if option:
            for field in BOOLEAN_OPTION_FIELDS:
                if getattr(option, field, False):
                    _add_count(by_option, field)

            for field in QUANTITY_OPTION_FIELDS:
                quantity = _safe_int(getattr(option, field, 0))
                if quantity > 0:
                    _add_count(by_option, field)
                    by_option_quantity[field] = by_option_quantity.get(field, 0) + quantity

        for member_name in _team_members(event):
            _add_count(by_team_member, member_name)

        _add_period_stats(
            by_year,
            str(event_date.year),
            event,
            is_confirmed,
            is_done,
        )
        _add_period_stats(
            by_month,
            event_date.strftime("%Y-%m"),
            event,
            is_confirmed,
            is_done,
        )

    marge_brute_estimee = ca_confirme - cout_post_presta_total

    return JsonResponse(
        {
            "status": "ok",
            "date_reference": today.isoformat(),
            "timezone": "Europe/Paris",
            "filters": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat() if end_date else None,
                "confirmed_statuses": CONFIRMED_STATUS_LIST,
            },
            "global": {
                "events": total_events,
                "events_confirmes": confirmed_events,
                "events_termines": done_events,
                "events_en_attente": pending_events,
                "taux_conversion_confirme_percent": _percent(confirmed_events, total_events),
                "ca_total_valide": ca_total_valide,
                "ca_total_confirme": ca_confirme,
                "panier_moyen_confirme": _average(ca_confirme, confirmed_events),
                "acompte_total_confirme": acompte_total_confirme,
                "reste_a_payer_total_confirme": reste_a_payer_total_confirme,
                "impayes_confirmes_count": impayes_confirmes_count,
                "cout_post_presta_total": cout_post_presta_total,
                "marge_brute_estimee": marge_brute_estimee,
            },
            "by_year": _sorted_period_stats(by_year),
            "by_month": _sorted_period_stats(by_month),
            "by_status": _sorted_counter(by_status),
            "by_prestation": _sorted_counter(by_prestation),
            "by_option": _sorted_counter(by_option),
            "by_option_quantity": _sorted_counter(by_option_quantity),
            "by_source": _sorted_counter(by_source),
            "top_villes": dict(list(_sorted_counter(by_city).items())[:20]),
            "by_team_member": _sorted_counter(by_team_member),
        },
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def private_api_upcoming_events(request):
    is_allowed, error_response = _check_private_token(request)
    if not is_allowed:
        return error_response

    today = _today_paris()
    limit, days = _get_limit_and_days(request)
    date_max = today + timedelta(days=days)

    events = (
        _event_queryset_with_team()
        .filter(
            event_details__date_evenement__gte=today,
            event_details__date_evenement__lte=date_max,
        )
        .order_by("event_details__date_evenement", "event_details__horaire")[:limit]
    )

    event_list = [_event_to_dict(event) for event in events]

    return JsonResponse(
        {
            "status": "ok",
            "date_reference": today.isoformat(),
            "timezone": "Europe/Paris",
            "days": days,
            "limit": limit,
            "count": len(event_list),
            "events": event_list,
        },
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def private_api_confirmed_events(request):
    is_allowed, error_response = _check_private_token(request)
    if not is_allowed:
        return error_response

    today = _today_paris()
    limit, days = _get_limit_and_days(request)
    date_max = today + timedelta(days=days)

    events = (
        _event_queryset_with_team()
        .filter(
            status__in=CONFIRMED_STATUS_LIST,
            event_details__date_evenement__gte=today,
            event_details__date_evenement__lte=date_max,
        )
        .order_by("event_details__date_evenement", "event_details__horaire")[:limit]
    )

    event_list = [_event_to_dict(event) for event in events]

    return JsonResponse(
        {
            "status": "ok",
            "date_reference": today.isoformat(),
            "timezone": "Europe/Paris",
            "statuses": CONFIRMED_STATUS_LIST,
            "days": days,
            "limit": limit,
            "count": len(event_list),
            "events": event_list,
        },
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def private_api_event_detail(request, event_id):
    is_allowed, error_response = _check_private_token(request)
    if not is_allowed:
        return error_response

    try:
        event = _event_queryset_with_team().get(id=event_id)
    except Event.DoesNotExist:
        return _json_error("Événement introuvable.", status=404)

    return JsonResponse(
        {
            "status": "ok",
            "event": _event_to_dict(event),
        },
        json_dumps_params={"ensure_ascii": False},
    )
