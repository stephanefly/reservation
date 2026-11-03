from types import SimpleNamespace

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import path

from app.models import EmailTracking
from app.views.email_stats_views import graph_email_stats

urlpatterns = [path("login/", lambda request: HttpResponse("Login"), name="login"),
               path("backend/graph/emails/", graph_email_stats, name="graph_email_stats")]


@override_settings(ROOT_URLCONF=__name__)
class EmailDashboardTests(TestCase):
    def request(self, params=None, staff=True, active=True):
        request = RequestFactory().get("/backend/graph/emails/", params or {})
        request.user = SimpleNamespace(is_active=active, is_staff=staff)
        return graph_email_stats(request)

    def test_dashboard_counts_and_graphs(self):
        for opened, status in ((True, "Sended"), (False, "Sended"), (True, "First Rappel")):
            EmailTracking.objects.create(opened=opened, status_devis=status)
        response = self.request()
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("66,7 %", html)
        self.assertIn("conic-gradient", html)
        self.assertIn("Devis envoyé", html)
        self.assertIn("Première relance", html)
        self.assertIn("66.67%", html)
        self.assertNotIn("test-private-token", html)
        self.assertIn("no-store", response["Cache-Control"])

    def test_empty_and_invalid_period(self):
        response = self.request()
        self.assertContains(response, "Aucun mail suivi")
        self.assertNotContains(response, "conic-gradient")
        response = self.request({"start_date": "2026-12-01", "end_date": "2026-01-01"})
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'role="alert"', status_code=400)
        self.assertNotContains(response, "Taux d'ouverture</h2>", status_code=400)

    def test_non_staff_is_redirected_and_post_is_rejected(self):
        self.assertEqual(self.request(staff=False).status_code, 302)
        self.assertEqual(self.request(active=False).status_code, 302)
        request = RequestFactory().post("/backend/graph/emails/")
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        self.assertEqual(graph_email_stats(request).status_code, 405)
