"""Régression : ne plus perdre les demandes à l'étape de confirmation."""
import io
import importlib
from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.utils import timezone

from app.models import Event
from app.views.frontend_views import FORM_PENDING, confirmation, demande_devis

frontend_module = importlib.import_module('app.views.frontend_views')


def payload():
    return {
        "nom": "Essai", "prenom": "Camille",
        "mail": "client@example.invalid", "numero_telephone": "0612345678",
        "date_evenement": str(timezone.localdate() + timedelta(days=60)),
        "adresse_evenement": "1 rue du Test", "ville_evenement": "Paris",
        "code_postal_evenement": "75001", "client_how_find": "INSTAGRAM",
        "selectedImages": "Photobooth", "selectedOption": "",
        "magnets_range": "0", "PorteCles_range": "0",
        "MagnetsSimple_range": "0", "livraison": "1",
        "heure_range": "5",
    }


class QuoteCaptureTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.session = {}

    def first_step(self, data=None):
        request = self.factory.post("/", data or payload())
        request.session = self.session
        return demande_devis(request)

    def final_step(self):
        request = self.factory.post("/confirmation/", {})
        request.session = self.session
        with patch.object(frontend_module, "create_google_contact"), \
             patch.object(frontend_module, "create_card", return_value="test-card"), \
             patch.object(frontend_module, "process_instant_quote", return_value=False):
            return confirmation(request)

    def test_first_step_persists_single_lead_before_second_confirmation(self):
        response = self.first_step()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.get()
        self.assertEqual(event.history_status, FORM_PENDING)
        self.assertIsNone(event.event_token)
        self.assertEqual(event.client.mail, "client@example.invalid")
        self.assertEqual(event.event_product.photobooth, True)
        self.assertEqual(self.session["draft_event_id"], event.id)

        final = self.final_step()
        self.assertEqual(final.status_code, 302)
        self.assertEqual(Event.objects.count(), 1)
        event.refresh_from_db()
        self.assertTrue(event.event_token)
        self.assertEqual(event.history_status, "Formulaire : demande confirmée")
        self.assertNotIn("draft_event_id", self.session)

        repeat = self.final_step()
        self.assertEqual(repeat.status_code, 302)
        self.assertEqual(Event.objects.count(), 1)

    def test_editing_previous_step_updates_same_lead(self):
        self.first_step()
        previous = Event.objects.get()
        number = previous.num_devis
        edited = payload()
        edited.update(nom="EssaiModifié", ville_evenement="Lyon",
                      selectedImages="Miroirbooth")
        self.assertEqual(self.first_step(edited).status_code, 200)
        self.assertEqual(Event.objects.count(), 1)
        previous.refresh_from_db()
        previous.client.refresh_from_db()
        previous.event_product.refresh_from_db()
        previous.event_details.refresh_from_db()
        self.assertEqual(previous.client.nom, "Camille EssaiModifié")
        self.assertEqual(previous.event_details.ville_evenement, "Lyon")
        self.assertTrue(previous.event_product.miroirbooth)
        self.assertFalse(previous.event_product.photobooth)
        self.assertEqual(previous.num_devis, number)

    def test_invalid_form_is_rejected_without_creating_ghosts(self):
        invalid = payload()
        invalid["mail"] = "invalid"
        self.assertEqual(self.first_step(invalid).status_code, 400)
        self.assertEqual(Event.objects.count(), 0)
        request = self.factory.post("/confirmation/", {})
        request.session = {}
        self.assertEqual(confirmation(request).status_code, 400)

    def test_abandoned_lead_alert_only_once_then_confirmation_still_works(self):
        self.first_step()
        event = Event.objects.get()
        Event.objects.filter(pk=event.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        with patch("app.management.commands.notify_pending_quotes.send_admin_alert", return_value=True) as send:
            call_command("notify_pending_quotes", stdout=io.StringIO())
            self.assertEqual(send.call_count, 1)
            call_command("notify_pending_quotes", stdout=io.StringIO())
            self.assertEqual(send.call_count, 1)
        self.assertIn("équipe alertée", Event.objects.get(pk=event.pk).history_status)
        self.assertEqual(self.final_step().status_code, 302)
        self.assertEqual(Event.objects.count(), 1)

    def test_abandoned_notification_retries_if_admin_mail_fails(self):
        self.first_step()
        event = Event.objects.get()
        Event.objects.filter(pk=event.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        with patch("app.management.commands.notify_pending_quotes.send_admin_alert", return_value=False):
            call_command("notify_pending_quotes", stdout=io.StringIO(), stderr=io.StringIO())
        self.assertEqual(Event.objects.get(pk=event.pk).history_status, FORM_PENDING)
