from datetime import datetime, timedelta, timezone as datetime_timezone
from io import BytesIO
from smtplib import SMTPDataError, SMTPServerDisconnected
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bs4 import BeautifulSoup
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client as Browser, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import Client, Event, EventDetails
from .models import Attribution, Campaign, Configuration, Consent, Delivery, Template, Unsubscribe
from .services import build_message, eligible, record_quote, smtp_settings, still_eligible
from .views import metrics


SMTP_ENV = {
    "NEWSLETTER_HOST": "smtp.example.invalid",
    "NEWSLETTER_USER": "newsletter-test",
    "NEWSLETTER_PASSWORD": "fake-test-password",
    "NEWSLETTER_PUBLIC_URL": "https://crm.example.invalid",
    "NEWSLETTER_PORT": "587",
}


@override_settings(ALLOWED_HOSTS=["testserver", "crm.example.invalid"])
class NewsletterTests(TestCase):
    def setUp(self):
        self.config = Configuration.objects.create(
            pk=1, enabled=True, sender="marketing@example.invalid", hourly_limit=1
        )
        self.staff = get_user_model().objects.create_user(username="newsletter", is_staff=True)
        self.client.force_login(self.staff)
        self.public = Browser(enforce_csrf_checks=True)
        environment = patch.dict("os.environ", SMTP_ENV)
        environment.start()
        self.addCleanup(environment.stop)
        smtp = patch("newsletter.services.EmailBackend", autospec=True)
        self.smtp = smtp.start()
        self.addCleanup(smtp.stop)
        self.messages = self.smtp.return_value.send_messages
        self.messages.return_value = 1
        lock_dir = TemporaryDirectory()
        self.addCleanup(lock_dir.cleanup)
        self.lock_file = f"{lock_dir.name}/newsletter.lock"

    def contact(self, email, business=False, consent=True, authorized=True):
        contact = Client.objects.create(
            mail=email, nom="Test", numero_telephone="0600000000",
            raison_sociale=business, autorisation_mail=authorized,
        )
        if consent:
            Consent.objects.create(client=contact, email=email.lower().strip())
        return contact

    def run_worker(self):
        call_command("send_newsletters", "--lock-file", self.lock_file)

    def campaign(self, scheduled_at=None, queued=False):
        return Campaign.objects.create(
            audience=Campaign.Audience.ALL, name="Exemple", subject="Infos",
            html='<html><body><a href="https://crm.example.invalid/">Devis</a></body></html>',
            step=4, scheduled_at=scheduled_at,
            status=Campaign.Status.QUEUED if queued else Campaign.Status.DRAFT,
            confirmed_at=timezone.now() if queued else None,
        )

    def test_audience_requires_explicit_consent_and_deduplicates(self):
        self.contact(" ALICE@EXAMPLE.INVALID ", business=True)
        self.contact("alice@example.invalid", business=True)
        self.contact("sans-consentement@example.invalid", consent=False)
        self.contact("refus@example.invalid", authorized=False)
        bob = self.contact("bob@example.invalid")
        updated = self.contact("ancienne@example.invalid")
        updated.mail = "nouvelle@example.invalid"
        updated.save(update_fields=["mail"])
        self.assertEqual(eligible(), {"alice@example.invalid", bob.mail})
        self.assertEqual(eligible(Campaign.Audience.BUSINESS), {"alice@example.invalid"})
        self.assertEqual(eligible(Campaign.Audience.INDIVIDUAL), {bob.mail})
        Unsubscribe.objects.create(email="alice@example.invalid")
        self.assertEqual(eligible(), {bob.mail})

    def test_crm_authorized_individuals_are_deduplicated_and_rechecked(self):
        individual = self.contact("  ALICE@EXAMPLE.INVALID ", consent=False)
        duplicate = self.contact("alice@example.invalid", consent=False)
        self.contact("business@example.invalid", business=True, consent=False)
        self.contact("refus@example.invalid", authorized=False, consent=False)
        self.contact("adresse-invalide", consent=False)
        self.contact("stop@example.invalid", consent=False)
        Unsubscribe.objects.create(email="stop@example.invalid")
        audience = Campaign.Audience.CRM_ALLOWED

        self.assertEqual(eligible(audience), {"alice@example.invalid"})
        self.assertEqual(eligible(), set())
        self.assertTrue(still_eligible("alice@example.invalid", audience))
        self.assertFalse(still_eligible("stop@example.invalid", audience))
        duplicate.delete()
        individual.autorisation_mail = False
        individual.save(update_fields=["autorisation_mail"])
        self.assertFalse(still_eligible("alice@example.invalid", audience))

    def test_campaign_editor_saves_tests_and_requires_manual_confirmation(self):
        anonymous = Browser()
        dashboard = reverse("newsletter:dashboard")
        self.assertEqual(anonymous.get(dashboard).status_code, 302)
        self.assertContains(self.client.get(dashboard), "Contacts éligibles")
        template_url = reverse("newsletter:templates")
        upload = SimpleUploadedFile("test.html", b"<html><p>Bonjour</p></html>")
        self.assertRedirects(self.client.post(template_url, {"name": "Démo", "upload": upload}), template_url)
        template = Template.objects.get()
        self.client.post(reverse("newsletter:duplicate", args=[template.pk]))
        self.assertEqual(Template.objects.count(), 2)

        self.contact("contact@example.invalid")
        data = {"audience": "all", "mode": "now", "name": "Infos", "subject": "Bonjour"}
        response = self.client.post(reverse("newsletter:create"), {
            **data, "template": template.pk, "action": "save",
        })
        campaign = Campaign.objects.get()
        edit = reverse("newsletter:edit", args=[campaign.pk])
        self.assertRedirects(response, edit)
        self.assertEqual(campaign.html, template.html)
        self.assertContains(self.client.get(edit), "Aperçu mobile")
        response = self.client.get(reverse("newsletter:preview", args=[campaign.pk]))
        self.assertContains(response, "Bonjour")
        self.assertIn("sandbox", response["Content-Security-Policy"])
        data.update(html=campaign.html)
        response = self.client.post(edit, {
            **data, "action": "test", "email": "equipe@example.invalid",
        }, follow=True)
        self.assertContains(response, "Email de test accepté")
        message = self.messages.call_args.args[0][0]
        self.assertEqual(message.to, ["equipe@example.invalid"])
        self.assertEqual(message.subject, "[TEST] Bonjour")
        self.assertFalse(message.extra_headers)
        self.assertFalse(Delivery.objects.exists())
        response = self.client.post(edit, {**data, "action": "confirm"}, follow=True)
        self.assertContains(response, "Cochez la confirmation")
        self.assertFalse(Delivery.objects.exists())
        detail = reverse("newsletter:detail", args=[campaign.pk])
        for _ in range(2):
            self.assertRedirects(self.client.post(edit, {**data, "action": "confirm", "confirm": "yes"}), detail)
        self.assertEqual(Delivery.objects.get().email, "contact@example.invalid")
        self.run_worker()
        self.assertEqual(Delivery.objects.get().status, Delivery.Status.PENDING)
        self.messages.assert_called_once()

    def test_existing_partial_draft_reopens_and_keeps_import_on_invalid_date(self):
        campaign = Campaign.objects.create(audience="all", name="Ancien brouillon", step=2)
        edit = reverse("newsletter:edit", args=[campaign.pk])
        self.assertRedirects(self.client.get(f"/backend/newsletter/campagnes/{campaign.pk}/etape/2/"), edit)
        data = {"audience": "all", "mode": "later", "name": campaign.name, "subject": "Sujet"}
        html = "<h1>Contenu importé</h1>"
        response = self.client.post(edit, {
            **data, "upload": SimpleUploadedFile("mail.html", html.encode()),
        })
        self.assertContains(response, "Indiquez la date et l’heure")
        retry = BeautifulSoup(response.content, "html.parser")
        self.assertEqual(retry.find("textarea", {"name": "html"}).text.strip(), html)
        response = self.client.post(edit, {**data, "html": html, "mode": "now", "action": "save"})
        self.assertRedirects(response, edit)
        campaign.refresh_from_db()
        self.assertEqual(campaign.html, html)
        self.assertEqual(campaign.status, Campaign.Status.DRAFT)

    def test_history_detail_only_shows_campaign_totals(self):
        now = timezone.now()
        campaign = self.campaign(datetime(2026, 11, 27, 17, tzinfo=datetime_timezone.utc), queued=True)
        campaign.audience = Campaign.Audience.CRM_ALLOWED
        campaign.save(update_fields=["audience"])
        history = self.client.get(reverse("newsletter:history"))
        self.assertContains(history, campaign.subject)
        self.assertContains(history, "27/11/2026 à 18:00")
        sent = Delivery.objects.create(
            campaign=campaign, email="visible-only-in-db@example.invalid", status=Delivery.Status.SENT,
            attempted_at=now, sent_at=now, opened_at=now, clicked_at=now,
        )
        Unsubscribe.objects.create(email=sent.email, delivery=sent)
        Delivery.objects.create(
            campaign=campaign, email="failed@example.invalid", status=Delivery.Status.FAILED,
            attempted_at=now, error="Internal SMTP diagnostic",
        )
        Delivery.objects.create(campaign=campaign, email="pending@example.invalid")

        response = self.client.get(reverse("newsletter:detail", args=[campaign.pk]))
        self.assertContains(response, "Résumé des envois")
        self.assertContains(response, campaign.subject)
        self.assertContains(response, "En file")
        self.assertContains(response, "Particuliers autorisés (CRM)")
        self.assertContains(response, "27/11/2026 à 18:00 (Paris)")
        self.assertContains(response, "Acceptés par le relais SMTP")
        self.assertNotContains(response, "@example.invalid")
        self.assertNotContains(response, "Internal SMTP diagnostic")
        self.assertEqual(response.context["delivery_summary"], {
            "recipients": 3, "attempted": 2, "pending": 1, "failed": 1, "uncertain": 0, "excluded": 0,
        })
        self.assertEqual(
            [response.context["stats"][key] for key in ("sent", "opened", "clicked", "unsubscribed")],
            [1, 1, 1, 1],
        )

    def test_staff_can_rename_campaign_from_history(self):
        now = timezone.now()
        campaign = self.campaign(now, queued=True)
        url = reverse("newsletter:detail", args=[campaign.pk])
        self.assertEqual(Browser().post(url, {"name": "Intrus"}).status_code, 302)
        response = self.client.post(url, {"name": " "})
        self.assertTrue(response.context["rename_form"].errors)
        for status in (Campaign.Status.QUEUED, Campaign.Status.FINISHED):
            Campaign.objects.filter(pk=campaign.pk).update(status=status)
            self.assertRedirects(self.client.post(url, {
                "name": f"Campagne {status}", "subject": "À ignorer",
            }), url)
            campaign.refresh_from_db()
            self.assertEqual(campaign.name, f"Campagne {status}")
            self.assertEqual(campaign.status, status)
            self.assertEqual(campaign.subject, "Infos")
            self.assertEqual(campaign.scheduled_at, now)

    def test_staff_image_upload_has_a_public_immutable_url(self):
        url = reverse("newsletter:images")
        anonymous = Browser()
        self.assertEqual(anonymous.get(url).status_code, 302)
        with TemporaryDirectory() as directory, patch.dict("os.environ", {"NEWSLETTER_IMAGE_ROOT": directory}):
            self.assertContains(self.client.get(url), "Aucune image importée")
            invalid = SimpleUploadedFile("invalide.png", b"<svg />", content_type="image/png")
            response = self.client.post(url, {"image": invalid})
            self.assertContains(response, "Aucune image importée")
            data = BytesIO()
            Image.new("RGB", (2, 2)).save(data, "PNG")
            upload = SimpleUploadedFile("Photo événement.png", data.getvalue(), content_type="image/png")
            self.assertRedirects(self.client.post(url, {"image": upload}), url)
            page = BeautifulSoup(self.client.get(url).content, "html.parser")
            image_url = page.select_one("img.card-img-top")["src"]
            self.assertTrue(image_url.startswith("https://crm.example.invalid/newsletter/image/"))
            public = anonymous.get(image_url)
            self.assertEqual(public.status_code, 200)
            self.assertEqual(public["Content-Type"], "image/png")
            self.assertEqual(public["X-Content-Type-Options"], "nosniff")
            self.assertEqual(b"".join(public.streaming_content), data.getvalue())
            public.close()

    def test_smtp_test_tab_sends_only_to_the_configured_recipient(self):
        url = reverse("newsletter:test")
        self.assertEqual(self.public.get(url).status_code, 302)
        self.assertContains(self.client.get(url), "faure_stephane@hotmail.fr")
        self.messages.assert_not_called()
        response = self.client.post(url, {"email": "other@example.invalid"}, follow=True)
        self.assertContains(response, "Email de test accepté")
        message = self.messages.call_args.args[0][0]
        self.assertEqual(message.to, ["faure_stephane@hotmail.fr"])
        self.assertIn("Vérification SMTP", message.subject)
        self.client.get(url)
        self.messages.assert_called_once()
        self.assertFalse(Delivery.objects.exists())
        self.assertFalse(Campaign.objects.exists())

    def test_smtp_test_tab_can_use_campaign_content(self):
        campaign = self.campaign()
        url = reverse("newsletter:test")
        self.client.post(url, {"campaign": campaign.pk})
        message = self.messages.call_args.args[0][0]
        self.assertEqual(message.to, ["faure_stephane@hotmail.fr"])
        self.assertEqual(message.alternatives[0][0], campaign.html)
        self.assertFalse(Delivery.objects.exists())

    def test_worker_checks_schedule_enabled_consent_and_rolling_limit(self):
        campaign = self.campaign(timezone.now() + timedelta(minutes=5), queued=True)
        for email in ("a@example.invalid", "b@example.invalid", "c@example.invalid"):
            self.contact(email)
            Delivery.objects.create(campaign=campaign, email=email)
        self.run_worker()
        self.messages.assert_not_called()
        Campaign.objects.filter(pk=campaign.pk).update(scheduled_at=timezone.now())
        Configuration.objects.filter(pk=1).update(enabled=False)
        self.run_worker()
        self.messages.assert_not_called()
        Configuration.objects.filter(pk=1).update(enabled=True)
        Unsubscribe.objects.create(email="a@example.invalid")
        self.run_worker()
        self.run_worker()
        self.messages.assert_called_once()
        self.assertEqual(Delivery.objects.get(email="a@example.invalid").status, Delivery.Status.EXCLUDED)
        sent = Delivery.objects.get(status=Delivery.Status.SENT)
        message = self.messages.call_args.args[0][0]
        self.assertEqual(message.to, [sent.email])
        self.assertIn(str(sent.token), message.extra_headers["List-Unsubscribe"])
        self.assertTrue(self.smtp.call_args.kwargs["use_tls"])
        Delivery.objects.filter(pk=sent.pk).update(attempted_at=timezone.now() - timedelta(hours=1))
        self.run_worker()
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, Campaign.Status.FINISHED)
        self.assertEqual(self.messages.call_count, 2)

    def test_smtp_failure_and_interruption_are_visible_without_retry(self):
        self.config.hourly_limit = 5
        self.config.save()
        campaign = self.campaign(timezone.now(), queued=True)
        for email in ("a@example.invalid", "b@example.invalid", "c@example.invalid"):
            self.contact(email)
            Delivery.objects.create(campaign=campaign, email=email)
        Delivery.objects.filter(email="a@example.invalid").update(status=Delivery.Status.SENDING)
        self.messages.side_effect = [SMTPDataError(550, b"rejected"), SMTPServerDisconnected()]
        self.run_worker()
        self.run_worker()
        self.assertEqual(self.messages.call_count, 2)
        self.assertEqual(dict(Delivery.objects.values_list("email", "status")), {
            "a@example.invalid": Delivery.Status.UNCERTAIN,
            "b@example.invalid": Delivery.Status.FAILED,
            "c@example.invalid": Delivery.Status.UNCERTAIN,
        })

    def test_tracking_attribution_and_unsubscribe_leave_crm_consent_untouched(self):
        contact = self.contact("contact@example.invalid")
        details = EventDetails.objects.create(
            date_evenement=timezone.localdate(), adresse_evenement="1 rue Test",
            ville_evenement="Paris", code_postal_evenement=75001,
        )
        event = Event.objects.create(
            client=contact, event_details=details, prix_brut=500,
            prix_valided=500, signer_at=timezone.now(),
        )
        campaign = self.campaign()
        delivery = Delivery.objects.create(campaign=campaign, email=contact.mail,
                                           status=Delivery.Status.SENT, sent_at=timezone.now())
        origin = {"HTTP_HOST": "crm.example.invalid", "secure": True}
        pixel = reverse("newsletter_public:open", args=[delivery.token])
        self.assertEqual(self.public.get(pixel, **origin)["Content-Type"], "image/gif")
        unsubscribe = reverse("newsletter_public:unsubscribe", args=[delivery.token])
        self.assertEqual(self.public.get(unsubscribe, **origin).status_code, 200)
        self.assertFalse(Unsubscribe.objects.exists())
        message = build_message(campaign, delivery.email, self.config, smtp_settings(), delivery)
        click_url = BeautifulSoup(message.alternatives[0][0], "html.parser").a["href"]
        self.assertEqual(self.public.get(click_url, **origin)["Location"], "https://crm.example.invalid/")
        invalid_url = reverse("newsletter_public:click", args=[delivery.token, "invalid"])
        self.assertEqual(self.public.get(invalid_url, **origin).status_code, 404)
        record_quote(event, False, self.public.session["newsletter_click"])
        self.assertEqual(Attribution.objects.get().delivery, delivery)
        for _ in range(2):
            response = self.public.post(unsubscribe, {"List-Unsubscribe": "One-Click"}, **origin)
            self.assertEqual(response.status_code, 204)
        contact.refresh_from_db()
        self.assertTrue(contact.autorisation_mail)
        self.assertEqual(eligible(), set())
        self.assertEqual(metrics(campaign.deliveries.all()), {
            "sent": 1, "opened": 1, "clicked": 1, "opened_rate": 100, "clicked_rate": 100,
            "requests": 1, "quotes": 1, "revenue": 500, "unsubscribed": 1,
        })
