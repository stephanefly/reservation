from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from django.db import transaction
import logging
import json
from typing import Optional
from ..models import Event, EventPostPrestation
from app.module.mail.send_mail_event import send_mail_event
from app.module.mail.post_presta_publication import send_post_presta_publication_mail
from ..module.cloud.send_media import send_media_logic

# ------------------- Actions email / statut d’event -------------------

@require_POST
def relance_avis_client(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    send_mail_event(event, 'relance_avis')
    return redirect('tableau_de_bord')


@require_POST
def presta_fini(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.status = "Presta FINI"
    event.save(update_fields=["status"])
    return redirect('post_presta')


# ------------------- Endpoint générique feedback_* / sent -------------------

ALLOWED_FLAGS_UPDATE = {
    'feedback_message': 'feedback_message',
    'feedback_google': 'feedback_google',
    'feedback_posted': 'feedback_posted',
    'go_post_photo': 'go_post_photo',  # tri-état
    'post_photo': 'post_photo',
    'rush_collected': 'rush_collected',
    'go_montage': 'go_montage',
    'post_montage': 'post_montage',
    'sent': 'sent',
}

logger = logging.getLogger(__name__)

TRISTATE_FIELDS = {'go_post_photo'}               # ✅ valeurs texte
TRISTATE_ALLOWED = {'oui', 'non', 'à définir'}    # ✅ valeurs autorisées


@require_http_methods(["POST"])
@login_required
def update_post_presta_status(request, post_presta_id, action):
    field = ALLOWED_FLAGS_UPDATE.get(action)
    if not field:
        return JsonResponse({'ok': False, 'message': 'Action inconnue.'}, status=400)

    # ✅ Récup JSON
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        payload = {}

    raw_value = payload.get('value', None)

    # ✅ Cas particulier : go_post_photo → tri-état (pas de conversion en bool)
    if field in TRISTATE_FIELDS:
        if raw_value in (None, "", "null"):
            value = None
        else:
            value = str(raw_value)
            if value not in TRISTATE_ALLOWED:
                return JsonResponse({'ok': False, 'message': 'Valeur non autorisée.'}, status=400)

    else:
        # ✅ Garde ton comportement précédent pour TOUT LE RESTE :
        value = bool(raw_value)

    # Verrouiller le changement d'état : deux sauvegardes de « Oui »
    # ne doivent pas déclencher deux e-mails.
    with transaction.atomic():
        post_presta = get_object_or_404(
            EventPostPrestation.objects.select_for_update(), pk=post_presta_id
        )
        prev = getattr(post_presta, field, None)
        setattr(post_presta, field, value)

        if field == 'sent' and value:
            post_presta.date_media_sent = timezone.now()
            post_presta.save(update_fields=[field, 'date_media_sent'])
        else:
            post_presta.save(update_fields=[field])

    result = {
        'ok': True, 'action': action, 'field': field,
        'value': value, 'prev': prev,
    }
    if field == 'go_post_photo' and value == 'oui' and prev != 'oui':
        try:
            event = get_object_or_404(
                Event.objects.select_related('client', 'event_details', 'event_template'),
                event_post_presta=post_presta,
            )
            send_post_presta_publication_mail(event)
        except Exception:
            logger.exception("Notification publication non envoyée : post-presta %s", post_presta_id)
            # Le choix « Oui » reste enregistré ; le renvoi peut être tenté
            # via le bouton dédié une fois la cause corrigée.
            result['notification_sent'] = False
            result['notification_message'] = "Enregistré, mais le mail à Djordan n'a pas été envoyé."
        else:
            result['notification_sent'] = True
            result['notification_message'] = "Enregistré. Envoi accepté par IONOS pour Djordan."
    return JsonResponse(result)


@require_POST
@login_required
def resend_publication_notification(request, post_presta_id):
    """Renvoi explicite, uniquement pour les prestations marquées « Oui »."""
    post_presta = get_object_or_404(EventPostPrestation, pk=post_presta_id)
    if post_presta.go_post_photo != 'oui':
        return JsonResponse(
            {'ok': False, 'message': 'La prestation doit être marquée À poster : Oui.'},
            status=400,
        )
    try:
        event = get_object_or_404(
            Event.objects.select_related('client', 'event_details', 'event_template'),
            event_post_presta=post_presta,
        )
        send_post_presta_publication_mail(event)
    except Exception:
        logger.exception("Renvoi publication non envoyé : post-presta %s", post_presta_id)
        return JsonResponse(
            {'ok': False, 'message': "Mail non envoyé. Vérifier pCloud et le journal e-mail."},
            status=503,
        )
    return JsonResponse({
        'ok': True, 'message': 'Envoi accepté par IONOS pour Djordan.',
    })



# ------------------- Page principale -------------------

def post_presta(request):
    lst_post_event = (
        Event.objects
        .filter(signer_at__isnull=False, status__in=['Post Presta', 'Sent Media', 'Pending', 'Media KO'])
        .select_related(
            'client', 'event_details', 'event_product', 'event_option',
            'event_acompte', 'event_template', 'event_post_presta'
        )
        .prefetch_related('event_team_members')
        .order_by('event_details__date_evenement')
    )
    # Les compteurs concernent les dossiers effectivement affichés sur cette page.
    events = list(lst_post_event)
    post_stats = {
        'total': len(events),
        'media_pending': sum(
            not (event.event_post_presta and event.event_post_presta.collected and event.event_post_presta.sent)
            for event in events
        ),
        'payment_pending': sum(
            not (event.event_post_presta and event.event_post_presta.client_paid and event.event_post_presta.members_paid)
            for event in events
        ),
        'feedback_pending': sum(
            not (event.event_post_presta and (
                event.event_post_presta.feedback_message or event.event_post_presta.feedback_google
            ))
            for event in events
        ),
    }
    return render(request, 'app/backend/post_presta.html', {
        'lst_post_event': events,
        'post_stats': post_stats,
    })


# ------------------- Envoi médias -------------------

@require_POST
def send_media(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.status = "Pending"
    event.save(update_fields=["status"])
    return redirect('post_presta')



# ------------------- Helper DRY pour flags booléens -------------------

ALLOWED_FLAGS_SET = {
    "client_paid", "members_paid", "sold_ok",
    "feedback_message", "feedback_google", "feedback_posted",
    "collected", "sent"
}

def _set_flag(
    event_id: int,
    field: str,
    value: bool,
    membre_salary: Optional[int] = None,
    charge: Optional[int] = None
):
    """
    Met à jour un booléen de EventPostPrestation lié à Event(pk=event_id).
    extra_updates: dict de champs supplémentaires à mettre à jour (ex: {'membre_salary': 300})
    """
    event = get_object_or_404(Event, pk=event_id)
    epp = event.event_post_presta

    setattr(epp, field, bool(value))
    update_fields = [field]

    if membre_salary is not None:
        try:
            epp.membre_salary = int(membre_salary)
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "message": "membre_salary invalide."}, status=400)
        update_fields.append("membre_salary")

    # Met à jour charge si fourni
    if charge is not None:
        try:
            epp.charge = int(charge)
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "message": "charge invalide."}, status=400)
        update_fields.append("charge")

    epp.save(update_fields=update_fields)
    return JsonResponse({
        "ok": True,
        "field": field,
        "value": bool(value),
        "membre_salary": epp.membre_salary if membre_salary is not None else None,
        "charge": epp.charge if charge is not None else None
    })

# ------------------- Endpoints séparés (préférés) -------------------

@require_POST
def mark_client_paid(request, event_id):
    return _set_flag(event_id, "client_paid", True)

@require_POST
def mark_client_unpaid(request, event_id):
    return _set_flag(event_id, "client_paid", False)

@require_POST
def mark_members_paid(request, event_id):
    """
    Attend un JSON: {"salary_total": <int>}
    - Enregistre EventPostPrestation.membre_salary = salary_total
    - Passe members_paid=True
    """
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        payload = {}
    salary_total = int(payload.get('salary_total', 0))
    return _set_flag(event_id, "members_paid", True, membre_salary=salary_total)

@require_POST
def mark_members_unpaid(request, event_id):
    # On remet seulement le flag. (Si tu veux aussi remettre membre_salary=0, ajoute extra_updates={'membre_salary': 0})
    return _set_flag(event_id, "members_paid", False)

@require_POST
def mark_sold_ok(request, event_id):
    return _set_flag(event_id, "sold_ok", True)

@require_POST
def mark_sold_not_ok(request, event_id):
    return _set_flag(event_id, "sold_ok", False)

@require_POST
def mark_charge(request, event_id):
    try:
        charge_val = int(request.POST.get("charge", 0))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "message": "Valeur de charge invalide."}, status=400)

    return _set_flag(event_id, "members_paid", True, charge=charge_val)

@require_POST
def update_post_presta_commentaire(request, pk):
    """Met à jour le commentaire feedback d'un EventPostPrestation."""
    post_presta = get_object_or_404(EventPostPrestation, pk=pk)
    commentaire = request.POST.get("commentaire", "").strip()

    post_presta.commentaire = commentaire
    post_presta.save(update_fields=["commentaire"])

    return JsonResponse({"ok": True, "message": "Commentaire enregistré"})