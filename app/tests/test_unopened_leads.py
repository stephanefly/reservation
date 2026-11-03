from datetime import timedelta
from types import SimpleNamespace

from django.http import Http404, HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import path
from django.utils import timezone

from app.models import Client, EmailTracking, Event, EventDetails, EventRelance
from app.views.unopened_leads_views import lead_queryset, unopened_leads


urlpatterns = [path("login/", lambda request: HttpResponse("Login"), name="login"),
               path("backend/leads/", unopened_leads, name="unopened_leads"),
               path("event/<int:id>/", lambda request, id: HttpResponse("Event"), name="info_event"),
               path("delivery/", lambda request: HttpResponse("Delivery"), name="graph_email_delivery")]


@override_settings(ROOT_URLCONF=__name__)
class UnopenedLeadsTests(TestCase):
    def event(self, name, status="Sended", business=False, allowed=True, signed=False, past=False):
        person = Client.objects.create(nom=name, mail=name.lower() + "@example.invalid", numero_telephone="+33 6 01 02 03 04", raison_sociale=business, autorisation_mail=allowed)
        details = EventDetails.objects.create(date_evenement=timezone.localdate() + timedelta(days=-1 if past else 30), adresse_evenement="Test", ville_evenement="Paris", code_postal_evenement=75001)
        return Event.objects.create(client=person, event_details=details, prix_brut=500, prix_proposed=500, status=status, signer_at=timezone.now() if signed else None)

    def quote(self, event, opened=False, state="accepted", hours=72, kind="devis", pixel=True):
        track = EmailTracking.objects.create(event_traced=event.id, opened=opened, delivery_status=state, mail_type=kind, recipient=event.client.mail, opening_tracked=pixel)
        EmailTracking.objects.filter(pk=track.pk).update(sent_at=timezone.now() - timedelta(hours=hours))
        return track

    def get(self, **params):
        request = RequestFactory().get("/backend/leads/", params)
        request.user = SimpleNamespace(is_active=True, is_staff=True, get_username=lambda: "Stephane")
        return unopened_leads(request)

    def post(self, event, **data):
        values = {"event_id":event.id, "qualification":3, "commentaire":"Rappel demandé demain", "channel":"phone", **data}
        request = RequestFactory().post("/backend/leads/", values)
        request.user = SimpleNamespace(is_active=True, is_staff=True, get_username=lambda: "Stephane")
        return unopened_leads(request)

    def test_unopened_queue_is_one_row_per_lead_and_excludes_opened_quotes(self):
        lead = self.event("LeadUnique")
        self.quote(lead, hours=100)
        self.quote(lead, hours=72)
        opened = self.event("AlreadyOpened")
        self.quote(opened, opened=True, hours=100)
        self.quote(opened, opened=False, hours=72)
        # A different kind of opened mail is not an opened quote.
        self.quote(lead, opened=True, hours=10, kind="send_media", pixel=False)
        response = self.get()
        self.assertContains(response, "LeadUnique", count=1)
        self.assertNotContains(response, "AlreadyOpened")
        self.assertContains(response, "tel:+33601020304")
        self.assertContains(response, "mailto:leadunique@example.invalid")

    def test_ineligible_leads_are_not_returned(self):
        for name, values in (("Signed", {"signed":True}), ("Refused", {"status":"Refused"}), ("OptedOut", {"allowed":False}), ("Past", {"past":True}), ("Confirmed", {"status":"Acompte OK"})):
            self.quote(self.event(name, **values))
        self.event("NeverSent")
        self.assertEqual(lead_queryset().count(), 0)

    def test_delivery_issues_are_separate_and_latest_attempt_controls_the_queue(self):
        problem = self.event("BadAddress")
        self.quote(problem, opened=True, hours=100)
        self.quote(problem, state="bounced", hours=72)
        fresh = self.event("FixedAddress")
        self.quote(fresh, state="refused", hours=100)
        self.quote(fresh, state="accepted", hours=72)
        self.assertNotContains(self.get(), "BadAddress")
        response = self.get(bucket="issues")
        self.assertContains(response, "BadAddress")
        self.assertNotContains(response, "FixedAddress")
        self.assertContains(self.get(), "FixedAddress")

    def test_legacy_quotes_and_preparation_failures(self):
        old = self.event("LegacyLead")
        self.quote(old, state="legacy", kind="")
        bad = self.event("PreparationFailed")
        self.quote(bad, state="error", pixel=False)
        self.assertContains(self.get(), "LegacyLead")
        self.assertNotContains(self.get(), "PreparationFailed")
        self.assertContains(self.get(bucket="issues"), "PreparationFailed")

    def test_contact_note_is_saved_with_server_identity_and_moves_to_contacted(self):
        lead = self.event("ManualFollowup")
        self.quote(lead)
        self.assertEqual(self.post(lead).status_code, 302)
        note = EventRelance.objects.get(event=lead)
        self.assertEqual(note.membre, "Stephane")
        self.assertEqual(note.qualification, 3)
        self.assertIn("Rappel demandé demain", note.commentaire)
        self.assertNotContains(self.get(), "ManualFollowup")
        self.assertContains(self.get(followup="done"), "ManualFollowup")
        self.assertContains(self.get(followup="all"), "ManualFollowup")
        self.quote(lead, hours=0)
        self.assertContains(self.get(age="0"), "ManualFollowup")

    def test_filters_age_search_and_segment(self):
        business = self.event("BusinessLead", business=True)
        fresh = self.event("FreshLead")
        self.quote(business)
        self.quote(fresh, hours=1)
        self.assertNotContains(self.get(), "FreshLead")
        self.assertContains(self.get(age="0", segment="individual"), "FreshLead")
        self.assertNotContains(self.get(age="0", segment="individual"), "BusinessLead")
        self.assertContains(self.get(q="Business"), "BusinessLead")
        self.assertNotContains(self.get(q="Business"), "FreshLead")
        for params in ({"age":"bad"}, {"bucket":"bad"}, {"followup":"bad"}, {"segment":"bad"}):
            self.assertEqual(self.get(**params).status_code, 400)

    def test_post_validation_and_stale_signed_lead(self):
        lead = self.event("Validation")
        self.quote(lead)
        for values in ({"qualification":9}, {"commentaire":""}, {"commentaire":"x" * 2001}, {"channel":"bad"}):
            self.assertEqual(self.post(lead, **values).status_code, 400)
        Event.objects.filter(pk=lead.pk).update(signer_at=timezone.now())
        with self.assertRaises(Http404):
            self.post(lead)
        self.assertEqual(EventRelance.objects.count(), 0)

    def test_non_staff_cannot_read_or_write(self):
        lead = self.event("PrivateLead")
        self.quote(lead)
        for method in ("get", "post"):
            request = getattr(RequestFactory(), method)("/backend/leads/", {"event_id":lead.id, "commentaire":"test"})
            request.user = SimpleNamespace(is_active=True, is_staff=False)
            self.assertEqual(unopened_leads(request).status_code, 302)
        self.assertEqual(EventRelance.objects.count(), 0)
