from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Client, Event, EventDetails
from app.module.mail.choose_to_relance import process_events_until
from app.module.mail.send_mail_event import send_mail_event


class ClientQuoteReminderToggleTests(TestCase):
    def setUp(self):
        self.contact = Client.objects.create(
            nom='Client Test', mail='test@example.com', numero_telephone='0600000000'
        )
        details = EventDetails.objects.create(
            date_evenement=date.today() + timedelta(days=30),
            adresse_evenement='1 rue Test',
            ville_evenement='Paris',
            code_postal_evenement=75001,
        )
        self.event = Event.objects.create(
            client=self.contact, event_details=details,
            prix_brut=400, status='Sended'
        )
        self.url = reverse('set_client_quote_reminders', args=[self.event.pk])
        self.staff = get_user_model().objects.create_user(
            username='staff_test', password='password', is_staff=True
        )

    def test_staff_can_suspend_and_reactivate_without_saving_the_event(self):
        self.client.force_login(self.staff)

        response = self.client.post(self.url, {'relance_devis_auto': '0'})
        self.assertEqual(response.status_code, 302)
        self.contact.refresh_from_db()
        self.event.refresh_from_db()
        self.assertFalse(self.contact.relance_devis_auto)
        self.assertEqual(self.event.status, 'Sended')

        response = self.client.post(self.url, {'relance_devis_auto': '1'})
        self.assertEqual(response.status_code, 302)
        self.contact.refresh_from_db()
        self.assertTrue(self.contact.relance_devis_auto)
        # Le choix de relances ne change pas le consentement aux e-mails.
        self.assertTrue(self.contact.autorisation_mail)

    def test_route_is_post_only_and_staff_only(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self.client.post(self.url, {'relance_devis_auto': 'invalid'}).status_code, 400)

        self.client.logout()
        self.assertEqual(self.client.post(self.url, {'relance_devis_auto': '0'}).status_code, 302)
        self.contact.refresh_from_db()
        self.assertTrue(self.contact.relance_devis_auto)

    @patch('app.module.mail.send_mail_event.smtplib.SMTP_SSL')
    def test_automatic_send_refuses_opted_out_client_before_smtp(self, smtp):
        self.contact.relance_devis_auto = False
        self.contact.save(update_fields=['relance_devis_auto'])
        self.assertFalse(send_mail_event(self.event, 'rappel_devis', automatic=True))
        smtp.assert_not_called()

    @patch('app.module.mail.choose_to_relance.send_mail_event')
    def test_automatic_relance_does_not_change_status_when_disabled(self, sender):
        Event.objects.filter(pk=self.event.pk).update(
            created_at=timezone.now() - timedelta(days=10)
        )
        self.contact.relance_devis_auto = False
        self.contact.save(update_fields=['relance_devis_auto'])
        process_events_until(2, 'Sended', 'First Rappel', 'rappel_devis')
        sender.assert_not_called()
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, 'Sended')

    @patch('app.module.mail.send_mail_event.smtplib.SMTP_SSL')
    def test_client_unsubscribed_still_blocks_automatic_commercial_email(self, smtp):
        self.contact.autorisation_mail = False
        self.contact.save(update_fields=['autorisation_mail'])
        self.assertFalse(send_mail_event(self.event, 'rappel_devis', automatic=True))
        smtp.assert_not_called()

    @patch('app.module.mail.send_mail_event.smtplib.SMTP_SSL')
    @patch('app.module.mail.send_mail_event.complete_mail')
    @patch('app.module.mail.send_mail_event.get_mail_template')
    @patch('builtins.open')
    def test_prep_reminder_is_still_sent_when_quote_relances_disabled(self, open_file, template, complete, smtp):
        self.contact.relance_devis_auto = False
        self.contact.save(update_fields=['relance_devis_auto'])
        template.return_value = ('Preparation', 'clients/mail_relance_espace_client.html', [], [])
        open_file.return_value.__enter__.return_value.read.return_value = '<html></html>'
        complete.return_value.prettify.return_value = '<html></html>'

        self.assertTrue(send_mail_event(self.event, 'relance_espace_client', automatic=True))
        smtp.assert_called_once()
