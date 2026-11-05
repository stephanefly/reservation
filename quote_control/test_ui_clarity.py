"""La documentation dans l'interface ne doit pas changer les règles commerciales."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from quote_control.models import AutoQuoteSettings, CatalogEntry


class CatalogueClarityTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="clarity-staff", password="test-only", is_staff=True
        )
        self.client.force_login(self.staff)

    def test_catalogue_shows_precise_price_impact_and_contextual_help(self):
        result = self.client.get(reverse("admin_catalog"))
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Où vont vos modifications ?")
        self.assertContains(result, "Machines et packs existants")
        self.assertContains(result, "Options :")
        self.assertContains(result, "Ce qui ne change pas automatiquement")
        self.assertContains(result, "Composition du pack")
        self.assertContains(result, "Enregistrer l'offre")
        self.assertContains(result, "Prix du catalogue pour devis auto :")

    def test_catalogue_edit_form_keeps_editable_price_and_safe_identity(self):
        ipad = CatalogEntry.objects.get(code="ipadbooth")
        result = self.client.get(reverse("admin_catalog"), {"edit": ipad.pk})
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Modifier iPad Booth")
        self.assertContains(result, "id_price")
        self.assertContains(result, "id_code")
        self.assertContains(result, "disabled")
        self.assertContains(result, "Les devis déjà établis ne changent pas.")
        self.assertEqual(CatalogEntry.objects.get(pk=ipad.pk).price, ipad.price)

    def test_devis_screen_distinguishes_public_prices_and_auto_send(self):
        result = self.client.get(reverse("admin_auto_quotes"))
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Deux réglages différents.")
        self.assertContains(result, "Tarifs/Brochure")
        self.assertContains(result, "Autoriser l'envoi automatique de devis PDF")
        self.assertContains(result, "Aperçu rapide des devis")
        self.assertNotContains(result, "Numéro de dossier CRM")
        self.assertContains(result, "Tarifs et packs de l'ancien mode")
        self.assertFalse(AutoQuoteSettings.objects.get(pk=1).enabled)

    def test_devis_mode_catalogue_hides_only_legacy_explanation_by_default(self):
        config = AutoQuoteSettings.objects.create(pk=1, catalog_enabled=True)
        result = self.client.get(reverse("admin_auto_quotes"))
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "non utilisés")
        self.assertContains(result, "id_product_photobooth")
        config.refresh_from_db()
        self.assertFalse(config.enabled)
        self.assertTrue(config.catalog_enabled)

    def test_unauthenticated_cannot_access_explanatory_pages(self):
        self.client.logout()
        for url in (reverse("admin_catalog"), reverse("admin_auto_quotes")):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)
