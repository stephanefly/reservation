"""Focused SQLite tests using real CRM models, views and URL patterns.

Skip unrelated package initializers (which load cloud/mail integrations).
No production configuration, external service or real customer data is loaded.
Run: python -m tests_api.run
"""
import sys
import types
from pathlib import Path

from django.conf import settings


def main():
    root = Path(__file__).resolve().parents[1]
    for name in ("app.views", "app.urls"):
        package = types.ModuleType(name)
        package.__path__ = [str(root.joinpath(*name.split(".")))]
        sys.modules[name] = package
    settings.configure(
        SECRET_KEY="isolated-tests-only", PRIVATE_API_TOKEN="test-private-token",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "app"], DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        LANGUAGE_CODE="fr-fr",
        ROOT_URLCONF="app.urls.private_api_urls", USE_TZ=True, TIME_ZONE="Europe/Paris",
        DEFAULT_AUTO_FIELD="django.db.models.AutoField", MIGRATION_MODULES={"app": None},
        ALLOWED_HOSTS=["testserver"],
        TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates", "OPTIONS": {"loaders": [
            ("django.template.loaders.locmem.Loader", {"app/backend/base.html": "{% block extra_css %}{% endblock %}{% block content %}{% endblock %}"}),
            ("django.template.loaders.filesystem.Loader", [str(root / "app/templates")]),
        ]}}],
    )
    import django
    django.setup()
    from django.test.runner import DiscoverRunner
    failures = DiscoverRunner(verbosity=2).run_tests(["app.tests.test_private_api", "app.tests.test_email_stats", "app.tests.test_commercial_stats", "app.tests.test_email_delivery", "app.tests.test_tracking_upgrade"])
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()
