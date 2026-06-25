from django.urls import path

from app.views.private_api import (
    private_api_crm_summary,
    private_api_event_detail,
    private_api_ping,
    private_api_upcoming_events,
)

urlpatterns = [
    path("ping/", private_api_ping, name="private_api_ping"),
    path("crm-summary/", private_api_crm_summary, name="private_api_crm_summary"),
    path("upcoming-events/", private_api_upcoming_events, name="private_api_upcoming_events"),
    path("event/<int:event_id>/", private_api_event_detail, name="private_api_event_detail"),
]
