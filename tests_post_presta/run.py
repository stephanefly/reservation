"""Exécute les tests post-presta avec Django isolé, sans settings.yaml ni base de production.

Commande: python -m tests_post_presta.run
"""
import sys
import types
from pathlib import Path

from django.conf import settings


def main():
    root = Path(__file__).resolve().parents[1]

    # Éviter de charger les intégrations cloud et e-mail durant ce test de vue.
    for name in ("app.views", "app.urls"):
        package = types.ModuleType(name)
        package.__path__ = [str(root.joinpath(*name.split(".")))]
        sys.modules[name] = package

    for module_name, function_name in (
        ("app.module.mail.send_mail_event", "send_mail_event"),
        ("app.module.cloud.send_media", "send_media_logic"),
    ):
        module = types.ModuleType(module_name)
        setattr(module, function_name, lambda *args, **kwargs: None)
        sys.modules[module_name] = module

    # Neutraliser aussi le client pCloud : son module normal lit settings.yaml
    # directement et n'est pas chargé dans le runner isolé.
    fake_cloud = types.ModuleType("app.module.cloud.get_pcloud_data")
    fake_cloud.get_pcloud_event_folder_data = lambda *args, **kwargs: None
    fake_cloud.get_pcloud_link_event_folder = lambda *args, **kwargs: ""
    sys.modules[fake_cloud.__name__] = fake_cloud

    settings.configure(
        SECRET_KEY="post-presta-tests-only",
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.staticfiles",
            "app",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        ROOT_URLCONF="app.urls.private_api_urls",
        LANGUAGE_CODE="fr-fr",
        USE_TZ=True,
        TIME_ZONE="Europe/Paris",
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        MIGRATION_MODULES={"app": None},
        STATIC_URL="/static/",
        ALLOWED_HOSTS=["testserver"],
        # Paramètres factices : tests sans connexion IONOS/pCloud.
        MAIL_MYSELFIEBOOTH="test@myselfiebooth-paris.fr",
        POST_PRESTA_PUBLICATION_EMAIL="djordan.cartier@myselfiebooth-paris.fr",
        MAIL_BCC="",
        MP="",
        API_PCLOUD_URL="https://api.pcloud.com",
        ACCESS_TOKEN="fake-test-token",
        ROOT_FOLDER_ID=1,
        ROOT_FOLDER_PREPA_ID=2,
        ROOT_FOLDER_MONTAGE_2025=3,
        ROOT_FOLDER_MONTAGE_2026=4,
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "OPTIONS": {"loaders": [
                ("django.template.loaders.locmem.Loader", {
                    "app/backend/base.html": "{% block extra_css %}{% endblock %}{% block content %}{% endblock %}"
                }),
                ("django.template.loaders.filesystem.Loader", [str(root / "app/templates")]),
            ]},
        }],
    )
    import django
    django.setup()

    from django.test.runner import DiscoverRunner

    failures = DiscoverRunner(verbosity=2).run_tests([
        "app.tests.test_post_presta_dashboard",
        "app.tests.test_publication_notification",
    ])
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()
