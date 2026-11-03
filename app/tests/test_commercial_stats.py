from datetime import date, datetime, timedelta
from unittest.mock import patch
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from django.urls import path

from app.models import Client, EmailTracking, Event, EventAcompte, EventDetails, EventProduct, EventRelance
from app.views.commercial_stats_views import commercial_report, graph_commercial_stats


urlpatterns = [path("login/", lambda request: HttpResponse("Login"), name="login"),
               path("backend/graph/commercial/", graph_commercial_stats, name="graph_commercial_stats"),
               path("event/<int:id>/", lambda request, id: HttpResponse("Event"), name="info_event")]


@override_settings(ROOT_URLCONF=__name__)
class CommercialStatsTests(TestCase):
    def setUp(self):
        self.created = datetime(2026, 11, 3, 23, 59, tzinfo=ZoneInfo("Europe/Paris"))
        self.person = Client.objects.create(nom="Particulier", mail="test@example.invalid", numero_telephone="01")
        self.business = Client.objects.create(nom="Entreprise", mail="pro@example.invalid", numero_telephone="02", raison_sociale=True)
        self.details = EventDetails.objects.create(date_evenement="2026-11-15", adresse_evenement="Test", ville_evenement="Paris", code_postal_evenement=75001)

    def event(self, status="Sended", proposed=1000, signed=None, validated=None, history="", business=False, balance=None):
        payment = EventAcompte.objects.create(montant_restant=balance) if balance is not None else None
        event = Event.objects.create(client=self.business if business else self.person, event_details=self.details,
                                     prix_brut=1500, prix_proposed=proposed, prix_valided=validated, signer_at=signed,
                                     status=status, history_status=history, event_acompte=payment)
        Event.objects.filter(pk=event.pk).update(created_at=self.created)
        return event

    def request(self, **params):
        return RequestFactory().get("/backend/graph/commercial/", params)

    def test_commercial_counts_amounts_delays_and_segments(self):
        self.event(status="Initied", proposed=None)
        self.event()
        self.event(status="Acompte OK", signed=self.created + timedelta(days=5), validated=900, history="Sended, First Rappel, First Rappel")
        self.event(status="Refused", proposed=500)
        self.event(status="Presta FINI", proposed=600, balance=200)
        self.event(status="Acompte OK", signed=self.created - timedelta(days=1), validated=0, business=True)
        with self.assertNumQueries(3):
            report = commercial_report(self.request())
        totals = report["totals"]
        for key, value in {"requests":6, "processed":5, "signed":2, "refused":1, "pending":2,
                           "conversion":40.0, "signed_amount":900, "pending_amount":1600,
                           "refused_amount":500, "average_signed":450.0, "average_delay":5.0,
                           "invalid_delays":1, "outstanding_count":1, "outstanding_amount":200}.items():
            self.assertEqual(totals[key], value, key)
        self.assertEqual(report["unsigned_confirmed"], 1)
        self.assertEqual(report["segments"][1]["signed_amount"], 0)
        self.assertEqual(report["segments"][1]["conversion"], 100.0)
        self.assertEqual(sum(row["count"] for row in report["statuses"]), 6)

    def test_history_matches_whole_status_and_tracking_is_deduplicated(self):
        signed = self.event(status="Acompte OK", signed=self.created + timedelta(days=1), history="Sended, First Rappel")
        for _ in range(2):
            EmailTracking.objects.create(event_traced=signed.id, status_devis="First Rappel")
        draft = self.event(status="Pending", history="Not First Rappel")
        EmailTracking.objects.create(event_traced=draft.id, status_devis="Sended")
        report = commercial_report(self.request())
        first = report["relances"][0]
        self.assertEqual(first["count"], 1)
        self.assertEqual(first["signed"], 1)
        self.assertEqual(report["totals"]["processed"], 2)

    def test_inclusive_cohort_dates_and_client_filter(self):
        self.event(business=True)
        self.event()
        self.assertEqual(commercial_report(self.request(start_date="2026-11-03", end_date="2026-11-03"))["totals"]["requests"], 2)
        self.assertEqual(commercial_report(self.request(start_date="2026-11-04"))["totals"]["requests"], 0)
        self.assertEqual(commercial_report(self.request(segment="business"))["totals"]["requests"], 1)
        self.assertEqual(commercial_report(self.request(segment="individual"))["totals"]["requests"], 1)
        for params in ({"segment":"invalid"}, {"start_date":"bad"}, {"start_date":"2026-12-01","end_date":"2026-11-01"}):
            with self.assertRaises(ValueError):
                commercial_report(self.request(**params))

    def test_missing_values_and_empty_period(self):
        report = commercial_report(self.request())
        self.assertIsNone(report["totals"]["conversion"])
        self.assertIsNone(report["totals"]["average_delay"])
        self.event(signed=self.created, proposed=None, validated=None)
        report = commercial_report(self.request())
        self.assertEqual(report["missing_amounts"], 1)
        self.assertEqual(report["totals"]["signed_amount"], 0)
        self.assertEqual(report["totals"]["average_delay"], 0)

    def test_dashboard_render_authentication_and_errors(self):
        self.event(status="Presta FINI", balance=200)
        request = self.request()
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        response = graph_commercial_stats(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Performance commerciale")
        self.assertContains(response, "Soldes à récupérer")
        self.assertContains(response, "/event/")
        self.assertIn("no-store", response["Cache-Control"])
        request.user.is_staff = False
        self.assertEqual(graph_commercial_stats(request).status_code, 302)
        bad = self.request(start_date="bad")
        bad.user = SimpleNamespace(is_active=True, is_staff=True)
        self.assertEqual(graph_commercial_stats(bad).status_code, 400)
        post = RequestFactory().post("/backend/graph/commercial/")
        post.user = bad.user
        self.assertEqual(graph_commercial_stats(post).status_code, 405)


    def test_quote_graphs_use_only_processed_quotes_and_current_state(self):
        pending_person = self.event(status="Sended", proposed=1400)
        self.event(status="Pending", proposed=300, business=True, history="Sended")
        self.event(status="Refused", proposed=500)
        self.event(status="Acompte OK", proposed=1200, signed=self.created + timedelta(days=2), validated=900)
        self.event(status="Initied", proposed=9999)  # Not yet sent: exclude.
        with patch("app.module.lib_graph.commercial_pipeline.timezone.now",
                   return_value=self.created + timedelta(days=40)):
            report = commercial_report(self.request())

        self.assertEqual(report["quote_portfolio"][0]["amount"], 900)
        self.assertEqual(report["quote_portfolio"][1]["amount"], 1700)
        self.assertEqual(report["quote_portfolio"][2]["amount"], 500)
        self.assertEqual([row["count"] for row in report["quote_portfolio"]], [1, 2, 1])
        self.assertEqual(report["quote_ages"][3]["count"], 2)
        self.assertEqual(report["quote_clients"][0]["amount"], 1400)
        self.assertEqual(report["quote_clients"][1]["amount"], 300)
        self.assertEqual(report["quote_periods"][0]["rows"][0]["label"], "2026")
        self.assertEqual(report["quote_periods"][0]["rows"][0]["processed"], 4)
        self.assertEqual(report["quote_periods"][0]["rows"][0]["conversion"], 25.0)
        self.assertEqual(report["quote_periods"][0]["rows"][0]["pending_amount"], 1700)
        self.assertEqual(report["quote_periods"][1]["rows"][0]["label"], "Nov 2026")
        self.assertEqual(report["quote_periods"][1]["rows"][0]["processed"], 4)
        self.assertEqual(report["quote_top_pending"][0]["event"].id, pending_person.id)
        self.assertEqual(report["quote_top_pending"][0]["amount"], 1400)

    def test_quote_graphs_respect_existing_client_and_date_filters(self):
        self.event(status="Sended", proposed=200)
        self.event(status="Sended", proposed=700, business=True)
        self.event(status="Acompte OK", signed=self.created, proposed=400, business=True)
        report = commercial_report(self.request(segment="business",
                                                start_date="2026-11-03",
                                                end_date="2026-11-03"))
        self.assertEqual([row["count"] for row in report["quote_clients"]], [0, 1])
        self.assertEqual([row["count"] for row in report["quote_portfolio"]], [1, 1, 0])
        self.assertEqual(len(report["quote_periods"][0]["rows"]), 1)
        self.assertEqual(report["quote_periods"][0]["rows"][0]["pending"], 1)
        self.assertEqual(report["quote_periods"][1]["rows"][0]["pending"], 1)

    def test_dashboard_displays_all_quote_graphs(self):
        self.event(status="Sended", proposed=450)
        request = self.request()
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        response = graph_commercial_stats(request)
        for title in ("Évolution annuelle des devis traités",
                      "Évolution mensuelle des devis traités",
                      "Ancienneté des devis en attente",
                      "Potentiel non signé par clientèle",
                      "Taux de signature par année",
                      "Taux de signature par mois",
                      "Répartition des montants de devis",
                      "10 plus gros devis en attente à relancer"):
            self.assertContains(response, title)
        self.assertContains(response, "450 €")


    def test_annual_and_month_boundary_with_paris_timezone(self):
        old = self.event(status="Sended", proposed=350)
        s1 = self.event(status="Acompte OK", signed=self.created, validated=800)
        s2 = self.event(status="Refused", proposed=200)
        dates = [
            (old, datetime(2025, 12, 31, 23, 59, tzinfo=ZoneInfo("Europe/Paris"))),
            (s1, datetime(2026, 6, 30, 23, 59, tzinfo=ZoneInfo("Europe/Paris"))),
            (s2, datetime(2026, 7, 1, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))),
        ]
        for event, created in dates:
            Event.objects.filter(pk=event.pk).update(created_at=created)
        report = commercial_report(self.request())
        years, monthly = [row["rows"] for row in report["quote_periods"]]
        months = {row["label"]: row for row in monthly}
        self.assertEqual([(row["label"], row["processed"]) for row in years],
                         [("2025", 1), ("2026", 2)])
        self.assertEqual(months["Déc 2025"]["processed"], 1)
        self.assertEqual(months["Juin 2026"]["processed"], 1)
        self.assertEqual(months["Juil 2026"]["processed"], 1)
        self.assertEqual(months["Jan 2026"]["processed"], 0)
        self.assertEqual(len(months), 8)
        self.assertEqual(years[0]["pending_amount"], 350)
        self.assertEqual(years[1]["signed_amount"], 800)
        self.assertEqual(years[1]["refused_amount"], 200)
        self.assertEqual(months["Juin 2026"]["conversion"], 100.0)
        self.assertEqual(months["Juil 2026"]["conversion"], 0.0)


    def test_insights_funnel_unique_tracking_and_multi_product_attribution(self):
        both = EventProduct.objects.create(photobooth=True, miroirbooth=True)
        mirror = EventProduct.objects.create(miroirbooth=True)
        photo = EventProduct.objects.create(photobooth=True)
        unprocessed = self.event(status="Initied", proposed=999)
        signed = self.event(status="Acompte OK", signed=self.created,
                            validated=900, proposed=1200)
        pending = self.event(status="Sended", proposed=1000, business=True)
        refused = self.event(status="Refused", proposed=500)
        for event, product in ((signed, both), (pending, mirror), (refused, photo)):
            Event.objects.filter(pk=event.pk).update(event_product=product)

        # Two quote emails for the same dossier must not double-count a send/open.
        for _ in range(2):
            EmailTracking.objects.create(
                event_traced=pending.id, status_devis="Sended", mail_type="devis",
                delivery_status="accepted", opened=True, opening_tracked=True,
            )
        EmailTracking.objects.create(
            event_traced=refused.id, status_devis="Sended", mail_type="devis",
            delivery_status="bounced", opened=False,
        )
        EmailTracking.objects.create(
            event_traced=signed.id, status_devis="Acompte OK",
            mail_type="confirmation", delivery_status="delivered", opened=True,
        )
        EmailTracking.objects.create(
            event_traced=unprocessed.id, status_devis="Initied", mail_type="devis",
            delivery_status="error", opened=False,
        )

        report = commercial_report(self.request())
        stages = report["insight_funnel"]
        self.assertEqual([stage["count"] for stage in stages], [4, 3, 2, 1, 1])
        products = {row["label"]: row for row in report["insight_products"]}
        self.assertEqual(products["Photobooth"]["signed"], 1)
        self.assertEqual(products["Photobooth"]["refused"], 1)
        self.assertEqual(products["Photobooth"]["signed_amount"], 900)
        self.assertEqual(products["Miroirbooth"]["pending_amount"], 1000)
        self.assertEqual(products["Miroirbooth"]["signed_amount"], 900)
        self.assertEqual(products["Photobooth"]["conversion"], 50.0)
        self.assertEqual(report["insight_products_missing"], 1)
        self.assertEqual(report["insight_loss_count"], 1)
        self.assertEqual(report["insight_loss_amount"], 500)
        self.assertEqual(report["insight_loss_rate"], 33.3)
        self.assertEqual(report["insight_loss_bands"][1]["count"], 1)
        self.assertEqual(report["insight_loss_segments"][0]["amount"], 500)

    def test_lead_scoring_uses_eligibility_human_qualification_and_recent_contact(self):
        product = EventProduct.objects.create(photobooth=True)
        hot = self.event(status="Sended", proposed=2200)
        warm = self.event(status="Sended", proposed=500, business=True)
        opt_out = self.event(status="Sended", proposed=4000)
        refused = self.event(status="Refused", proposed=5000)
        signed = self.event(status="Acompte OK", proposed=5000, signed=self.created)
        draft = self.event(status="Initied", proposed=10000)
        past = self.event(status="Sended", proposed=9000)
        old_details = EventDetails.objects.create(
            date_evenement="2026-01-01", adresse_evenement="Test",
            ville_evenement="Paris", code_postal_evenement=75001,
        )
        Event.objects.filter(pk=past.pk).update(event_details=old_details)
        for event in (hot, warm, opt_out, refused, signed, draft, past):
            Event.objects.filter(pk=event.pk).update(event_product=product)
        self.person.autorisation_mail = False
        # Use a separate client for the opted-out dossier so hot/refused keep consent.
        self.person.save(update_fields=["autorisation_mail"])
        self.business.autorisation_mail = True
        self.business.save(update_fields=["autorisation_mail"])
        hot.client = self.business
        hot.save(update_fields=["client"])
        opt_out.client = self.person
        opt_out.save(update_fields=["client"])
        EventRelance.objects.create(
            event=warm, membre="Test", qualification=5,
            date_relance=self.created - timedelta(days=10), commentaire="Qualifié",
        )
        EmailTracking.objects.create(
            event_traced=hot.id, status_devis="Sended", mail_type="devis",
            delivery_status="accepted", opened=True,
        )

        with patch("app.module.lib_graph.commercial_insights.timezone.now",
                   return_value=self.created + timedelta(days=5)):
            report = commercial_report(self.request())
        rows = report["insight_leads"]
        ids = {row["event"].id for row in rows}
        self.assertEqual(ids, {hot.id, warm.id})
        self.assertEqual(rows[0]["event"].id, hot.id)
        self.assertGreater(rows[0]["score"], rows[1]["score"])
        self.assertTrue(rows[0]["opened"])
        self.assertEqual(report["insight_leads_count"], 2)
        self.assertEqual(report["insight_leads_more"], 0)

    def test_insights_respect_business_and_date_filters(self):
        self.event(status="Refused", proposed=400)
        self.event(status="Sended", proposed=1500, business=True)
        filtered = commercial_report(self.request(
            segment="business", start_date="2026-11-03", end_date="2026-11-03",
        ))
        self.assertEqual(filtered["insight_funnel"][0]["count"], 1)
        self.assertEqual(filtered["insight_loss_count"], 0)
        self.assertEqual(filtered["insight_leads_count"], 1)
        self.assertEqual(filtered["insight_loss_segments"][0]["count"], 0)

    def test_insight_dashboard_renders_and_handles_no_data(self):
        request = self.request()
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        response = graph_commercial_stats(request)
        for title in ("Tunnel de conversion commercial",
                      "Performance commerciale par produit",
                      "Analyse des devis refusés",
                      "Prospects à relancer en priorité"):
            self.assertContains(response, title)
        self.assertContains(response, "Aucun devis en attente éligible")
        self.assertContains(response, "Aucun refus enregistré")
        self.assertIn("no-store", response["Cache-Control"])


    def test_alerts_counts_priorities_filters_and_open_quote_eligibility(self):
        """One dossier appears once, even when it matches several categories."""
        future = EventDetails.objects.create(
            date_evenement="2026-12-30", adresse_evenement="Test",
            ville_evenement="Paris", code_postal_evenement=75001,
        )
        imminent = EventDetails.objects.create(
            date_evenement="2026-11-12", adresse_evenement="Test",
            ville_evenement="Paris", code_postal_evenement=75001,
        )
        past = EventDetails.objects.create(
            date_evenement="2026-11-01", adresse_evenement="Test",
            ville_evenement="Paris", code_postal_evenement=75001,
        )
        high = self.event(status="Sended", proposed=2400)
        near = self.event(status="Sended", proposed=100)
        issue = self.event(status="Sended", proposed=100)
        opted = self.event(status="Sended", proposed=1400)
        healthy = self.event(status="Sended", proposed=100)
        refused = self.event(status="Refused", proposed=5000)
        signed = self.event(status="Acompte OK", proposed=5000, signed=self.created)
        draft = self.event(status="Initied", proposed=5000)
        expired = self.event(status="Sended", proposed=5000)

        for event in (high, issue, opted, healthy, refused, signed, draft):
            Event.objects.filter(pk=event.pk).update(event_details=future)
        Event.objects.filter(pk=near.pk).update(event_details=imminent)
        Event.objects.filter(pk=expired.pk).update(event_details=past)
        Event.objects.filter(pk=issue.pk).update(
            created_at=datetime(2026, 11, 10, 9, tzinfo=ZoneInfo("Europe/Paris"))
        )
        Event.objects.filter(pk=healthy.pk).update(
            created_at=datetime(2026, 11, 10, 9, tzinfo=ZoneInfo("Europe/Paris"))
        )
        separate_client = Client.objects.create(
            nom="Sans emails", mail="optout@example.invalid",
            numero_telephone="01", autorisation_mail=False,
        )
        Event.objects.filter(pk=opted.pk).update(client=separate_client)
        failed = EmailTracking.objects.create(
            event_traced=issue.id, status_devis="Sended", mail_type="devis",
            delivery_status="bounced",
        )
        EmailTracking.objects.filter(pk=failed.pk).update(
            sent_at=datetime(2026, 11, 10, 10, tzinfo=ZoneInfo("Europe/Paris"))
        )
        fake_now = datetime(2026, 11, 10, 12, tzinfo=ZoneInfo("Europe/Paris"))
        with patch("django.utils.timezone.now", return_value=fake_now):
            report = commercial_report(self.request())
            filtered = commercial_report(self.request(alert="delivery"))

        self.assertEqual(report["commercial_alert_total"], 4)
        counts = {row["key"]: row["count"] for row in report["commercial_alert_categories"]}
        self.assertEqual(counts, {
            "all": 4, "delivery": 1, "upcoming": 1,
            "followup": 3, "high_value": 2,
        })
        self.assertEqual([row["event"].id for row in filtered["commercial_alert_rows"]],
                         [issue.id])
        self.assertEqual(filtered["commercial_alert_total"], 4)
        self.assertEqual(filtered["commercial_alert_filtered_count"], 1)
        self.assertEqual(report["commercial_alert_rows"][0]["event"].id, issue.id)
        opt_row = next(row for row in report["commercial_alert_rows"]
                       if row["event"].id == opted.id)
        self.assertFalse(opt_row["email_allowed"])
        self.assertEqual(report["commercial_alert_as_of"], date(2026, 11, 10))
        self.assertNotIn(healthy.id, {row["event"].id for row
                                     in report["commercial_alert_rows"]})

    def test_alerts_use_latest_quote_delivery_and_latest_recorded_contact(self):
        future = EventDetails.objects.create(
            date_evenement="2026-12-30", adresse_evenement="Test",
            ville_evenement="Paris", code_postal_evenement=75001,
        )
        fixed = datetime(2026, 11, 10, 12, tzinfo=ZoneInfo("Europe/Paris"))
        resolved = self.event(status="Sended", proposed=250)
        failed = self.event(status="Sended", proposed=250)
        contacted = self.event(status="Sended", proposed=250)
        for event in (resolved, failed, contacted):
            Event.objects.filter(pk=event.pk).update(event_details=future)

        def mail(event, status, when):
            delivery = EmailTracking.objects.create(
                event_traced=event.id, status_devis="Sended", mail_type="devis",
                delivery_status=status,
            )
            EmailTracking.objects.filter(pk=delivery.id).update(sent_at=when)

        last_week = datetime(2026, 11, 4, 12, tzinfo=ZoneInfo("Europe/Paris"))
        yesterday = datetime(2026, 11, 9, 12, tzinfo=ZoneInfo("Europe/Paris"))
        today = datetime(2026, 11, 10, 10, tzinfo=ZoneInfo("Europe/Paris"))
        mail(resolved, "bounced", last_week)
        mail(resolved, "delivered", yesterday)
        mail(failed, "accepted", yesterday)
        mail(failed, "error", today)
        # A non-quote transactional error must not override a healthy quote.
        EmailTracking.objects.create(
            event_traced=resolved.id, status_devis="Pending",
            mail_type="confirmation", delivery_status="error",
        )
        EventRelance.objects.create(
            event=contacted, membre="test", commentaire="Contact récent",
            qualification=4, date_relance=yesterday,
        )
        with patch("django.utils.timezone.now", return_value=fixed):
            with self.assertNumQueries(3):
                report = commercial_report(self.request())

        self.assertEqual(report["commercial_alert_total"], 1)
        row = report["commercial_alert_rows"][0]
        self.assertEqual(row["event"].id, failed.id)
        self.assertEqual(row["delivery_state"], "error")
        self.assertIn("delivery", row["matched"])
        self.assertNotIn("followup", row["matched"])
        self.assertEqual(row["days_since_touch"], 1)

    def test_alerts_preserve_cohort_filters_and_staff_read_only(self):
        # A separate business dossier is the only relevant selection.
        self.event(status="Sended", proposed=1200)
        business = self.event(status="Sended", proposed=1500, business=True)
        fake_now = datetime(2026, 11, 4, 12, tzinfo=ZoneInfo("Europe/Paris"))
        with patch("django.utils.timezone.now", return_value=fake_now):
            report = commercial_report(self.request(
                segment="business", start_date="2026-11-03",
                end_date="2026-11-03", alert="high_value",
            ))
            self.assertEqual(report["commercial_alert_total"], 1)
            self.assertEqual(report["commercial_alert_rows"][0]["event"].id,
                             business.id)
            self.assertEqual(report["commercial_alert_filtered_count"], 1)
            request = self.request(segment="business", alert="high_value")
            request.user = SimpleNamespace(is_active=True, is_staff=True)
            response = graph_commercial_stats(request)
            self.assertContains(response, "Alertes commerciales")
            self.assertContains(response, "commercial-alerts")
            self.assertContains(response, "Examiner")
            self.assertContains(response, "Devis importants")
            self.assertIn("no-store", response["Cache-Control"])
            invalid = self.request(alert="not-a-category")
            invalid.user = request.user
            self.assertEqual(graph_commercial_stats(invalid).status_code, 400)
            request.user.is_staff = False
            self.assertEqual(graph_commercial_stats(request).status_code, 302)
            post = RequestFactory().post("/backend/graph/commercial/",
                                         {"alert": "delivery"})
            post.user = SimpleNamespace(is_active=True, is_staff=True)
            self.assertEqual(graph_commercial_stats(post).status_code, 405)
