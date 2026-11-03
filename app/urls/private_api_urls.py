from django.urls import path

from app.views.private_api_data import (
    private_api_email_stats,
    private_api_resource,
    private_api_schema,
)

from app.views.private_api import (
    private_api_confirmed_events,
    private_api_crm_summary,
    private_api_event_detail,
    private_api_ping,
    private_api_upcoming_events,
)

urlpatterns = [
    path("schema/", private_api_schema, name="private_api_schema"),
    path("email-stats/", private_api_email_stats, name="private_api_email_stats"),
    path("resources/<slug:resource>/", private_api_resource, name="private_api_resource"),
    path("resources/<slug:resource>/<int:record_id>/", private_api_resource, name="private_api_resource_detail"),
    path("ping/", private_api_ping, name="private_api_ping"),
    path("crm-summary/", private_api_crm_summary, name="private_api_crm_summary"),
    path("upcoming-events/", private_api_upcoming_events, name="private_api_upcoming_events"),
    path("confirmed-events/", private_api_confirmed_events, name="private_api_confirmed_events"),
    path("event/<int:event_id>/", private_api_event_detail, name="private_api_event_detail"),
]

