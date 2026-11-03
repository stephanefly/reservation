"""Read-only CRM resources. Field lists deliberately exclude access credentials."""
from datetime import date, datetime, time, timedelta
from functools import wraps

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from app import models
from app.views.private_api import PARIS_TIME_ZONE, _check_private_token


# Explicit allowlists: adding a model field never exposes it automatically.
RESOURCES = {
    "email-deliveries": (models.EmailTracking, "event_traced status_devis sent_at opened opened_at message_id recipient mail_type opening_tracked accepted_at delivery_status smtp_code diagnostic copy_refused feedback_at"),
    "email-mailbox-checks": (models.EmailMailboxCheck, "key checked_at success scanned matched unmatched skipped diagnostic"),
    "clients": (models.Client, "nom mail numero_telephone how_find raison_sociale nb_relance_devis nb_relance_avis autorisation_mail mail_sondage"),
    "events": (models.Event, "id_card num_devis client_id event_details_id event_product_id event_option_id event_acompte_id event_template_id event_post_presta_id prix_brut reduc_product reduc_all prix_proposed prix_valided created_at signer_at status history_status"),
    "event-details": (models.EventDetails, "date_evenement adresse_evenement ville_evenement code_postal_evenement comment comment_client horaire"),
    "products": (models.EventProduct, "photobooth miroirbooth videobooth voguebooth ipadbooth airbooth"),
    "options": (models.EventOption, "MurFloral mur_floral_style MurFloral_reduc_prix Phonebooth Phonebooth_reduc_prix LivreOr LivreOr_reduc_prix Fond360 Fond360_reduc_prix PanneauBienvenue PanneauBienvenue_reduc_prix PhotographeVoguebooth PhotographeVoguebooth_reduc_prix ImpressionVoguebooth ImpressionVoguebooth_reduc_prix DecorVoguebooth DecorVoguebooth_reduc_prix Holo3D Holo3D_reduc_prix PanneauFontaine PanneauFontaine_reduc_prix VideoLivreOr VideoLivreOr_reduc_prix panneaux_xxl panneaux_forfait panneaux_remise magnets magnets_reduc_prix PorteCles PorteCles_reduc_prix MagnetsSimple MagnetsSimple_reduc_prix livraison duree"),
    "payments": (models.EventAcompte, "montant_acompte mode_payement date_payement montant_restant"),
    "templates": (models.EventTemplate, "url_modele text_template statut directory_name image_name num_template url_pcloud_template_folder url_music_360"),
    "post-prestation": (models.EventPostPrestation, "feedback_message feedback_google feedback_posted collected go_post_photo post_photo rush_collected sent date_media_sent link_media_shared members_paid client_paid sold_ok charge membre_salary go_montage post_montage commentaire"),
    "team": (models.TeamMember, "name email phone"),
    "cost-names": (models.NameCost, "name"),
    "costs": (models.Cost, "name_cost_id type_cost price_cost created_at frecency"),
    "email-tracking": (models.EmailTracking, "event_traced status_devis sent_at opened opened_at message_id recipient mail_type opening_tracked accepted_at delivery_status smtp_code diagnostic copy_refused feedback_at"),
    "follow-ups": (models.EventRelance, "event_id membre date_relance commentaire qualification"),
}


def private_read(view):
    @require_GET
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        allowed, error = _check_private_token(request)
        if not allowed:
            response = error
        else:
            try:
                response = view(request, *args, **kwargs)
            except ValueError as exc:
                response = JsonResponse({"status": "error", "message": str(exc)}, status=400)
        response["Cache-Control"] = "no-store"
        return response
    return wrapped


def record(obj, resource):
    if obj is None:
        return None
    fields = RESOURCES[resource][1].split()
    data = {field: getattr(obj, field) for field in ["id"] + fields}
    if resource == "events":
        data["team_ids"] = [member.id for member in obj.event_team_members.all()]
    return data


def integer(request, key, default, minimum=1, maximum=None):
    try:
        value = int(request.GET.get(key, default))
    except (ValueError, TypeError):
        raise ValueError(f"{key} doit être un entier.")
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"Valeur hors limites pour {key}.")
    return value


def filter_dates(request, queryset, field, with_time=False):
    bounds = []
    for key in ("start_date", "end_date"):
        raw = request.GET.get(key)
        try:
            value = date.fromisoformat(raw) if raw else None
        except ValueError:
            raise ValueError(f"{key} doit être au format AAAA-MM-JJ.")
        bounds.append(value)
    start, end = bounds
    if start and end and start > end:
        raise ValueError("start_date doit précéder end_date.")
    if with_time:
        if start:
            start = timezone.make_aware(datetime.combine(start, time.min), PARIS_TIME_ZONE)
        if end:
            end = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min), PARIS_TIME_ZONE)
    if start:
        queryset = queryset.filter(**{field + "__gte": start})
    if end:
        queryset = queryset.filter(**{field + ("__lt" if with_time else "__lte"): end})
    return queryset


def filtered(request, resource):
    queryset = RESOURCES[resource][0].objects.all()
    if resource == "events":
        queryset = queryset.prefetch_related("event_team_members")
        queryset = filter_dates(request, queryset, "event_details__date_evenement")
        if request.GET.get("status"):
            queryset = queryset.filter(status=request.GET["status"])
        if request.GET.get("client_id"):
            queryset = queryset.filter(client_id=integer(request, "client_id", 0))
        if request.GET.get("q"):
            term = request.GET["q"]
            queryset = queryset.filter(Q(client__nom__icontains=term) | Q(client__mail__icontains=term) | Q(event_details__ville_evenement__icontains=term))
    if resource in ("email-tracking", "follow-ups"):
        if request.GET.get("event_id"):
            field = "event_traced" if resource == "email-tracking" else "event_id"
            queryset = queryset.filter(**{field: integer(request, "event_id", 0)})
        date_field = "sent_at" if resource == "email-tracking" else "date_relance"
        queryset = filter_dates(request, queryset, date_field, with_time=True)
    if resource == "email-tracking":
        if request.GET.get("status"):
            queryset = queryset.filter(status_devis=request.GET["status"])
        if "opened" in request.GET:
            raw = request.GET["opened"].lower()
            if raw not in ("true", "false", "1", "0"):
                raise ValueError("opened doit valoir true ou false.")
            queryset = queryset.filter(opened=raw in ("true", "1"))
    if resource == "clients" and request.GET.get("q"):
        term = request.GET["q"]
        queryset = queryset.filter(Q(nom__icontains=term) | Q(mail__icontains=term) | Q(numero_telephone__icontains=term))
    if resource == "costs":
        queryset = filter_dates(request, queryset, "created_at", with_time=True)
    if resource == "email-deliveries":
        queryset = filter_dates(request, queryset, "sent_at", with_time=True)
        if request.GET.get("event_id"):
            queryset = queryset.filter(event_traced=integer(request, "event_id", 0))
        if request.GET.get("status"):
            queryset = queryset.filter(delivery_status=request.GET["status"])
    return queryset


@private_read
def private_api_schema(request):
    return JsonResponse({
        "status": "ok", "version": 2, "read_only": True,
        "resources": {name: ["id"] + fields.split() + (["team_ids"] if name == "events" else []) for name, (_, fields) in RESOURCES.items()},
        "pagination": {"page": 1, "page_size": 50, "max_page_size": 100},
        "excluded": ["event_token", "code_espace_client", "tracking_uuid", "configuration secrets"],
    })


@private_read
def private_api_resource(request, resource, record_id=None):
    if resource not in RESOURCES:
        return JsonResponse({"status": "error", "message": "Ressource introuvable."}, status=404)
    queryset = filtered(request, resource)
    if record_id is not None:
        obj = queryset.filter(pk=record_id).first()
        if obj is None:
            return JsonResponse({"status": "error", "message": "Objet introuvable."}, status=404)
        return JsonResponse({"status": "ok", "resource": resource, "item": record(obj, resource)})
    page = integer(request, "page", 1)
    size = integer(request, "page_size", 50, maximum=100)
    total = queryset.count()
    offset = (page - 1) * size
    items = [record(obj, resource) for obj in queryset.order_by("id")[offset:offset + size]]
    return JsonResponse({"status": "ok", "resource": resource, "page": page, "page_size": size, "total": total, "has_next": offset + size < total, "items": items})


def opening_queryset(queryset):
    return queryset.filter(opening_tracked=True).exclude(delivery_status__in=["preparing", "error", "refused"])


def email_counts(queryset):
    queryset = opening_queryset(queryset)
    result = queryset.aggregate(tracked=Count("id"), opened=Count("id", filter=Q(opened=True)))
    return rate(result)


def rate(result):
    total, opened = result["tracked"], result["opened"]
    return {**result, "not_opened": total - opened, "opening_rate_percent": round(100 * opened / total, 2) if total else None}


def email_report(request):
    queryset = opening_queryset(filtered(request, "email-tracking"))
    # The rate denominator must include unopened records too.
    if "opened" in request.GET:
        raise ValueError("Le filtre opened est réservé à la liste, pas aux statistiques.")
    by_status = queryset.values("status_devis").annotate(tracked=Count("id"), opened=Count("id", filter=Q(opened=True))).order_by("status_devis")
    monthly = queryset.annotate(month=TruncMonth("sent_at", tzinfo=PARIS_TIME_ZONE)).values("month").annotate(tracked=Count("id"), opened=Count("id", filter=Q(opened=True))).order_by("month")
    return {
        "status": "ok", "timezone": "Europe/Paris", "totals": email_counts(queryset),
        "by_status": [rate(row) for row in by_status],
        "by_month": [rate(row) for row in monthly],
        "definition": "Une ouverture au moins par enregistrement de suivi, regroupé selon la date d'envoi.",
        "limitations": "Suivi par image des devis et relances : chargement automatique ou images bloquées possibles. Un suivi est créé avant l'envoi SMTP : il ne prouve pas la livraison. opened_at est le dernier chargement enregistré. Les réponses client ne sont pas détectées.",
    }


@private_read
def private_api_email_stats(request):
    return JsonResponse(email_report(request))


def event_data(event):
    data = {"event": record(event, "events")}
    for attribute, resource in (
        ("client", "clients"), ("event_details", "event-details"),
        ("event_product", "products"), ("event_option", "options"),
        ("event_acompte", "payments"), ("event_template", "templates"),
        ("event_post_presta", "post-prestation"),
    ):
        data[attribute] = record(getattr(event, attribute), resource)
    data["team"] = [record(member, "team") for member in event.event_team_members.all()]
    data["email_stats"] = email_counts(models.EmailTracking.objects.filter(event_traced=event.id))
    data["email_tracking_url"] = f"/api/private/resources/email-tracking/?event_id={event.id}"
    data["follow_ups_url"] = f"/api/private/resources/follow-ups/?event_id={event.id}"
    return data
