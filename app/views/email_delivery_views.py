from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from app.models import EmailTracking, EmailMailboxCheck, Event
from app.views.private_api_data import filter_dates, integer


@never_cache
@staff_member_required(login_url="login")
@require_GET
def graph_email_delivery(request):
    context = {"start_date": request.GET.get("start_date", ""), "end_date": request.GET.get("end_date", ""),
               "delivery_status": request.GET.get("status", ""), "event_id": request.GET.get("event_id", ""),
               "choices": EmailTracking.DELIVERY_STATUS, "mailbox": EmailMailboxCheck.objects.filter(key="ionos").first()}
    try:
        deliveries = filter_dates(request, EmailTracking.objects.all(), "sent_at", with_time=True)
        if context["event_id"]:
            deliveries = deliveries.filter(event_traced=integer(request, "event_id", 0))
        if context["delivery_status"]:
            if context["delivery_status"] not in dict(EmailTracking.DELIVERY_STATUS):
                raise ValueError("État d'envoi invalide.")
            deliveries = deliveries.filter(delivery_status=context["delivery_status"])
        counts = dict(deliveries.values("delivery_status").annotate(total=Count("id")).values_list("delivery_status", "total"))
        context["counters"] = [{"label": label, "count": counts.get(status, 0)} for status, label in EmailTracking.DELIVERY_STATUS]
        context["total"] = sum(counts.values())
        context["page"] = Paginator(deliveries.order_by("-sent_at", "-id"), 50).get_page(request.GET.get("page"))
        rows = list(context["page"].object_list)
        events = {event.id: event for event in Event.objects.filter(id__in=[row.event_traced for row in rows if row.event_traced]).select_related("client")}
        for row in rows:
            row.event = events.get(row.event_traced)
        context["page"].object_list = rows
        params = request.GET.copy()
        params.pop("page", None)
        context["query"] = params.urlencode()
    except ValueError as exc:
        context["error"] = str(exc)
        return render(request, "app/backend/graph/graph_email_delivery.html", context, status=400)
    return render(request, "app/backend/graph/graph_email_delivery.html", context)
