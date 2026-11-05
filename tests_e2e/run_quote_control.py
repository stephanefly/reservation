"""Tester l'administration des devis sans charger les secrets PythonAnywhere."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests_e2e.settings")
os.environ.setdefault("CRM_E2E_SQLITE_PATH", ":memory:")

import django
django.setup()

from tests_e2e.boundaries import install_boundaries
install_boundaries()

from django.core.management import call_command

if __name__ == "__main__":
    call_command("test", "quote_control.tests", "quote_control.test_catalog", "quote_control.test_public_pricing", "quote_control.test_ui_clarity", "quote_control.test_preview_choices", "quote_control.test_price_breakdown", "quote_control.test_catalog_consolidation", "quote_control.test_quote_history", verbosity=1)
