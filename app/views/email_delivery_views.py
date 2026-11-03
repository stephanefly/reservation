from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from app.models import EmailDelivery, EmailMailboxCheck
from app.views.private_api_data import filter_dates, integer


@never_cache
@staff_member_required(login_url="login")
@require_GET
def graph_email_delivery(request):
    context = {"start_date": request.GET.get("start_date", ""), "end_date": request.GET.get("end_date", ""),
               "delivery_status": request.GET.get("status", ""), "event_id": request.GET.get("event_id", ""),
               "choices": EmailDelivery.STATUS, "mailbox": EmailMailboxCheck.objects.filter(key="ionos").first()}
    try:
        deliveries = filter_dates(request, EmailDelivery.objects.all(), "created_at", with_time=True)
        if context["event_id"]:
            deliveries = deliveries.filter(event_id=integer(request, "event_id", 0))
        if context["delivery_status"]:
            if context["delivery_status"] not in dict(EmailDelivery.STATUS):
                raise ValueError("État d'envoi invalide.")
            deliveries = deliveries.filter(status=context["delivery_status"])
        counts = dict(deliveries.values("status").annotate(total=Count("id")).values_list("status", "total"))
        context["counters"] = [{"label": label, "count": counts.get(status, 0)} for status, label in EmailDelivery.STATUS]
        context["total"] = sum(counts.values())
        context["page"] = Paginator(deliveries.select_related("event__client", "tracking").order_by("-created_at", "-id"), 50).get_page(request.GET.get("page"))
        params = request.GET.copy()
        params.pop("page", None)
        context["query"] = params.urlencode()
    except ValueError as exc:
        context["error"] = str(exc)
        return render(request, "app/backend/graph/graph_email_delivery.html", context, status=400)
    return render(request, "app/backend/graph/graph_email_delivery.html", context)
