"""Routes commerciales réelles, navigation hors scénario rendue inopérante."""
import re
import sys

from django.http import HttpResponseNotFound
from django.urls import include, path, re_path
from django.views.static import serve

from app.views import backend_views, frontend_views
from tests_e2e import settings

views = sys.modules["app.views"]
for module in (frontend_views, backend_views):
    for name, value in vars(module).items():
        if callable(value):
            setattr(views, name, value)

urlpatterns = [
    path("", include("app.urls.frontend_urls")),
    path("backend/info-event/", include("app.urls.info_event_urls")),
    path("backend/devis-auto/", include("quote_control.urls")),
    path("tarifs/", include("app.urls.pricing_urls")),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.BASE_DIR / "app/static"}),
]


def outside_scenario(request, **kwargs):
    return HttpResponseNotFound("Route hors du scénario de test.")


from app.urls import frontend_urls, info_event_urls, pricing_urls
from quote_control import urls as quote_control_urls

known_names = {
    route.name
    for module in (frontend_urls, info_event_urls, pricing_urls, quote_control_urls)
    for route in module.urlpatterns
}
# Neutraliser uniquement les liens de navigation qui sortent du parcours commercial.
for template in (settings.BASE_DIR / "app/templates/app").rglob("*.html"):
    for name, arguments in re.findall(r"{% url '([\w-]+)'([^%]*)%}", template.read_text()):
        if name not in known_names:
            suffix = "<str:id>/" if arguments.strip() else ""
            urlpatterns.append(path(f"outside-test/{name}/{suffix}", outside_scenario, name=name))
            known_names.add(name)
