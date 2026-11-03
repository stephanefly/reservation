import io
import smtplib
import tempfile
from email import message_from_string
from email.mime.text import MIMEText
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import path

from app.models import Client, EmailTracking, EmailMailboxCheck, Event, EventDetails, EventOption
from app.module.mail.bounces import apply_report, reports
from app.module.mail.delivery import begin_delivery, submit
from app.views.email_delivery_views import graph_email_delivery


urlpatterns = [path("login/", lambda request: HttpResponse("Login"), name="login"),
               path("backend/graph/email-delivery/", graph_email_delivery, name="graph_email_delivery"),
               path("event/<int:id>/", lambda request, id: HttpResponse("Event"), name="info_event")]


def dsn(message_id, recipient="client@example.invalid", action="failed", code="5.1.1"):
    return (f'MIME-Version: 1.0\r\nContent-Type: multipart/report; report-type=delivery-status; boundary="test"\r\n\r\n'
            f'--test\r\nContent-Type: text/plain\r\n\r\nDelivery report\r\n'
            f'--test\r\nContent-Type: message/delivery-status\r\n\r\nReporting-MTA: dns; test.invalid\r\n\r\n'
            f'Final-Recipient: rfc822; {recipient}\r\nAction: {action}\r\nStatus: {code}\r\n\r\n'
            f'--test\r\nContent-Type: text/rfc822-headers\r\n\r\nMessage-ID: {message_id}\r\nTo: {recipient}\r\n\r\n--test--\r\n').encode()


@override_settings(ROOT_URLCONF=__name__, MAIL_MYSELFIEBOOTH="sender@example.invalid", MP="fake-test-password", MAIL_BCC="archive@example.invalid")
class EmailTrackingTests(TestCase):
    def setUp(self):
        person = Client.objects.create(nom="Client test", mail="client@example.invalid", numero_telephone="01", raison_sociale=True)
        details = EventDetails.objects.create(date_evenement="2026-11-03", adresse_evenement="Test", ville_evenement="Paris", code_postal_evenement=75001)
        self.event = Event.objects.create(client=person, event_details=details, prix_brut=500)

    def delivery(self):
        return begin_delivery(self.event, "validation")

    def smtp(self, refused=None):
        smtp = Mock()
        smtp.has_extn.return_value = False
        smtp.sendmail.return_value = refused or {}
        return smtp

    def test_accepted_and_copy_refused_are_separate(self):
        delivery = self.delivery()
        server = self.smtp({"archive@example.invalid": (550, b"No mailbox")})
        with patch("app.module.mail.delivery.smtplib.SMTP_SSL", return_value=server):
            self.assertTrue(submit(delivery, MIMEText("Test"), ["archive@example.invalid"]))
        delivery.refresh_from_db()
        self.assertEqual(delivery.delivery_status, "accepted")
        self.assertTrue(delivery.copy_refused)
        self.assertIsNotNone(delivery.accepted_at)
        message = message_from_string(server.sendmail.call_args.args[2])
        self.assertEqual(message["Message-ID"], delivery.message_id)
        self.assertIsNotNone(message["Date"])

    def test_refused_client_is_not_hidden_by_successful_bcc(self):
        delivery = self.delivery()
        server = self.smtp({"client@example.invalid": (550, b"Unknown recipient")})
        with patch("app.module.mail.delivery.smtplib.SMTP_SSL", return_value=server):
            with self.assertRaises(smtplib.SMTPRecipientsRefused):
                submit(delivery, MIMEText("Test"), ["archive@example.invalid"])
        delivery.refresh_from_db()
        self.assertEqual(delivery.delivery_status, "refused")
        self.assertEqual(delivery.smtp_code, 550)
        self.assertIsNone(delivery.accepted_at)

    def test_all_recipients_refused(self):
        delivery = self.delivery()
        server = self.smtp()
        server.sendmail.side_effect = smtplib.SMTPRecipientsRefused({delivery.recipient: (551, b"No")})
        with patch("app.module.mail.delivery.smtplib.SMTP_SSL", return_value=server), self.assertRaises(smtplib.SMTPRecipientsRefused):
            submit(delivery, MIMEText("Test"))
        delivery.refresh_from_db()
        self.assertEqual((delivery.delivery_status, delivery.smtp_code), ("refused", 551))

    def test_authentication_error_and_ambiguous_timeout(self):
        for after_login, expected in ((False, "error"), (True, "unknown")):
            delivery = self.delivery()
            server = self.smtp()
            if after_login:
                server.sendmail.side_effect = TimeoutError("socket closed")
            else:
                server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"secret must not be saved")
            with patch("app.module.mail.delivery.smtplib.SMTP_SSL", return_value=server), self.assertRaises((OSError, smtplib.SMTPException)):
                submit(delivery, MIMEText("Test"))
            delivery.refresh_from_db()
            self.assertEqual(delivery.delivery_status, expected)
            self.assertNotIn("secret", delivery.diagnostic)

    def test_quit_failure_does_not_turn_acceptance_into_failure(self):
        delivery = self.delivery()
        server = self.smtp()
        server.quit.side_effect = smtplib.SMTPServerDisconnected("closed")
        with patch("app.module.mail.delivery.smtplib.SMTP_SSL", return_value=server):
            self.assertTrue(submit(delivery, MIMEText("Test")))
        delivery.refresh_from_db()
        self.assertEqual(delivery.delivery_status, "accepted")

    def test_dsn_options_are_requested_only_when_supported(self):
        delivery = self.delivery()
        server = self.smtp()
        server.has_extn.return_value = True
        with patch("app.module.mail.delivery.smtplib.SMTP_SSL", return_value=server):
            submit(delivery, MIMEText("Test"))
        self.assertEqual(server.sendmail.call_args.kwargs["rcpt_options"], ["NOTIFY=SUCCESS,FAILURE,DELAY"])

    def test_dsn_matching_requires_message_and_recipient_and_is_idempotent(self):
        delivery = self.delivery()
        EmailTracking.objects.filter(pk=delivery.pk).update(delivery_status="accepted")
        self.assertEqual(apply_report(dsn(delivery.message_id, recipient="other@example.invalid")), (0, 1))
        self.assertEqual(apply_report(dsn("<another@example.invalid>")), (0, 1))
        self.assertEqual(apply_report(dsn(delivery.message_id)), (1, 0))
        delivery.refresh_from_db()
        self.assertEqual(delivery.delivery_status, "bounced")
        feedback_at = delivery.feedback_at
        apply_report(dsn(delivery.message_id))
        apply_report(dsn(delivery.message_id, action="delivered", code="2.0.0"))
        delivery.refresh_from_db()
        self.assertEqual(delivery.delivery_status, "bounced")
        self.assertEqual(delivery.feedback_at, feedback_at)
        self.assertEqual(reports(b"Subject: Mail delivery failed\r\n\r\nJust a normal message"), [])
        self.assertEqual(reports(dsn(delivery.message_id, action="failed", code="2.0.0")), [])

    def test_delayed_report_can_become_delivered(self):
        delivery = self.delivery()
        EmailTracking.objects.filter(pk=delivery.pk).update(delivery_status="accepted")
        apply_report(dsn(delivery.message_id, action="delayed", code="4.2.0"))
        delivery.refresh_from_db()
        self.assertEqual(delivery.delivery_status, "delayed")
        apply_report(dsn(delivery.message_id, action="delivered", code="2.0.0"))
        delivery.refresh_from_db()
        self.assertEqual(delivery.delivery_status, "delivered")

    def test_mailbox_read_is_read_only_and_keeps_messages_unread(self):
        delivery = self.delivery()
        EmailTracking.objects.filter(pk=delivery.pk).update(delivery_status="accepted")
        raw = dsn(delivery.message_id)
        mailbox = Mock()
        mailbox.select.return_value = ("OK", [b"1"])
        mailbox.uid.side_effect = [("OK", [b"42"]), ("OK", [b"42 (RFC822.SIZE 900)"]), ("OK", [(b"42 BODY", raw), b")"])]
        with patch("app.management.commands.sync_email_bounces.imaplib.IMAP4_SSL", return_value=mailbox):
            call_command("sync_email_bounces", stdout=io.StringIO())
        mailbox.select.assert_called_once_with("INBOX", readonly=True)
        self.assertEqual(mailbox.uid.call_args_list[-1].args, ("fetch", b"42", "(BODY.PEEK[])"))
        self.assertFalse(mailbox.store.called)
        self.assertFalse(mailbox.expunge.called)
        check = EmailMailboxCheck.objects.get(key="ionos")
        self.assertTrue(check.success)
        self.assertEqual(check.matched, 1)

    def test_mailbox_failure_is_visible_without_exposing_password(self):
        mailbox = Mock()
        mailbox.login.side_effect = OSError("fake-test-password")
        with patch("app.management.commands.sync_email_bounces.imaplib.IMAP4_SSL", return_value=mailbox), self.assertRaises(CommandError):
            call_command("sync_email_bounces", stdout=io.StringIO())
        check = EmailMailboxCheck.objects.get(key="ionos")
        self.assertFalse(check.success)
        self.assertNotIn("fake-test-password", check.diagnostic)

    def test_real_message_builder_uses_recorded_transport(self):
        from app.module.mail.send_mail_event import send_mail_event
        server = self.smtp()
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "clients/mail_validation.html"
            template.parent.mkdir()
            template.write_text('<b class="client_nom"></b><a class="mail_desabonnement"></a><a class="mail_client"></a>')
            with override_settings(MAIL_TEMPLATE_REPOSITORY=directory), patch("app.module.mail.delivery.smtplib.SMTP_SSL", return_value=server):
                self.assertTrue(send_mail_event(self.event, "validation"))
        delivery = EmailTracking.objects.get(event_traced=self.event.id)
        self.assertEqual(delivery.delivery_status, "accepted")
        self.assertEqual(set(server.sendmail.call_args.args[1]), {"client@example.invalid", "archive@example.invalid"})
        self.assertIn("Client test", server.sendmail.call_args.args[2])

    def test_preparation_failure_does_not_contact_smtp(self):
        from app.module.mail.send_mail_event import send_mail_event
        with override_settings(MAIL_TEMPLATE_REPOSITORY="/missing-test-template"), patch("app.module.mail.delivery.smtplib.SMTP_SSL") as transport:
            with self.assertRaises(FileNotFoundError):
                send_mail_event(self.event, "validation")
        transport.assert_not_called()
        self.assertEqual(EmailTracking.objects.get(event_traced=self.event.id).delivery_status, "error")

    def test_delivery_dashboard_access_render_and_filters(self):
        self.delivery()
        request = RequestFactory().get("/backend/graph/email-delivery/")
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        response = graph_email_delivery(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Livraison des mails")
        self.assertContains(response, "client@example.invalid")
        self.assertContains(response, "pas encore été exécutée")
        request.user.is_staff = False
        self.assertEqual(graph_email_delivery(request).status_code, 302)
        request = RequestFactory().get("/backend/graph/email-delivery/", {"status":"bad"})
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        self.assertEqual(graph_email_delivery(request).status_code, 400)

    def test_uncertain_attempt_blocks_retry_until_manually_resolved(self):
        delivery = self.delivery()
        EmailTracking.objects.filter(pk=delivery.pk).update(delivery_status="unknown")
        with self.assertRaises(ValueError):
            self.delivery()
        with self.assertRaises(CommandError):
            call_command("resolve_email_delivery", delivery.id, result="refused", stdout=io.StringIO())
        call_command("resolve_email_delivery", delivery.id, result="refused", confirm=True, stdout=io.StringIO())
        self.assertEqual(self.delivery().delivery_status, "preparing")

    def test_devis_builder_links_tracking_and_keeps_pdf_attachment(self):
        from app.module.mail.send_mail_event import send_mail_event
        import sys
        import types
        option = EventOption.objects.create()
        self.event.event_option = option
        self.event.reduc_product = self.event.reduc_all = 0
        self.event.num_devis = 1
        pdf = types.ModuleType("app.module.devis_pdf.generate_pdf")
        pdf.generate_pdf_devis = lambda event: io.BytesIO(b"%PDF-1.4 test attachment")
        post_form = types.ModuleType("app.module.data_bdd.post_form")
        post_form.make_num_devis = Mock()
        server = self.smtp()
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "devis/mail_devis.html"
            template.parent.mkdir()
            template.write_text('<b class="client_nom"></b><b class="date_butoire"></b><div class="acompte_particulier"></div><a class="txt_reduc"></a><a class="reduc_all"></a><img class="traceur_devis"><a class="mail_desabonnement"></a><a class="mail_client"></a>')
            with override_settings(MAIL_TEMPLATE_REPOSITORY=directory), patch.dict(sys.modules, {pdf.__name__:pdf, post_form.__name__:post_form}), patch("app.module.mail.delivery.smtplib.SMTP_SSL", return_value=server):
                self.assertTrue(send_mail_event(self.event, "devis"))
        delivery = EmailTracking.objects.get(event_traced=self.event.id)
        self.assertTrue(delivery.opening_tracked)
        self.assertEqual(EmailTracking.objects.filter(event_traced=self.event.id).count(), 1)
        msg = message_from_string(server.sendmail.call_args.args[2])
        self.assertEqual(msg.get_content_type(), "multipart/mixed")
        self.assertTrue(any(part.get_content_type() == "application/pdf" and part.get_payload(decode=True) == b"%PDF-1.4 test attachment" for part in msg.walk()))

    def test_opening_rates_exclude_non_pixel_and_failed_attempts(self):
        from app.views.private_api_data import email_counts
        EmailTracking.objects.create(event_traced=self.event.id, opened=True)
        EmailTracking.objects.create(event_traced=self.event.id, opening_tracked=False, delivery_status="accepted")
        EmailTracking.objects.create(event_traced=self.event.id, opening_tracked=True, delivery_status="refused")
        counts = email_counts(EmailTracking.objects.all())
        self.assertEqual(counts["tracked"], 1)
        self.assertEqual(counts["opening_rate_percent"], 100)
