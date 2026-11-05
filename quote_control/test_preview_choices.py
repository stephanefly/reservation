"""Choix d'un dossier recent pour l'apercu, sans saisie d'identifiant."""
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Client, Event, EventDetails, EventOption, EventProduct
from quote_control.models import AutoQuoteLog, AutoQuoteSettings


class RecentQuotePreviewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("preview-staff", password="test-only", is_staff=True)
        self.client.force_login(self.staff)
        self.client_record = Client.objects.create(
            nom="Client aperçu", mail="preview@example.invalid",
            numero_telephone="0100000000", how_find="INSTAGRAM",
        )
        self.details = EventDetails.objects.create(
            date_evenement=date(2027, 3, 12), adresse_evenement="1 rue Exemple",
            ville_evenement="Paris", code_postal_evenement=75001,
        )
        self.product = EventProduct.objects.create(photobooth=True)
        self.option = EventOption.objects.create(duree=5)
        self.url = reverse("admin_auto_quotes")

    def add_event(self):
        return Event.objects.create(
            client=self.client_record, event_details=self.details,
            event_product=self.product, event_option=self.option,
            prix_brut=0,
        )

    def test_show_recent_dossiers_instead_of_manual_id_field(self):
        event = self.add_event()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aperçu rapide des devis")
        self.assertContains(response, "Client aperçu")
        self.assertContains(response, "Voir le calcul")
        self.assertContains(response, f"?event={event.pk}#apercu")
        self.assertNotContains(response, 'id="preview-id"')
        self.assertNotContains(response, "Numéro de dossier CRM")
        self.assertEqual(len(response.context["recent_events"]), 1)

    def test_recent_dossiers_limited_and_ordered(self):
        events = [self.add_event() for _ in range(11)]
        response = self.client.get(self.url)
        visible = list(response.context["recent_events"])
        self.assertEqual(len(visible), 8)
        self.assertEqual([e.pk for e in visible], [e.pk for e in reversed(events[-8:])])

    def test_preview_remains_read_only_with_real_dossier(self):
        event = self.add_event()
        response = self.client.get(self.url, {"event": event.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aperçu affiché")
        self.assertContains(response, "400 € TTC")
        self.assertContains(response, "Ouvrir l'aperçu PDF")
        self.assertContains(response, "aucun e-mail n'est envoyé")
        event.refresh_from_db()
        self.assertEqual(event.prix_brut, 0)
        self.assertFalse(AutoQuoteLog.objects.exists())
        self.assertFalse(AutoQuoteSettings.objects.get(pk=1).enabled)

    def test_empty_recent_list_does_not_break_dashboard(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aucune demande enregistrée pour le moment.")
        self.assertNotContains(response, "Voir le calcul")
