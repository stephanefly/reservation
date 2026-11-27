"""Régression : ne plus perdre les demandes à l'étape de confirmation."""
import io
import importlib
from datetime import datetime, timedelta, timezone as datetime_timezone
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils import timezone

from app.models import Event
from newsletter.models import NewsletterSubscriber, QuoteEmailConsent
from quote_control.models import AutoQuoteLog, CatalogEntry
from app.views.frontend_views import FORM_PENDING, confirmation, demande_devis

frontend_module = importlib.import_module('app.views.frontend_views')


class BlackFridayBannerTests(SimpleTestCase):
    def test_campaign_visibility_uses_paris_midnight_and_expires(self):
        for instant, visible in [
            (datetime(2026, 11, 24, 22, 59), False),
            (datetime(2026, 11, 24, 23, 0), True),
            (datetime(2026, 11, 30, 22, 59), True),
            (datetime(2026, 11, 30, 23, 0), False),
            (datetime(2027, 11, 26, 12, 0), False),
        ]:
            with self.subTest(instant=instant), patch.object(
                frontend_module.timezone, 'now',
                return_value=instant.replace(tzinfo=datetime_timezone.utc),
            ):
                request = RequestFactory().get('/')
                request.session = {}
                response = demande_devis(request)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertEqual('id="black-friday-title"' in html, visible)
                self.assertEqual('Composez votre animation événementielle' in html, not visible)
                self.assertIn('id="monFormulaire"', html)


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
        "quote_email_consent": "yes",
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
        self.assertTrue(QuoteEmailConsent.objects.filter(event_id=event.pk).exists())
        self.assertFalse(NewsletterSubscriber.objects.exists())

        final = self.final_step()
        self.assertEqual(final.status_code, 302)
        self.assertEqual(Event.objects.count(), 1)
        event.refresh_from_db()
        self.assertTrue(event.event_token)
        self.assertEqual(event.history_status, "Formulaire : demande confirmée")
        self.assertNotIn("draft_event_id", self.session)
        self.assertFalse(NewsletterSubscriber.objects.exists())

        repeat = self.final_step()
        self.assertEqual(repeat.status_code, 302)
        self.assertEqual(Event.objects.count(), 1)

    def test_quote_consent_is_required(self):
        for value in (None, "no", "false", "on"):
            data = payload()
            if value is None:
                data.pop("quote_email_consent")
            else:
                data["quote_email_consent"] = value
            self.assertEqual(self.first_step(data).status_code, 400)
        self.assertFalse(Event.objects.exists())
        self.assertFalse(QuoteEmailConsent.objects.exists())

    def test_newsletter_opt_in_requires_confirmed_explicit_acceptance(self):
        data = payload()
        data["newsletter_consent"] = "yes"
        self.assertEqual(self.first_step(data).status_code, 200)
        self.assertFalse(NewsletterSubscriber.objects.exists())
        self.assertEqual(self.final_step().status_code, 302)
        subscriber = NewsletterSubscriber.subscribed().get()
        self.assertEqual(subscriber.email, data["mail"])
        self.assertEqual(subscriber.event_id, Event.objects.get().pk)
        self.assertEqual(self.final_step().status_code, 302)
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)

    def test_newsletter_unchecked_after_edit_does_not_subscribe(self):
        data = payload()
        data["newsletter_consent"] = "yes"
        self.first_step(data)
        self.first_step(payload())
        self.assertEqual(self.final_step().status_code, 302)
        self.assertFalse(NewsletterSubscriber.objects.exists())

    def test_newsletter_opt_in_can_be_revoked(self):
        data = payload()
        data["newsletter_consent"] = "yes"
        self.first_step(data)
        self.final_step()
        event = Event.objects.get()
        frontend_module.desabonner(self.factory.get("/"), event.event_token)
        self.assertFalse(NewsletterSubscriber.subscribed().exists())

    def test_newsletter_deduplicates_emails_and_keeps_existing_subscriber(self):
        data = payload()
        data["newsletter_consent"] = "yes"
        self.first_step(data)
        self.final_step()
        self.session = {}
        data["mail"] = data["mail"].upper()
        self.first_step(data)
        self.final_step()
        self.assertEqual(NewsletterSubscriber.subscribed().count(), 1)
        self.session = {}
        self.first_step(payload())
        self.final_step()
        self.assertEqual(NewsletterSubscriber.subscribed().count(), 1)

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

    def test_confirmation_persists_options_and_blocks_automatic_mail(self):
        CatalogEntry.objects.filter(kind="product", code="photobooth").update(auto_enabled=True)
        data = payload()
        data.update(selectedOption="Phonebooth, VideoLivreOr", magnets_range="50",
                    PorteCles_range="100", MagnetsSimple_range="150",
                    avec_panneaux="on", panneaux_xxl="4")
        self.assertEqual(self.first_step(data).status_code, 200)
        request = self.factory.get("/")
        request.session = self.session
        html = demande_devis(request).content.decode()
        self.assertIn('value="50" name="magnets_range"', html)
        self.assertIn('value="100" name="PorteCles_range"', html)
        self.assertIn('value="150" name="MagnetsSimple_range"', html)
        event = Event.objects.get()
        # Une incohérence du brouillon ne doit jamais effacer la sélection confirmée.
        event.event_option.Phonebooth = False
        event.event_option.save()
        request = self.factory.post("/confirmation/", {})
        request.session = self.session
        with patch.object(frontend_module, "create_google_contact"), \
             patch.object(frontend_module, "create_card", return_value="test-card"), \
             patch.object(frontend_module, "send_mail_event") as sender:
            self.assertEqual(confirmation(request).status_code, 302)
            sender.assert_not_called()
        event.refresh_from_db()
        option = event.event_option
        self.assertTrue(option.Phonebooth and option.VideoLivreOr)
        self.assertEqual((option.magnets, option.PorteCles, option.MagnetsSimple, option.panneaux_xxl), (50, 100, 150, 4))
        self.assertEqual(event.status, "Initied")
        log = AutoQuoteLog.objects.get(event_id=event.pk)
        self.assertEqual(log.outcome, "manual")
        for code in ("Phonebooth", "VideoLivreOr", "magnets=50", "PorteCles=100", "MagnetsSimple=150", "panneaux_xxl=4"):
            self.assertIn(code, log.reason)

    def test_final_guard_blocks_even_if_engine_returns_eligible(self):
        from quote_control.service import process_instant_quote
        from app.module.data_bdd.instant_quote import preparer_et_envoyer_devis
        CatalogEntry.objects.filter(kind="product", code="photobooth").update(auto_enabled=True)
        data = payload()
        data.update(selectedOption="LivreOr")
        self.first_step(data)
        event = Event.objects.get()
        fake_eligible = {"eligible": True, "pack": None, "amount": 400, "label": "Photobooth", "calculation": {}}
        with patch("quote_control.service.analyse_quote", return_value=fake_eligible), \
             patch.object(frontend_module, "send_mail_event") as sender:
            self.assertFalse(process_instant_quote(event, sender))
            self.assertFalse(preparer_et_envoyer_devis(event, sender))
            sender.assert_not_called()
        self.assertEqual(AutoQuoteLog.objects.filter(event_id=event.pk, outcome="manual").count(), 2)

    def test_manual_mail_remains_available_for_request_with_options(self):
        from app.views import backend_views
        data = payload()
        data.update(selectedOption="LivreOr")
        self.first_step(data)
        event = Event.objects.get()
        with patch.object(backend_views, "send_mail_event", return_value=True) as sender:
            response = backend_views.envoi_mail_devis(self.factory.post("/"), event.pk)
            self.assertEqual(response.status_code, 200)
            sender.assert_called_once()
        event.refresh_from_db()
        self.assertEqual(event.status, "Sended")

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
