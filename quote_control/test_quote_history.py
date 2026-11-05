"""Historique CRM : seulement les devis envoyés par le moteur automatique."""
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Client, Event, EventDetails, EventOption, EventProduct
from quote_control.models import AutoQuoteLog


class AutomaticQuoteHistoryTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="history-staff", password="test-only", is_staff=True
        )
        self.other = User.objects.create_user(
            username="history-visitor", password="test-only"
        )
        self.client.force_login(self.staff)
        self.catalogue = reverse("admin_catalog")
        self.url = self.catalogue + "?tab=historique"

    def make_event(self):
        client = Client.objects.create(
            nom="Client Test Historique",
            mail="historique@example.invalid",
            numero_telephone="0100000000",
            how_find="INSTAGRAM",
        )
        details = EventDetails.objects.create(
            date_evenement=date(2027, 2, 20),
            adresse_evenement="1 rue Exemple",
            ville_evenement="Paris",
            code_postal_evenement=75001,
        )
        product = EventProduct.objects.create(photobooth=True)
        option = EventOption.objects.create(duree=5)
        return Event.objects.create(
            client=client, event_details=details,
            event_product=product, event_option=option, prix_brut=0,
        )

    def test_history_is_a_third_tab_next_to_simulation(self):
        response = self.client.get(self.catalogue)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Offres et tarifs</a>", html)
        self.assertIn("Simulation</a>", html)
        self.assertIn("Historique des envois</a>", html)
        self.assertLess(html.index("Simulation</a>"), html.index("Historique des envois</a>"))
        self.assertNotContains(response, "Historique des devis envoyés automatiquement")

    def test_empty_history_has_clear_message(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "historique")
        self.assertContains(response, "Aucun devis envoyé automatiquement")
        self.assertContains(response, "0 envoi")
        self.assertNotContains(response, "Client Test Historique")

    def test_sent_log_shows_date_client_mail_product_amount_and_event(self):
        event = self.make_event()
        sent = AutoQuoteLog.objects.create(
            event_id=event.pk, source="INSTAGRAM", outcome="sent",
            amount=400, reason="Photobooth",
        )
        AutoQuoteLog.objects.create(
            event_id=event.pk, source="INSTAGRAM", outcome="error",
            reason="Mail non accepté",
        )
        AutoQuoteLog.objects.create(
            event_id=event.pk, source="INSTAGRAM", outcome="manual",
            reason="Entreprise",
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sent_total"], 1)
        self.assertContains(response, "1 envoi")
        self.assertContains(response, "Client Test Historique")
        self.assertContains(response, "historique@example.invalid")
        self.assertContains(response, "400 € TTC")
        self.assertContains(response, "Photobooth")
        self.assertContains(response, "Source : INSTAGRAM")
        self.assertContains(response, sent.created_at.strftime("%d/%m/%Y"))
        self.assertContains(response, "Voir le dossier")
        self.assertContains(response, reverse("info_event", kwargs={"id": event.pk}))
        self.assertNotContains(response, "Mail non accepté")
        self.assertNotContains(response, "Entreprise")
        self.assertContains(response, "ne confirme pas que le destinataire")
        self.assertContains(response, "fiche client actuelle")

    def test_deleted_or_missing_event_remains_visible_without_broken_link(self):
        AutoQuoteLog.objects.create(
            event_id=999999, source="INSTAGRAM",
            outcome="sent", amount=600, reason="Pack Souvenirs",
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dossier supprimé ou indisponible")
        self.assertContains(response, "#999999")
        self.assertContains(response, "Pack Souvenirs")
        self.assertNotContains(response, reverse("info_event", kwargs={"id": 999999}))

    def test_pagination_25_and_bad_page_values(self):
        for index in range(52):
            AutoQuoteLog.objects.create(
                event_id=10000 + index, outcome="sent",
                amount=400, reason="Offre %02d" % index,
            )
        response = self.client.get(self.url)
        self.assertEqual(response.context["sent_total"], 52)
        self.assertEqual(len(response.context["history"]), 25)
        self.assertContains(response, "Page 1 sur 3")
        self.assertContains(response, "tab=historique&amp;page=2")
        self.assertNotContains(response, "Offre 00")

        response2 = self.client.get(self.url + "&page=2")
        self.assertEqual(len(response2.context["history"]), 25)
        self.assertContains(response2, "Page 2 sur 3")
        response3 = self.client.get(self.url + "&page=3")
        self.assertEqual(len(response3.context["history"]), 2)
        self.assertContains(response3, "Page 3 sur 3")
        bad = self.client.get(self.url + "&page=not-a-number")
        self.assertEqual(bad.context["history"].number, 1)
        out_of_range = self.client.get(self.url + "&page=999")
        self.assertEqual(out_of_range.context["history"].number, 3)

    def test_history_does_not_appear_inside_simulation(self):
        AutoQuoteLog.objects.create(
            event_id=1, outcome="sent",
            amount=777, reason="HISTORIQUE_SENT_UNIQUE",
        )
        response = self.client.get(self.catalogue + "?tab=simulation")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "HISTORIQUE_SENT_UNIQUE")
        self.assertContains(response, "Simulation de devis")

    def test_only_staff_can_see_history(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 302)
