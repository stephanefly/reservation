from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase, override_settings

from app import models
from app.views.private_api_data import RESOURCES


class PrivateApiTests(TestCase):
    def get(self, path, **params):
        return self.client.get(path, params, HTTP_X_PRIVATE_API_TOKEN="test-private-token")

    def setUp(self):
        self.person = models.Client.objects.create(nom="Test", mail="test@example.invalid", numero_telephone="0100000000", code_espace_client="SECRET")
        self.details = models.EventDetails.objects.create(date_evenement="2026-11-03", adresse_evenement="Test", ville_evenement="Paris", code_postal_evenement=75001)
        self.event = models.Event.objects.create(client=self.person, event_details=self.details, prix_brut=500, event_token="SECRET")

    def test_authentication_and_read_only_for_all_new_routes(self):
        for path in ("/schema/", "/email-stats/", "/resources/clients/", "/resources/events/1/"):
            self.assertEqual(self.client.get(path).status_code, 403)
            self.assertEqual(self.client.get(path, HTTP_X_PRIVATE_API_TOKEN="wrong").status_code, 403)
            self.assertEqual(self.client.post(path, HTTP_X_PRIVATE_API_TOKEN="test-private-token").status_code, 405)
        with override_settings(PRIVATE_API_TOKEN=""):
            self.assertEqual(self.get("/schema/").status_code, 500)

    def test_schema_covers_every_model_field_except_credentials(self):
        excluded = {"event_token", "code_espace_client", "uuid"}
        for resource, (model, fields) in RESOURCES.items():
            actual = {field.attname for field in model._meta.concrete_fields} - {"id"} - excluded
            self.assertEqual(set(fields.split()), actual, resource)
        self.assertEqual(len(RESOURCES), len(list(models.Client._meta.apps.get_app_config("app").get_models())))

    def test_related_record_fields_and_resource_details(self):
        option = models.EventOption.objects.create(panneaux_xxl=4, panneaux_forfait=400)
        payment = models.EventAcompte.objects.create(montant_acompte=100, montant_restant=800)
        self.event.event_option = option
        self.event.event_acompte = payment
        # Avoid business save hooks, which invoke external integrations.
        models.Event.objects.filter(pk=self.event.pk).update(event_option=option, event_acompte=payment)
        data = self.get(f"/event/{self.event.id}/").json()["event"]["details_complets"]
        self.assertEqual(data["event_option"]["panneaux_forfait"], 400)
        self.assertEqual(data["event_acompte"]["montant_restant"], 800)
        self.assertEqual(self.get(f"/resources/options/{option.id}/").json()["item"]["panneaux_xxl"], 4)

    def test_resources_are_valid_and_paginated(self):
        for resource in RESOURCES:
            result = self.get(f"/resources/{resource}/")
            self.assertEqual(result.status_code, 200, result.content)
        models.Client.objects.create(nom="Second", mail="second@example.invalid", numero_telephone="02")
        first = self.get("/resources/clients/", page_size=1).json()
        second = self.get("/resources/clients/", page_size=1, page=2).json()
        self.assertEqual(first["total"], 2)
        self.assertTrue(first["has_next"])
        self.assertFalse(second["has_next"])
        self.assertNotEqual(first["items"][0]["id"], second["items"][0]["id"])
        self.assertNotIn("SECRET", str(first))
        self.assertEqual(self.get("/resources/clients/", q="Second").json()["total"], 1)
        for params in ({"page": "x"}, {"page": 0}, {"page_size": 101}):
            self.assertEqual(self.get("/resources/clients/", **params).status_code, 400)
        self.assertEqual(self.get("/resources/unknown/").status_code, 404)
        self.assertEqual(self.get("/resources/clients/999/").status_code, 404)

    def test_email_stats_counts_and_date_boundaries(self):
        paris = ZoneInfo("Europe/Paris")
        for day, opened, status in ((2, True, "Sended"), (3, True, "Sended"), (3, False, "Resended"), (4, False, "Sended")):
            obj = models.EmailTracking.objects.create(event_traced=self.event.id, opened=opened, status_devis=status)
            models.EmailTracking.objects.filter(pk=obj.pk).update(sent_at=datetime(2026, 11, day, 23, 59, tzinfo=paris))
        result = self.get("/email-stats/", start_date="2026-11-03", end_date="2026-11-03").json()
        self.assertEqual(result["totals"], {"tracked": 2, "opened": 1, "not_opened": 1, "opening_rate_percent": 50.0})
        self.assertEqual(result["by_month"][0]["tracked"], 2)
        self.assertEqual(len(result["by_status"]), 2)
        self.assertEqual(self.get("/email-stats/", status="Resended").json()["totals"]["opening_rate_percent"], 0.0)
        self.assertIsNone(self.get("/email-stats/", event_id=999).json()["totals"]["opening_rate_percent"])
        self.assertEqual(self.get("/email-stats/", opened="true").status_code, 400)
        self.assertEqual(self.get("/resources/email-tracking/", opened="true").json()["total"], 2)
        self.assertEqual(self.get("/resources/email-tracking/", opened="invalid").status_code, 400)
        for params in ({"start_date": "bad"}, {"start_date": "2026-11-04", "end_date": "2026-11-01"}):
            self.assertEqual(self.get("/email-stats/", **params).status_code, 400)

    def test_event_detail_preserves_old_fields_and_includes_related_data(self):
        member = models.TeamMember.objects.create(name="Test member")
        self.event.event_team_members.add(member)
        models.EventRelance.objects.create(event=self.event, commentaire="Client contacté")
        response = self.get(f"/event/{self.event.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()["event"]
        self.assertEqual(data["client"], "Test")
        full = data["details_complets"]
        self.assertEqual(full["client"]["mail"], "test@example.invalid")
        self.assertEqual(full["team"][0]["id"], member.id)
        self.assertIsNone(full["event_option"])
        self.assertNotIn("SECRET", str(data))
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(self.get("/resources/follow-ups/", event_id=self.event.id).json()["items"][0]["commentaire"], "Client contacté")

    def test_event_filters_and_legacy_endpoints(self):
        self.assertEqual(self.get("/resources/events/", q="Paris", client_id=self.person.id).json()["total"], 1)
        self.assertEqual(self.get("/resources/events/", start_date="2026-11-04").json()["total"], 0)
        self.assertEqual(self.get("/resources/events/", status="Refused").json()["total"], 0)
        for path in ("/ping/", "/crm-summary/", "/upcoming-events/", "/confirmed-events/"):
            self.assertEqual(self.get(path).status_code, 200)
            self.assertEqual(self.client.get(path).status_code, 403)
