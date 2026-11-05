"""Une seule navigation Catalogue, avec paramètres et simulation sécurisés."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Client, Event, EventDetails, EventOption, EventProduct
from quote_control.catalog import default_pack_prices, default_product_prices
from quote_control.models import AutoQuoteLog, AutoQuoteSettings, CatalogEntry


class UnifiedCatalogueTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            "unified-staff", password="tests", is_staff=True,
        )
        self.visitor = User.objects.create_user("unified-visitor", password="tests")
        self.client.force_login(self.staff)
        self.url = reverse("admin_catalog")
        self.legacy = reverse("admin_auto_quotes")

    def settings_payload(self, **updates):
        values = {
            "operation": "settings",
            "enabled": "on",
            "catalog_enabled": "on",
            "confirm_activation": "on",
            "sources": ["INSTAGRAM"],
            "products": ["photobooth"],
            "packs": ["vogue-premium"],
        }
        values.update({"product_" + k: price for k, price in default_product_prices().items()})
        values.update({"pack_" + k: price for k, price in default_pack_prices().items()})
        values.update(updates)
        return values

    def test_only_catalogue_in_backend_nav_and_two_subtabs(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Offres et tarifs", html)
        self.assertIn("Paramètres et simulation", html)
        self.assertIn('class="catalog-tabs"', html)
        self.assertNotIn("fa-magic", html)
        self.assertEqual(response.context["active_tab"], "offres")
        self.assertContains(response, "Remise −50 €")
        self.assertNotContains(response, "Simuler le devis")

    def test_automation_lives_inside_catalogue(self):
        response = self.client.get(self.url, {"tab": "automation"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "automation")
        self.assertContains(response, "Paramétrage des devis")
        self.assertContains(response, "Simulation")
        self.assertContains(response, "Origine des demandes")
        self.assertContains(response, "Client entreprise")
        self.assertContains(response, "Enregistrer les paramètres")
        self.assertNotContains(response, "Enregistrer l'offre")
        self.assertNotContains(response, "Numéro de dossier CRM")
        self.assertFalse(AutoQuoteSettings.objects.get(pk=1).enabled)

    def test_settings_post_from_catalogue_does_not_touch_offers(self):
        self.client.get(self.url)
        original_price = CatalogEntry.objects.get(code="photobooth").price
        response = self.client.post(self.url + "?tab=automation", self.settings_payload())
        self.assertEqual(response.status_code, 302)
        self.assertIn("?tab=automation&saved_settings=1", response["Location"])
        config = AutoQuoteSettings.objects.get(pk=1)
        self.assertTrue(config.enabled)
        self.assertTrue(config.catalog_enabled)
        self.assertEqual(config.sources, ["INSTAGRAM"])
        self.assertEqual(config.packs, ["vogue-premium"])
        self.assertEqual(CatalogEntry.objects.get(code="photobooth").price, original_price)

    def test_settings_require_confirmation_and_keep_automation_disabled(self):
        values = self.settings_payload()
        values.pop("confirm_activation")
        response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "automation")
        self.assertIn("confirm_activation", response.context["settings_form"].errors)
        self.assertFalse(AutoQuoteSettings.objects.get(pk=1).enabled)

    def test_company_name_is_sufficient_for_manual_quote_and_never_saved(self):
        original = (Client.objects.count(), Event.objects.count(),
                    EventDetails.objects.count(), EventOption.objects.count(),
                    EventProduct.objects.count())
        response = self.client.post(self.url + "?tab=automation", {
            "operation": "simulate", "products": ["photobooth"],
            "duration": "5", "postal_code": "75001", "source": "INSTAGRAM",
            "client_name": "Martin", "company_name": "Entreprise Exemple",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Martin")
        self.assertContains(response, "Entreprise Exemple")
        self.assertContains(response, "Devis à traiter manuellement")
        self.assertFalse(response.context["simulation"]["analysis"]["eligible"])
        self.assertEqual((Client.objects.count(), Event.objects.count(),
                          EventDetails.objects.count(), EventOption.objects.count(),
                          EventProduct.objects.count()), original)
        self.assertFalse(AutoQuoteLog.objects.exists())
        self.assertFalse(AutoQuoteSettings.objects.get(pk=1).enabled)

    def test_post_simulation_uses_catalogue_prices_without_saving_config(self):
        offer = CatalogEntry.objects.get(code="photobooth")
        original_price = offer.price
        response = self.client.post(self.url, {
            "operation": "simulate", "products": ["photobooth"],
            "duration": "5", "postal_code": "75001",
            "source": "INSTAGRAM", "client_name": "Test sans stockage",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "automation")
        self.assertEqual(response.context["simulation"]["analysis"]["amount"], 400)
        self.assertContains(response, "Test sans stockage")
        self.assertEqual(CatalogEntry.objects.get(pk=offer.pk).price, original_price)
        self.assertFalse(AutoQuoteSettings.objects.get(pk=1).enabled)

    def test_old_get_redirects_to_catalogue_without_losing_query(self):
        response = self.client.get(self.legacy, {
            "simulate": "1", "products": ["photobooth"], "duration": "5",
            "postal_code": "75001", "source": "INSTAGRAM",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("/backend/catalogue/", response["Location"])
        self.assertIn("tab=automation", response["Location"])
        self.assertIn("simulate=1", response["Location"])
        canonical = self.client.get(response["Location"])
        self.assertEqual(canonical.status_code, 200)
        self.assertEqual(canonical.context["simulation"]["analysis"]["amount"], 400)

    def test_legacy_settings_post_remains_compatible(self):
        values = self.settings_payload()
        values.pop("operation")
        response = self.client.post(self.legacy, values)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/backend/catalogue/", response["Location"])
        self.assertTrue(AutoQuoteSettings.objects.get(pk=1).enabled)

    def test_only_staff_can_read_or_edit_unified_catalogue(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.client.post(self.url, self.settings_payload()).status_code, 302)
        self.client.force_login(self.visitor)
        self.assertEqual(self.client.get(self.url, {"tab": "automation"}).status_code, 302)
        self.assertEqual(self.client.get(self.legacy).status_code, 302)
