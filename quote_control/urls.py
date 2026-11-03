from django.urls import path
from .views import admin_quotes, preview_pdf

urlpatterns = [
    path("", admin_quotes, name="admin_auto_quotes"),
    path("apercu-pdf/<int:event_id>/", preview_pdf, name="admin_auto_quotes_preview_pdf"),
]
