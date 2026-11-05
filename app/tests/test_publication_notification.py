"""Tests des alertes internes de publication, sans requête SMTP ni pCloud réelle."""

import json
from contextlib import nullcontext
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase

from app.module.mail import post_presta_publication as publication
from app.views import post_presta_views


class PublicationMailTests(SimpleTestCase):
    def setUp(self):
        self.event = SimpleNamespace(
            id=42,
            status="Post Presta",
            client=SimpleNamespace(nom="Soirée Exemple"),
            event_details=SimpleNamespace(date_evenement=date(2026, 11, 5)),
            event_template=SimpleNamespace(directory_name="2026-11-05 EXEMPLE"),
        )

    @patch.object(publication, "submit", return_value=True)
    @patch.object(publication.EmailTracking.objects, "create")
    @patch.object(publication.EmailTracking.objects, "filter")
    @patch.object(publication, "get_pcloud_link_event_folder",
                  return_value="https://u.pcloud.link/publink/show?code=TEST")
    @patch.object(publication, "get_pcloud_event_folder_data",
                  return_value={"folderid": 123})
    def test_notification_has_fresh_folder_link_and_is_tracked(
        self, get_folder, get_link, filter_tracking, create_tracking, submit
    ):
        filter_tracking.return_value.exists.return_value = False
        create_tracking.return_value = SimpleNamespace(recipient="test@example.org")
        self.assertTrue(publication.send_post_presta_publication_mail(self.event))
        get_folder.assert_called_once_with("2026-11-05 EXEMPLE")
        get_link.assert_called_once_with({"folderid": 123})
        self.assertEqual(create_tracking.call_args.kwargs["mail_type"], "publication_a_poster")
        self.assertEqual(create_tracking.call_args.kwargs["event_traced"], 42)
        msg = submit.call_args.args[1]
        self.assertIn("[À PUBLIER]", str(msg["Subject"]))
        self.assertIn("https://u.pcloud.link/publink/show?code=TEST", msg.get_payload(decode=True).decode("utf-8"))
        self.assertIn("autorisation", msg.get_payload(decode=True).decode("utf-8").lower())

    @patch.object(publication, "submit")
    @patch.object(publication.EmailTracking.objects, "filter")
    @patch.object(publication, "get_pcloud_event_folder_data", return_value=None)
    def test_missing_folder_does_not_send_email(self, get_folder, filter_tracking, submit):
        filter_tracking.return_value.exists.return_value = False
        with self.assertRaisesMessage(ValueError, "introuvable"):
            publication.send_post_presta_publication_mail(self.event)
        submit.assert_not_called()

    @patch.object(publication, "submit")
    @patch.object(publication.EmailTracking.objects, "filter")
    def test_uncertain_prior_send_requires_review(self, filter_tracking, submit):
        filter_tracking.return_value.exists.return_value = True
        with self.assertRaisesMessage(ValueError, "incertain"):
            publication.send_post_presta_publication_mail(self.event)
        submit.assert_not_called()


class PublicationStatusTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.post_presta = SimpleNamespace(pk=7, go_post_photo=None, save=Mock())
        self.event = SimpleNamespace(id=42)

    def request(self, value):
        request = self.factory.post(
            "/post-presta/7/go_post_photo/",
            data=json.dumps({"value": value}),
            content_type="application/json",
        )
        request.user = SimpleNamespace(is_authenticated=True)
        return request

    def call_update(self, value, post_record=None):
        post_record = post_record or self.post_presta
        with (
            patch.object(post_presta_views.transaction, "atomic", return_value=nullcontext()),
            patch.object(post_presta_views.EventPostPrestation.objects, "select_for_update"),
            patch.object(post_presta_views, "get_object_or_404") as get_or_404,
            patch.object(post_presta_views, "send_post_presta_publication_mail") as mail,
        ):
            get_or_404.side_effect = [post_record, self.event]
            response = post_presta_views.update_post_presta_status(
                self.request(value), post_record.pk, "go_post_photo"
            )
        return response, mail

    def test_first_yes_sends_one_notification(self):
        response, mail = self.call_update("oui")
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["notification_sent"])
        self.assertEqual(self.post_presta.go_post_photo, "oui")
        mail.assert_called_once_with(self.event)

    def test_saving_yes_again_does_not_send_duplicate(self):
        self.post_presta.go_post_photo = "oui"
        response, mail = self.call_update("oui")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("notification_sent", json.loads(response.content))
        mail.assert_not_called()

    def test_no_or_undefined_do_not_trigger_email(self):
        for value in ("non", "à définir", None):
            response, mail = self.call_update(value)
            self.assertEqual(response.status_code, 200)
            mail.assert_not_called()

    def test_failed_email_keeps_status_and_shows_warning(self):
        with (
            patch.object(post_presta_views.transaction, "atomic", return_value=nullcontext()),
            patch.object(post_presta_views.EventPostPrestation.objects, "select_for_update"),
            patch.object(post_presta_views, "get_object_or_404", side_effect=[self.post_presta, self.event]),
            patch.object(post_presta_views, "send_post_presta_publication_mail",
                         side_effect=RuntimeError("SMTP indisponible")),
            patch.object(post_presta_views.logger, "exception"),
        ):
            response = post_presta_views.update_post_presta_status(
                self.request("oui"), 7, "go_post_photo"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post_presta.go_post_photo, "oui")
        self.assertFalse(json.loads(response.content)["notification_sent"])

    def test_renvoi_refuse_si_pas_a_poster(self):
        self.post_presta.go_post_photo = "non"
        request = self.factory.post("/post-presta/notification-publication/7/")
        request.user = SimpleNamespace(is_authenticated=True)
        with (
            patch.object(post_presta_views, "get_object_or_404", return_value=self.post_presta),
            patch.object(post_presta_views, "send_post_presta_publication_mail") as mail,
        ):
            response = post_presta_views.resend_publication_notification(request, 7)
        self.assertEqual(response.status_code, 400)
        mail.assert_not_called()

    def test_renvoi_explicite_si_oui(self):
        self.post_presta.go_post_photo = "oui"
        request = self.factory.post("/post-presta/notification-publication/7/")
        request.user = SimpleNamespace(is_authenticated=True)
        with (
            patch.object(post_presta_views, "get_object_or_404", side_effect=[self.post_presta, self.event]),
            patch.object(post_presta_views, "send_post_presta_publication_mail") as mail,
        ):
            response = post_presta_views.resend_publication_notification(request, 7)
        self.assertEqual(response.status_code, 200)
        mail.assert_called_once_with(self.event)
