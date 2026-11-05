"""Le catalogue est la seule commande de l'envoi automatique."""
from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Client, Event, EventDetails, EventOption, EventProduct
from quote_control.auto_policy import effective_quote_config, has_automatic_offers
from quote_control.models import AutoQuoteLog, AutoQuoteSettings, CatalogEntry
from quote_control.service import process_instant_quote
from quote_control.tests import fake_event


class UnifiedCatalogueTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            "unified-staff", password="tests", is_staff=True
        )
        self.visitor = User.objects.create_user(
            "unified-visitor", password="tests"
        )
        self.client.force_login(self.staff)
        self.url = reverse("admin_catalog")
        self.legacy = reverse("admin_auto_quotes")

    def offer_payload(self, *, enabled=True, price=400):
        values = {
            "entry": CatalogEntry.objects.get(code="photobooth").pk,
            "kind": "product", "name": "Photobooth",
            "code": "photobooth", "price": str(price), "active": "on",
        }
        if enabled:
            values["auto_enabled"] = "on"
        return values

    def test_catalogue_has_only_offers_and_simulation_tabs(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Offres et tarifs", html)
        self.assertIn("Simulation</a>", html)
        self.assertNotIn("Paramètres et simulation", html)
        self.assertNotIn("Paramétrage des devis", html)
        self.assertNotIn("fa-magic", html)
        self.assertEqual(response.context["active_tab"], "offres")
        self.assertFalse(response.context["auto_enabled"])

    def test_simulation_has_no_settings_form(self):
        response = self.client.get(self.url, {"tab": "simulation"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "simulation")
        self.assertContains(response, "Simulation de devis")
        self.assertContains(response, "Simuler le devis")
        self.assertContains(response, "Nom de l'entreprise")
        self.assertNotContains(response, "Enregistrer les paramètres")
        self.assertNotContains(response, "Réglages avancés")
        self.assertNotContains(response, "Paramétrage des devis")

    def test_checkbox_is_effective_without_any_second_activation(self):
        self.assertFalse(has_automatic_offers())
        self.client.get(self.url)  # ancienne config créée mais non activée
        config = AutoQuoteSettings.objects.get(pk=1)
        self.assertFalse(config.enabled)
        self.assertFalse(config.catalog_enabled)
        response = self.client.post(self.url, self.offer_payload())
        self.assertEqual(response.status_code, 302)
        offer = CatalogEntry.objects.get(code="photobooth")
        self.assertTrue(offer.auto_enabled)
        self.assertTrue(has_automatic_offers())
        effective = effective_quote_config(config)
        self.assertTrue(effective.enabled)
        self.assertTrue(effective.catalog_enabled)
        self.assertFalse(config.enabled)  # aucune deuxième case cachée

        simulation = self.client.post(self.url + "?tab=simulation", {
            "operation": "simulate", "products": ["photobooth"],
            "duration": "5", "postal_code": "75001",
            "source": "INSTAGRAM",
        })
        self.assertEqual(simulation.status_code, 200)
        self.assertEqual(simulation.context["simulation"]["analysis"]["amount"], 400)
        self.assertTrue(simulation.context["simulation"]["analysis"]["eligible"])

    def test_unchecking_last_offer_disables_sending_even_if_legacy_enabled(self):
        offer = CatalogEntry.objects.get(code="photobooth")
        offer.auto_enabled = True
        offer.save(update_fields=["auto_enabled"])
        AutoQuoteSettings.objects.create(
            pk=1, enabled=True, catalog_enabled=False
        )
        self.assertTrue(effective_quote_config().enabled)
        response = self.client.post(self.url, self.offer_payload(enabled=False))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(has_automatic_offers())
        self.assertFalse(effective_quote_config().enabled)
        event = fake_event(photobooth=True)
        event.pk = 884
        event.save = Mock()
        send = Mock(return_value=True)
        self.assertFalse(process_instant_quote(event, send))
        send.assert_not_called()
        event.save.assert_not_called()

    def test_eligible_offer_sends_quote_for_new_supported_request(self):
        offer = CatalogEntry.objects.get(code="photobooth")
        offer.auto_enabled = True
        offer.save(update_fields=["auto_enabled"])
        # Aucune validation de config ni formulaire complémentaire.
        event = fake_event(photobooth=True)
        event.pk = 885
        event.save = Mock()
        send = Mock(return_value=True)
        self.assertTrue(process_instant_quote(event, send))
        send.assert_called_once_with(event, "devis")
        self.assertEqual(event.prix_proposed, 400)
        self.assertEqual(event.status, "Sended")
        self.assertEqual(AutoQuoteLog.objects.get(event_id=885).outcome, "sent")

    def test_company_and_recommendation_remain_manual(self):
        offer = CatalogEntry.objects.get(code="photobooth")
        offer.auto_enabled = True
        offer.save(update_fields=["auto_enabled"])
        for i, event in enumerate((
            fake_event(photobooth=True, entreprise=True),
            fake_event(photobooth=True, source="RECOMMENDATION"),
        ), start=1):
            event.pk = 900 + i
            event.save = Mock()
            send = Mock(return_value=True)
            self.assertFalse(process_instant_quote(event, send))
            send.assert_not_called()
            event.save.assert_not_called()
            self.assertEqual(
                AutoQuoteLog.objects.get(event_id=event.pk).outcome, "manual"
            )

    def test_company_simulation_is_realistic_and_saves_nothing(self):
        self.client.get(self.url)
        original = (
            Client.objects.count(), Event.objects.count(),
            EventDetails.objects.count(), EventOption.objects.count(),
            EventProduct.objects.count(),
        )
        response = self.client.post(self.url + "?tab=simulation", {
            "operation": "simulate", "products": ["photobooth"],
            "duration": "5", "postal_code": "75001",
            "source": "INSTAGRAM", "client_name": "Martin",
            "company_name": "Entreprise Exemple",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Martin")
        self.assertContains(response, "Entreprise Exemple")
        self.assertContains(response, "Devis à traiter manuellement")
        self.assertFalse(response.context["simulation"]["analysis"]["eligible"])
        self.assertEqual(
            (Client.objects.count(), Event.objects.count(),
             EventDetails.objects.count(), EventOption.objects.count(),
             EventProduct.objects.count()), original,
        )
        self.assertFalse(AutoQuoteLog.objects.exists())

    def test_old_link_and_post_cannot_restore_hidden_settings(self):
        response = self.client.get(self.legacy, {
            "simulate": "1", "products": ["photobooth"],
            "duration": "5", "postal_code": "75001", "source": "INSTAGRAM",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("tab=simulation", response["Location"])
        self.assertIn("simulate=1", response["Location"])
        response = self.client.post(self.legacy, {
            "enabled": "on", "catalog_enabled": "on",
            "confirm_activation": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(has_automatic_offers())
        self.assertFalse(effective_quote_config().enabled)

    def test_staff_access_restrictions(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.client.post(self.url, self.offer_payload()).status_code, 302)
        self.client.force_login(self.visitor)
        self.assertEqual(self.client.get(self.url, {"tab": "simulation"}).status_code, 302)
        self.assertEqual(self.client.get(self.legacy).status_code, 302)
