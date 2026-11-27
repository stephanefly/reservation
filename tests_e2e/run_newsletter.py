"""Vérifier la Newsletter avec base de test et SMTP simulé."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests_e2e.settings")
os.environ.setdefault("CRM_E2E_SQLITE_PATH", ":memory:")

import django
from django.core.management import call_command
from tests_e2e.boundaries import install_boundaries

django.setup()
install_boundaries()

if __name__ == "__main__":
    call_command("test", "newsletter", verbosity=1)
