from django.urls import path
from .catalog_views import admin_catalog

urlpatterns = [
    path("", admin_catalog, name="admin_catalog"),
]
