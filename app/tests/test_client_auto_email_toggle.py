from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Client, Event, EventDetails
from app.module.mail.choose_to_relance import process_events_until
from app.module.mail.send_mail_event import send_mail_event


class ClientAutoEmailToggleTests(TestCase):
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
        self.url = reverse('set_client_auto_emails', args=[self.event.pk])
        self.staff = get_user_model().objects.create_user(
            username='staff_test', password='password', is_staff=True
        )

    def test_staff_can_suspend_and_reactivate_without_saving_the_event(self):
        self.client.force_login(self.staff)

        response = self.client.post(self.url, {'autorisation_mail': '0'})
        self.assertEqual(response.status_code, 302)
        self.contact.refresh_from_db()
        self.event.refresh_from_db()
        self.assertFalse(self.contact.autorisation_mail)
        self.assertEqual(self.event.status, 'Sended')

        response = self.client.post(self.url, {'autorisation_mail': '1'})
        self.assertEqual(response.status_code, 302)
        self.contact.refresh_from_db()
        self.assertTrue(self.contact.autorisation_mail)

    def test_route_is_post_only_and_staff_only(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self.client.post(self.url, {'autorisation_mail': 'invalid'}).status_code, 400)

        self.client.logout()
        self.assertEqual(self.client.post(self.url, {'autorisation_mail': '0'}).status_code, 302)
        self.contact.refresh_from_db()
        self.assertTrue(self.contact.autorisation_mail)

    @patch('app.module.mail.send_mail_event.smtplib.SMTP_SSL')
    def test_automatic_send_refuses_opted_out_client_before_smtp(self, smtp):
        self.contact.autorisation_mail = False
        self.contact.save(update_fields=['autorisation_mail'])
        self.assertFalse(send_mail_event(self.event, 'rappel_devis', automatic=True))
        smtp.assert_not_called()

    @patch('app.module.mail.choose_to_relance.send_mail_event')
    def test_automatic_relance_does_not_change_status_when_disabled(self, sender):
        Event.objects.filter(pk=self.event.pk).update(
            created_at=timezone.now() - timedelta(days=10)
        )
        self.contact.autorisation_mail = False
        self.contact.save(update_fields=['autorisation_mail'])
        process_events_until(2, 'Sended', 'First Rappel', 'rappel_devis')
        sender.assert_not_called()
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, 'Sended')
