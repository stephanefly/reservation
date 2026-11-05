"""L'interface doit être compréhensible sans deuxième paramétrage."""
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

    def test_catalogue_explains_single_automatic_checkbox(self):
        result = self.client.get(reverse("admin_catalog"))
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Où vont vos modifications ?")
        self.assertContains(result, "Machines et packs existants")
        self.assertContains(result, "Ce qui ne change pas automatiquement")
        self.assertContains(result, "Composition du pack")
        self.assertContains(result, "Enregistrer l'offre")
        self.assertContains(result, "Un seul réglage")
        self.assertNotContains(result, "Prix du catalogue pour devis auto")
        self.assertNotContains(result, "Paramètres et simulation")

    def test_edit_offer_keeps_price_and_identity(self):
        ipad = CatalogEntry.objects.get(code="ipadbooth")
        result = self.client.get(reverse("admin_catalog"), {"edit": ipad.pk})
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Modifier iPad Booth")
        self.assertContains(result, "id_price")
        self.assertContains(result, "id_code")
        self.assertContains(result, "disabled")
        self.assertContains(result, "Les devis déjà établis ne changent pas.")
        self.assertEqual(CatalogEntry.objects.get(pk=ipad.pk).price, ipad.price)

    def test_simulation_only_no_legacy_settings_controls(self):
        result = self.client.get(reverse("admin_catalog"), {"tab": "simulation"})
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Simulation de devis")
        self.assertContains(result, "Simuler le devis")
        self.assertContains(result, "Machines demandées")
        self.assertNotContains(result, "Envoi automatique des devis")
        self.assertNotContains(result, "Paramétrage des devis")
        self.assertNotContains(result, "Réglages avancés")
        self.assertNotContains(result, "Numéro de dossier CRM")
        self.assertFalse(AutoQuoteSettings.objects.get(pk=1).enabled)

    def test_historic_config_does_not_add_more_settings(self):
        AutoQuoteSettings.objects.create(
            pk=1, enabled=True, catalog_enabled=False
        )
        result = self.client.get(reverse("admin_catalog"), {"tab": "simulation"})
        self.assertEqual(result.status_code, 200)
        self.assertNotContains(result, "Prix historiques de l'ancien mode")
        self.assertNotContains(result, "id_product_photobooth")
        self.assertNotContains(result, "Enregistrer les paramètres")

    def test_unauthenticated_cannot_access_catalogue(self):
        self.client.logout()
        for url in (reverse("admin_catalog"), reverse("admin_auto_quotes")):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)
