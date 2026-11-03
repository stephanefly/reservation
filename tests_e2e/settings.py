"""Configuration exclusivement réservée au test automatique."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "crm-e2e-local-only"
INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.auth", "app", "quote_control", "bootstrap5"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "tests_e2e.urls"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}]
STATIC_URL = "/static/"
USE_TZ = True
TIME_ZONE = "Europe/Paris"
# Les migrations privées de PythonAnywhere ne sont pas utilisées par ce test.
MIGRATION_MODULES = {"app": None}
if os.environ.get("CRM_E2E_MYSQL") == "1":
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.mysql", "NAME": "crm_e2e", "USER": "crm_e2e",
        "PASSWORD": "crm-e2e-only", "HOST": "127.0.0.1",
        "PORT": os.environ.get("CRM_E2E_MYSQL_PORT", "3306"),
    }}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3", "NAME": os.environ["CRM_E2E_SQLITE_PATH"],
    }}

# Valeurs fictives, indépendantes de settings.yaml et de la production.
PDF_REPERTORY = str(BASE_DIR / "app/module/devis_pdf")
MAIL_TEMPLATE_REPOSITORY = str(BASE_DIR / "app/templates/mail")
MAIL_MYSELFIEBOOTH = "crm@example.invalid"
MAIL_BCC = "archive@example.invalid"
MP = "not-a-production-password"
KEY_TRELLO = TOKEN_TRELLO = API_PCLOUD_URL = ACCESS_TOKEN = "test-only"
TITULAIRE_DU_COMPTE_A = TITULAIRE_DU_COMPTE_B = "TEST"
IBAN_A = IBAN_B = BIC_A = BIC_B = "TEST"
