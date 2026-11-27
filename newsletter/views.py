import base64
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.contrib.admin.views.decorators import staff_member_required
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CampaignForm, CampaignTestForm, ConfigurationForm, TemplateForm
from .models import Attribution, Campaign, Configuration, Delivery, Template, TestAttempt, Unsubscribe
from .services import CLICK_SALT, build_message, eligible, has_capacity, http_url, smtp_settings

staff = staff_member_required(login_url="login")
PIXEL = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


def metrics(deliveries):
    data = deliveries.aggregate(
        sent=Count("sent_at"), opened=Count("opened_at"), clicked=Count("clicked_at"),
    )
    for kind in ("opened", "clicked"):
        data[kind + "_rate"] = round(100 * data[kind] / data["sent"], 1) if data["sent"] else 0
    business = Attribution.objects.filter(delivery__in=deliveries).aggregate(
        requests=Count("pk"),
        quotes=Count("pk", filter=Q(event__prix_proposed__isnull=False) |
                     Q(event__prix_valided__isnull=False)),
        revenue=Sum("event__prix_valided", filter=Q(event__signer_at__isnull=False), default=0),
    )
    return {**data, **business, "unsubscribed": Unsubscribe.objects.filter(delivery__in=deliveries).count()}


@staff
def dashboard(request):
    sent = Campaign.objects.filter(deliveries__sent_at__isnull=False).distinct().count()
    return render(request, "newsletter/dashboard.html", {
        "eligible": len(eligible()), "sent_campaigns": sent,
        "stats": metrics(Delivery.objects.all()),
    })


@staff
def campaigns(request):
    page = Paginator(Campaign.objects.order_by("-pk"), 50).get_page(request.GET.get("page"))
    return render(request, "newsletter/campaigns.html", {"page_obj": page})


@staff
@require_http_methods(["GET", "POST"])
def edit(request, pk=None):
    with timezone.override(ZoneInfo("Europe/Paris")):
        if request.method == "POST":
            return save_campaign(request, pk)
        campaign = get_object_or_404(Campaign, pk=pk) if pk else None
        if campaign and campaign.status != Campaign.Status.DRAFT:
            return redirect("newsletter:detail", pk=pk)
        form = CampaignForm(instance=campaign)
        feedback = request.session.pop(f"newsletter_editor_{pk}", {})
        return render_editor(request, form, campaign, feedback)


def render_editor(request, form, campaign, feedback=None):
    audience = form["audience"].value()
    return render(request, "newsletter/editor.html", {
        "form": form,
        "campaign": campaign,
        "count": len(eligible(audience)) if audience in Campaign.Audience.values else None,
        **(feedback or {}),
    })


def save_campaign(request, pk):
    with transaction.atomic():
        campaign = get_object_or_404(Campaign.objects.select_for_update(), pk=pk) if pk else None
        if campaign and campaign.status != Campaign.Status.DRAFT:
            return redirect("newsletter:detail", pk=pk)
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if not form.is_valid():
            # Les champs fichier sont vidés par le navigateur après une soumission.
            if form.cleaned_data.get("html"):
                form.data = form.data.copy()
                form.data["html"] = form.cleaned_data["html"]
            return render_editor(request, form, campaign)
        campaign = form.save()
        action = request.POST.get("action")
        if action == "confirm" and pk:
            error = queue_campaign(campaign, request.POST.get("confirm") == "yes")
            if not error:
                return redirect("newsletter:detail", pk=campaign.pk)
            feedback = {"error": error}
        else:
            feedback = {"notice": "Brouillon enregistré."}

    if action == "test":
        email = request.POST.get("email", "").strip()
        feedback = {"test_email": email}
        send_editor_test(campaign, email, feedback)

    request.session[f"newsletter_editor_{campaign.pk}"] = feedback
    return redirect("newsletter:edit", pk=campaign.pk)


def send_editor_test(campaign, email, feedback):
    try:
        validate_email(email)
    except ValidationError:
        feedback["error"] = "Indiquez une adresse de test valide. Le brouillon a été enregistré."
        return
    if not campaign.subject or not campaign.html:
        feedback["error"] = "Renseignez l’objet et le HTML avant d’envoyer un test."
        return
    send_test(campaign, email, feedback)


@staff
@require_http_methods(["GET", "POST"])
def legacy_editor(request, pk, step=None):
    return redirect("newsletter:edit", pk=pk)


@staff
@require_http_methods(["GET", "POST"])
def smtp_test(request):
    recipient = "faure_stephane@hotmail.fr"
    form = CampaignTestForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        campaign = form.cleaned_data["campaign"] or Campaign(
            subject="Vérification SMTP MySelfieBooth",
            html="<p>Cet email vérifie le SMTP marketing du CRM MySelfieBooth.</p>",
        )
        result = {}
        send_test(campaign, recipient, result)
        request.session["newsletter_smtp_test_result"] = result
        return redirect("newsletter:test")
    return render(request, "newsletter/test.html", {
        "form": form, "recipient": recipient,
        **request.session.pop("newsletter_smtp_test_result", {}),
    })


def send_test(campaign, email, context):
    with transaction.atomic():
        config = Configuration.objects.select_for_update().filter(
            pk=1, enabled=True, sender__gt=""
        ).first()
        if not config:
            context["error"] = "Activez les envois et renseignez l’adresse d’expédition."
            return
        try:
            smtp = smtp_settings()
        except ValueError as exc:
            context["error"] = str(exc)
            return
        now = timezone.now()
        if not has_capacity(config, now):
            context["error"] = "La limite horaire d’envoi est atteinte."
            return
        TestAttempt.objects.filter(attempted_at__lte=now - timedelta(hours=1)).delete()
        TestAttempt.objects.create(attempted_at=now)
    try:
        sent = build_message(campaign, email, config, smtp).send()
    except Exception as exc:
        context["error"] = f"Échec de l’envoi de test ({type(exc).__name__})."
    else:
        context["notice" if sent == 1 else "error"] = (
            "Email de test accepté par le SMTP." if sent == 1 else "Aucun email accepté par le SMTP."
        )


def queue_campaign(campaign, confirmed):
    if not confirmed:
        return "Cochez la confirmation pour mettre la campagne en file."
    if not (campaign.name and campaign.subject and campaign.html):
        return "Renseignez le nom, l’objet et le HTML avant de confirmer l’envoi."
    now = timezone.now()
    if campaign.scheduled_at and campaign.scheduled_at <= now:
        return "La date prévue est passée. Modifiez la programmation."
    emails = eligible(campaign.audience)
    if not emails:
        return "Aucun destinataire éligible."
    if not Configuration.objects.filter(pk=1, enabled=True, sender__gt="").exists():
        return "Activez les envois et renseignez l’adresse d’expédition."
    try:
        smtp_settings()
    except ValueError as exc:
        return str(exc)

    Delivery.objects.bulk_create([
        Delivery(campaign=campaign, email=email) for email in sorted(emails)
    ], batch_size=500)
    campaign.confirmed_at = now
    campaign.scheduled_at = campaign.scheduled_at or now
    campaign.status = Campaign.Status.QUEUED
    campaign.save(update_fields=["confirmed_at", "scheduled_at", "status"])
    return None


@staff
def preview(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    response = HttpResponse(campaign.html)
    response["Content-Security-Policy"] = (
        "sandbox; default-src 'none'; img-src https: data:; style-src 'unsafe-inline'; "
        "base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
    )
    response["X-Frame-Options"] = "SAMEORIGIN"
    response["Referrer-Policy"] = "no-referrer"
    return response


@staff
@require_http_methods(["GET", "POST"])
def templates(request, pk=None):
    template = get_object_or_404(Template, pk=pk) if pk else None
    form = TemplateForm(request.POST or None, request.FILES, instance=template)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("newsletter:templates")
    return render(request, "newsletter/templates.html", {
        "templates": Template.objects.order_by("name", "pk"), "form": form,
    })


@staff
@require_POST
def duplicate(request, pk):
    source = get_object_or_404(Template, pk=pk)
    copy = Template.objects.create(name=source.name[:142] + " (copie)", html=source.html)
    return redirect("newsletter:template", pk=copy.pk)


@staff
def history(request):
    page = Paginator(Campaign.objects.exclude(status=Campaign.Status.DRAFT).order_by(
        "-confirmed_at", "-pk"
    ), 50).get_page(request.GET.get("page"))
    return render(request, "newsletter/campaigns.html", {"page_obj": page, "history": True})


@staff
def detail(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if campaign.status == Campaign.Status.DRAFT:
        return redirect("newsletter:edit", pk=pk)
    deliveries = campaign.deliveries.all()
    status = Delivery.Status
    delivery_summary = deliveries.aggregate(
        recipients=Count("pk"),
        attempted=Count("attempted_at"),
        pending=Count("pk", filter=Q(status__in=[status.PENDING, status.SENDING])),
        failed=Count("pk", filter=Q(status=status.FAILED)),
        uncertain=Count("pk", filter=Q(status=status.UNCERTAIN)),
        excluded=Count("pk", filter=Q(status=status.EXCLUDED)),
    )
    return render(request, "newsletter/detail.html", {
        "campaign": campaign, "stats": metrics(deliveries), "delivery_summary": delivery_summary,
    })


@staff
@require_http_methods(["GET", "POST"])
def configuration(request):
    config = Configuration.objects.filter(pk=1).first() or Configuration(pk=1)
    form = ConfigurationForm(request.POST or None, instance=config)
    if request.method == "POST" and form.is_valid():
        if not form.cleaned_data["enabled"]:
            form.save()
            return redirect("newsletter:settings")
        try:
            smtp_settings()
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            form.save()
            return redirect("newsletter:settings")
    return render(request, "newsletter/settings.html", {"form": form})


@require_http_methods(["GET", "HEAD"])
def opened(request, token):
    if request.method == "GET":
        Delivery.objects.filter(token=token, opened_at__isnull=True, sent_at__isnull=False).update(
            opened_at=timezone.now()
        )
    response = HttpResponse(PIXEL, content_type="image/gif")
    response["Cache-Control"] = "no-store, private"
    return response


@require_http_methods(["GET", "HEAD"])
def click(request, token, signature):
    try:
        target = signing.loads(signature, salt=f"{CLICK_SALT}.{token}")
    except signing.BadSignature as exc:
        raise Http404 from exc
    parsed = http_url(target)
    if not parsed:
        raise Http404
    delivery = get_object_or_404(Delivery, token=token, sent_at__isnull=False)
    if request.method == "GET":
        Delivery.objects.filter(pk=delivery.pk, clicked_at__isnull=True).update(clicked_at=timezone.now())
        if parsed.scheme == "https" and parsed.netloc.lower() == request.get_host().lower():
            request.session["newsletter_click"] = {"token": str(token), "at": timezone.now().timestamp()}
    response = redirect(target)
    response["Referrer-Policy"] = "no-referrer"
    response["Cache-Control"] = "no-store, private"
    return response


@csrf_exempt
@require_http_methods(["GET", "POST", "HEAD"])
def unsubscribe(request, token):
    delivery = get_object_or_404(Delivery, token=token, sent_at__isnull=False)
    if request.method == "POST":
        if request.POST.get("List-Unsubscribe") != "One-Click" and request.POST.get("unsubscribe") != "yes":
            return HttpResponse(status=400)
        Unsubscribe.objects.get_or_create(email=delivery.email, defaults={"delivery": delivery})
        if request.POST.get("List-Unsubscribe") == "One-Click":
            return HttpResponse(status=204)
    response = render(request, "newsletter/unsubscribe.html", {"finished": request.method == "POST"})
    response["Referrer-Policy"] = "no-referrer"
    response["Cache-Control"] = "no-store, private"
    return response
