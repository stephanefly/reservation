from datetime import timedelta

from django.conf import settings
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from app.models import Event


def _json_error(message, status=400):
    return JsonResponse(
        {
            "status": "error",
            "message": message,
        },
        status=status,
        json_dumps_params={"ensure_ascii": False},
    )


def _check_private_token(request):
    expected_token = getattr(settings, "PRIVATE_API_TOKEN", None)

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

    return JsonResponse(
        {
            "status": "ok",
            "message": "API privée active",
            "server_date": timezone.now().isoformat(),
        },
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def private_api_crm_summary(request):
    is_allowed, error_response = _check_private_token(request)
    if not is_allowed:
        return error_response

    today = timezone.localdate()
    month_start = today.replace(day=1)

    events = Event.objects.select_related(
        "client",
        "event_details",
        "event_product",
        "event_option",
        "event_acompte",
        "event_template",
        "event_post_presta",
    )

    total_events = events.count()
    upcoming_events = events.filter(event_details__date_evenement__gte=today).count()
    month_events = events.filter(event_details__date_evenement__gte=month_start).count()
    done_events = events.filter(status__in=["Presta FINI", "Post Presta", "Sent Media"]).count()
    pending_events = events.filter(status__in=["Initied", "Calculed", "Sended", "Pending"]).count()

    ca_total_valide = events.aggregate(total=Sum("prix_valided")).get("total") or 0
    ca_mois = events.filter(event_details__date_evenement__gte=month_start).aggregate(total=Sum("prix_valided")).get("total") or 0
    reste_total = events.aggregate(total=Sum("event_acompte__montant_restant")).get("total") or 0
    impayes_count = events.filter(event_acompte__montant_restant__gt=0).count()

    media_non_envoyes = events.filter(
        status__in=["Presta FINI", "Post Presta"],
        event_post_presta__sent=False,
    ).count()

    return JsonResponse(
        {
            "status": "ok",
            "date_reference": today.isoformat(),
            "total_events": total_events,
            "events_a_venir": upcoming_events,
            "events_ce_mois_et_apres": month_events,
            "events_termines": done_events,
            "events_en_attente": pending_events,
            "ca_total_valide": ca_total_valide,
            "ca_mois_et_apres": ca_mois,
            "reste_a_payer_total": reste_total,
            "impayes_count": impayes_count,
            "media_non_envoyes_count": media_non_envoyes,
        },
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def private_api_upcoming_events(request):
    is_allowed, error_response = _check_private_token(request)
    if not is_allowed:
        return error_response

    today = timezone.localdate()
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

    date_max = today + timedelta(days=days)

    events = (
        Event.objects.select_related(
            "client",
            "event_details",
            "event_product",
            "event_option",
            "event_acompte",
            "event_template",
            "event_post_presta",
        )
        .prefetch_related("event_team_members")
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
        event = (
            Event.objects.select_related(
                "client",
                "event_details",
                "event_product",
                "event_option",
                "event_acompte",
                "event_template",
                "event_post_presta",
            )
            .prefetch_related("event_team_members")
            .get(id=event_id)
        )
    except Event.DoesNotExist:
        return _json_error("Événement introuvable.", status=404)

    return JsonResponse(
        {
            "status": "ok",
            "event": _event_to_dict(event),
        },
        json_dumps_params={"ensure_ascii": False},
    )
