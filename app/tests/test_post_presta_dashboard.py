"""Tests de la synthèse post-prestation (sans accès à la base de production)."""

from types import SimpleNamespace
from unittest.mock import patch
import importlib

from django.http import HttpRequest
from django.template.loader import get_template
from django.test import SimpleTestCase

post_views = importlib.import_module("app.views.post_presta_views")


class PostPrestaDashboardTests(SimpleTestCase):
    def _context_for(self, events):
        with (
            patch.object(post_views.Event.objects, "filter") as filter_events,
            patch.object(post_views, "render") as render,
        ):
            filter_events.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = events
            post_views.post_presta(HttpRequest())
            return render.call_args.args[2]

    def test_overview_counts_only_open_events(self):
        complete = SimpleNamespace(event_post_presta=SimpleNamespace(
            collected=True, sent=True, client_paid=True, members_paid=True,
            feedback_message=False, feedback_google=True,
        ))
        incomplete = SimpleNamespace(event_post_presta=SimpleNamespace(
            collected=True, sent=False, client_paid=False, members_paid=True,
            feedback_message=False, feedback_google=False,
        ))
        without_post_record = SimpleNamespace(event_post_presta=None)

        context = self._context_for([complete, incomplete, without_post_record])

        self.assertEqual(context["post_stats"], {
            "total": 3,
            "media_pending": 2,
            "payment_pending": 2,
            "feedback_pending": 2,
        })
        self.assertEqual(context["lst_post_event"], [complete, incomplete, without_post_record])

    def test_empty_list_has_zero_counters(self):
        context = self._context_for([])
        self.assertEqual(context["post_stats"], {
            "total": 0,
            "media_pending": 0,
            "payment_pending": 0,
            "feedback_pending": 0,
        })

    def test_template_compiles(self):
        self.assertIsNotNone(get_template("app/backend/post_presta.html"))
