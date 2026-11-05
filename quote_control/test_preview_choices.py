"""Simuler une demande fictive sans retrouver, creer ou modifier un dossier CRM."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Client, Event, EventDetails, EventOption, EventProduct
from quote_control.models import AutoQuoteLog, AutoQuoteSettings, CatalogEntry


class FreeQuoteSimulationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("simulation-staff", password="test-only", is_staff=True)
        self.client.force_login(self.staff)
        self.url = reverse("admin_auto_quotes")
        self.config = AutoQuoteSettings.objects.create(pk=1)

    def scenario(self, **changes):
        query = {
            "simulate": "1",
            "products": ["photobooth"],
            "duration": "5",
            "postal_code": "75001",
            "source": "INSTAGRAM",
        }
        query.update(changes)
        return self.client.get(self.url, query)

    def test_dashboard_has_only_two_primary_panels(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        page = response.content.decode()
        self.assertEqual(page.count('class="auto-panel"'), 2)
        self.assertIn('id="settings-title">Paramétrage', page)
        self.assertIn('id="simulation-title">Simulation', page)
        self.assertIn("Choisissez les machines", page)
        self.assertNotIn("Voir le calcul", page)
        self.assertNotIn("Choisissez une demande récente", page)

    def test_simulate_single_photobooth_without_saving_any_client_or_event(self):
        counts_before = (
            Client.objects.count(), Event.objects.count(), EventProduct.objects.count(),
            EventOption.objects.count(), EventDetails.objects.count(),
        )
        with patch("app.module.mail.send_mail_event.send_mail_event") as sender:
            result = self.scenario()
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Résultat de la simulation")
        self.assertContains(result, "400 € TTC")
        self.assertTrue(result.context["simulation"]["analysis"]["eligible"])
        self.assertEqual(result.context["simulation"]["analysis"]["amount"], 400)
        self.assertEqual(
            (Client.objects.count(), Event.objects.count(), EventProduct.objects.count(),
             EventOption.objects.count(), EventDetails.objects.count()),
            counts_before,
        )
        self.assertFalse(AutoQuoteLog.objects.exists())
        sender.assert_not_called()
        self.config.refresh_from_db()
        self.assertFalse(self.config.enabled)

    def test_simulate_two_machines_without_known_pack_requires_manual(self):
        result = self.scenario(products=["photobooth", "miroirbooth"])
        self.assertFalse(result.context["simulation"]["analysis"]["eligible"])
        self.assertContains(result, "Devis à traiter manuellement")
        self.assertContains(result, "Combinaison sans pack")

    def test_simulate_known_vogue_pack(self):
        result = self.scenario(
            products=["voguebooth"],
            options=["PhotographeVoguebooth", "ImpressionVoguebooth"],
        )
        self.assertTrue(result.context["simulation"]["analysis"]["eligible"])
        self.assertEqual(result.context["simulation"]["analysis"]["amount"], 700)
        self.assertContains(result, "Pack Vogue Premium")

    def test_incorrect_postcode_does_not_calculate(self):
        for postal_code in ("abcde", "7500", "750011", "-1"):
            with self.subTest(postal_code=postal_code):
                result = self.scenario(postal_code=postal_code)
                self.assertIsNone(result.context["simulation"])
                self.assertContains(result, "code postal")

    def test_company_and_recommendation_stay_manual(self):
        result = self.scenario(business="on")
        self.assertFalse(result.context["simulation"]["analysis"]["eligible"])
        self.assertContains(result, "Entreprise")
        result = self.scenario(source="RECOMMENDATION")
        self.assertFalse(result.context["simulation"]["analysis"]["eligible"])
        self.assertContains(result, "Recommandation")

    def test_catalog_prices_are_used_when_enabled_and_allowed(self):
        self.config.catalog_enabled = True
        self.config.save(update_fields=["catalog_enabled"])
        photo = CatalogEntry.objects.get(code="photobooth")
        photo.price = 375
        photo.auto_enabled = True
        photo.save(update_fields=["price", "auto_enabled"])
        result = self.scenario()
        self.assertEqual(result.context["simulation"]["analysis"]["amount"], 375)

    def test_no_products_no_quote(self):
        result = self.scenario(products=[])
        self.assertIsNone(result.context["simulation"])
        self.assertContains(result, "Vérifiez les champs")

    def test_private_page(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url, {"simulate": 1}).status_code, 302)
