"""Read-only history of automatic quotes, restricted to authenticated staff."""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache
from app.models import Event
from .models import AutoQuoteLog


@never_cache
@require_GET
def auto_quote_history(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"error": "Authentication required"}, status=403)

    try:
        limit = int(request.GET.get("limit", 20))
        offset = int(request.GET.get("offset", 0))
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError()
    except ValueError:
        return JsonResponse({"error": "Invalid limit or offset"}, status=400)

    outcome = request.GET.get("outcome", "sent")
    logs = AutoQuoteLog.objects.order_by("-created_at", "-pk")
    if outcome != "all":
        if outcome not in dict(AutoQuoteLog.OUTCOMES):
            return JsonResponse({"error": "Invalid outcome"}, status=400)
        logs = logs.filter(outcome=outcome)

    page = list(logs[offset:offset + limit + 1])
    events = Event.objects.select_related("client").in_bulk(
        [log.event_id for log in page[:limit]]
    )
    rows = []
    for log in page[:limit]:
        event = events.get(log.event_id)
        current = event.prix_proposed if event else None
        rows.append({
            "log_id": log.pk,
            "event_id": log.event_id,
            "created_at": log.created_at.isoformat(),
            "outcome": log.outcome,
            "source": log.source,
            "reason": log.reason,
            "automatic_amount_eur": log.amount,
            "current_amount_eur": current,
            "difference_eur": current - log.amount if current is not None and log.amount is not None else None,
            "client_name": event.client.nom if event else None,
            "quote_number": event.num_devis if event else None,
            "current_status": event.status if event else None,
            "history_status": event.history_status if event else None,
        })
    return JsonResponse({
        "results": rows,
        "next_offset": offset + limit if len(page) > limit else None,
    })
