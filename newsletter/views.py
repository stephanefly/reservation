import base64
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.contrib.admin.views.decorators import staff_member_required
from django.core import signing
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .forms import AudienceForm, ConfigurationForm, ContentForm, ScheduleForm, TemplateForm, TestForm
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
def create(request):
    form = AudienceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        campaign = form.save()
        campaign.step = 2
        campaign.save(update_fields=["step"])
        return redirect("newsletter:edit", pk=campaign.pk, step=2)
    return render(request, "newsletter/wizard.html", {"form": form, "step": 1})


@staff
@require_http_methods(["GET", "POST"])
def edit(request, pk, step):
    if step not in (1, 2, 3, 4):
        raise Http404
    if request.method == "POST" and step < 4:
        with transaction.atomic():
            return edit_step(request, pk, step, lock=True)
    return edit_step(request, pk, step)


def edit_step(request, pk, step, lock=False):
    campaigns = Campaign.objects.select_for_update() if lock else Campaign.objects
    campaign = get_object_or_404(campaigns, pk=pk)
    if campaign.status != Campaign.Status.DRAFT:
        return redirect("newsletter:detail", pk=pk)
    if step > campaign.step:
        return redirect("newsletter:edit", pk=pk, step=campaign.step)
    data = request.POST if request.method == "POST" else None
    context = {"campaign": campaign, "step": step}
    if step == 4:
        context.update(form=TestForm(data), count=len(eligible(campaign.audience)))
        if data is not None and context["form"].is_valid():
            send_test(campaign, context["form"].cleaned_data["email"], context)
    elif step == 1:
        context["form"] = AudienceForm(data, instance=campaign)
    elif step == 2:
        context["form"] = ContentForm(data, request.FILES, instance=campaign)
    else:
        with timezone.override(ZoneInfo("Europe/Paris")):
            initial = {"mode": "later" if campaign.scheduled_at else "now", "at": campaign.scheduled_at}
            context["form"] = ScheduleForm(data, initial=initial)
            if data is not None and context["form"].is_valid():
                campaign.scheduled_at = context["form"].cleaned_data["at"]
            return save_step(request, campaign, context)
    return save_step(request, campaign, context)


def save_step(request, campaign, context):
    step = context["step"]
    form = context["form"]
    if request.method == "POST" and step < 4 and form.is_valid():
        if step < 3:
            campaign = form.save(commit=False)
        campaign.step = step + 1
        campaign.save()
        return redirect("newsletter:edit", pk=campaign.pk, step=campaign.step)
    return render(request, "newsletter/wizard.html", context)


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


@staff
@require_POST
def confirm(request, pk):
    with transaction.atomic():
        campaign = get_object_or_404(Campaign.objects.select_for_update(), pk=pk)
        if campaign.status != Campaign.Status.DRAFT:
            return redirect("newsletter:detail", pk=pk)
        if campaign.step != 4:
            return redirect("newsletter:edit", pk=pk, step=campaign.step)
        emails = eligible(campaign.audience)
        now = timezone.now()
        error = None
        if request.POST.get("confirm") != "yes":
            error = "Cochez la confirmation pour mettre la campagne en file."
        elif not emails:
            error = "Aucun destinataire éligible."
        elif campaign.scheduled_at and campaign.scheduled_at <= now:
            error = "La date prévue est passée. Modifiez la programmation."
        elif not Configuration.objects.filter(pk=1, enabled=True, sender__gt="").exists():
            error = "Activez les envois et renseignez l’adresse d’expédition."
        else:
            try:
                smtp_settings()
            except ValueError as exc:
                error = str(exc)
        if error:
            return render(request, "newsletter/wizard.html", {
                "campaign": campaign, "step": 4, "count": len(emails), "form": TestForm(), "error": error,
            }, status=400)
        Delivery.objects.bulk_create([
            Delivery(campaign=campaign, email=email) for email in sorted(emails)
        ], batch_size=500)
        campaign.confirmed_at = now
        campaign.scheduled_at = campaign.scheduled_at or now
        campaign.status = Campaign.Status.QUEUED
        campaign.save(update_fields=["confirmed_at", "scheduled_at", "status"])
    return redirect("newsletter:detail", pk=pk)


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
        return redirect("newsletter:edit", pk=pk, step=campaign.step)
    deliveries = campaign.deliveries.order_by("pk")
    page = Paginator(deliveries, 100).get_page(request.GET.get("page"))
    return render(request, "newsletter/detail.html", {
        "campaign": campaign, "page_obj": page, "stats": metrics(deliveries),
        "unsubscribes": Unsubscribe.objects.filter(delivery__campaign=campaign).order_by("-created_at"),
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
