"""Tests des règles, du tableau de bord et de la simulation des devis."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.urls import reverse

from app.models import Client, Event, EventDetails, EventOption, EventProduct
from .catalog import default_pack_prices, default_product_prices, default_products, default_sources, PACKS
from .engine import analyse_quote
from .models import AutoQuoteLog, AutoQuoteSettings
from .service import process_instant_quote


def fake_event(source="INSTAGRAM", entreprise=False, duree=5, code_postal=75001, **flags):
    selection = {key: bool(flags.get(key, False)) for key in (
        "photobooth", "miroirbooth", "videobooth", "voguebooth", "airbooth", "ipadbooth",
    )}
    option_fields = {key: value for key, value in flags.items() if key not in selection}
    return SimpleNamespace(
        client=Client(how_find=source, raison_sociale=entreprise),
        event_product=EventProduct(**selection),
        event_option=EventOption(duree=duree, **option_fields),
        event_details=EventDetails(code_postal_evenement=code_postal),
    )


def settings_stub():
    return SimpleNamespace(
        enabled=False,
        sources=default_sources(),
        products=default_products(),
        packs=[pack[0] for pack in PACKS],
        product_prices=default_product_prices(),
        pack_prices=default_pack_prices(),
    )


class QuoteEngineTests(TestCase):
    def test_recommendation_always_manual_even_if_selected_elsewhere(self):
        config = settings_stub()
        config.sources += ["RECOMMANDATION", "RECOMMENDATION"]
        for source in ["RECOMMANDATION", "RECOMMENDATION", " recommandation "]:
            event = fake_event(source=source, photobooth=True)
            result = analyse_quote(event, config, preview=True)
            self.assertFalse(result["eligible"])
            self.assertIn("Recommandation", result["reason"])

    def test_business_always_manual(self):
        result = analyse_quote(fake_event(entreprise=True, photobooth=True), settings_stub(), preview=True)
        self.assertFalse(result["eligible"])

    def test_photobooth_5h_400_and_3h_350(self):
        config = settings_stub()
        p5 = analyse_quote(fake_event(photobooth=True), config, preview=True)
        p3 = analyse_quote(fake_event(photobooth=True, duree=3), config, preview=True)
        self.assertEqual(p5["amount"], 400)
        self.assertEqual(p5["calculation"]["reduc_product"], 50)
        self.assertEqual(p3["amount"], 350)

    def test_vogue_550_with_150_photographer_and_100_printing(self):
        config = settings_stub()
        config.products = ["voguebooth"]
        e = fake_event(voguebooth=True)
        self.assertEqual(analyse_quote(e, config, preview=True)["amount"], 550)
        e.event_option.PhotographeVoguebooth = True
        e.event_option.ImpressionVoguebooth = True
        result = analyse_quote(e, config, preview=True)
        self.assertEqual(result["amount"], 700)
        self.assertEqual(result["label"], "Pack Vogue Premium")
        self.assertEqual(result["calculation"]["reduc_all"], 100)

    def test_all_six_packs_match_prices(self):
        for key, price in [
            ("souvenirs", 600), ("immersion-360", 700), ("signature", 800),
            ("duo-vip", 850), ("vogue-premium", 700), ("mariage-prestige", 1200),
        ]:
            pack = next(item for item in PACKS if item[0] == key)
            flags = {name: True for name in pack[2]}
            flags.update({name: True for name in pack[3]})
            flags.update({field: quantity for field, quantity in pack[4]})
            result = analyse_quote(fake_event(**flags), settings_stub(), preview=True)
            with self.subTest(pack=key):
                self.assertTrue(result["eligible"], result)
                self.assertEqual(result["amount"], price)
                self.assertEqual(result["pack"], key)

    def test_extra_option_and_delivery_added_to_pack(self):
        config = settings_stub()
        event = fake_event(voguebooth=True, PhotographeVoguebooth=True,
                           ImpressionVoguebooth=True, LivreOr=True, code_postal=62000)
        result = analyse_quote(event, config, preview=True)
        self.assertEqual(result["amount"], 700 + 70 + 100)

    def test_disabled_pack_does_not_become_full_price_quote(self):
        config = settings_stub()
        config.products = ["voguebooth"]
        config.packs = []
        result = analyse_quote(fake_event(voguebooth=True,
                        PhotographeVoguebooth=True, ImpressionVoguebooth=True), config, preview=True)
        self.assertFalse(result["eligible"])
        self.assertIn("Pack", result["reason"])

    def test_missing_config_and_long_duration_are_manual(self):
        config = settings_stub()
        event = fake_event(photobooth=True, duree=7)
        self.assertFalse(analyse_quote(event, config, preview=True)["eligible"])
        config.enabled = False
        self.assertFalse(analyse_quote(fake_event(photobooth=True), config)["eligible"])


class QuoteControlViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff-auto", password="test-password", is_staff=True)
        self.user = User.objects.create_user(username="ordinary-auto", password="test-password")
        self.url = reverse("admin_auto_quotes")

    def test_staff_only_and_default_disabled(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/backend/catalogue/", response["Location"])
        canonical = self.client.get(response["Location"])
        self.assertContains(canonical, "Paramétrage des devis")
        self.assertFalse(AutoQuoteSettings.objects.get(pk=1).enabled)

    def test_save_prices_sources_and_activation_requires_confirmation(self):
        self.client.force_login(self.staff)
        self.client.get(self.url)
        fields = {
            "enabled": "on",
            "sources": ["INSTAGRAM"],
            "products": ["photobooth"],
            "packs": ["vogue-premium"],
        }
        fields.update({"product_" + k: v for k, v in default_product_prices().items()})
        fields.update({"pack_" + k: v for k, v in default_pack_prices().items()})
        fields["pack_vogue-premium"] = 700
        response = self.client.post(self.url, fields)
        self.assertContains(response, "Confirmez que les prix")
        self.assertFalse(AutoQuoteSettings.objects.get(pk=1).enabled)
        fields["confirm_activation"] = "on"
        response = self.client.post(self.url, fields)
        self.assertEqual(response.status_code, 302)
        config = AutoQuoteSettings.objects.get(pk=1)
        self.assertTrue(config.enabled)
        self.assertEqual(config.sources, ["INSTAGRAM"])
        self.assertEqual(config.packs, ["vogue-premium"])
        self.assertEqual(config.pack_prices["vogue-premium"], 700)

    def test_recommendation_cannot_be_authorized_by_form(self):
        self.client.force_login(self.staff)
        fields = {
            "sources": ["RECOMMANDATION"],
            "products": [],
            "packs": [],
        }
        fields.update({"product_" + k: v for k, v in default_product_prices().items()})
        fields.update({"pack_" + k: v for k, v in default_pack_prices().items()})
        response = self.client.post(self.url, fields)
        self.assertEqual(response.status_code, 200)
        self.assertIn("sources", response.context["settings_form"].errors)
        self.assertFalse(AutoQuoteSettings.objects.get(pk=1).enabled)

    def test_simulation_is_read_only_and_pdf_is_private(self):
        self.client.force_login(self.staff)
        config = AutoQuoteSettings.objects.create(id=1)
        client = Client.objects.create(nom="Test", mail="test@example.invalid",
                       numero_telephone="0100000000", how_find="INSTAGRAM")
        details = EventDetails.objects.create(date_evenement=date(2027, 3, 12),
                     adresse_evenement="1 rue Exemple", ville_evenement="Paris",
                     code_postal_evenement=75001)
        product = EventProduct.objects.create(photobooth=True)
        option = EventOption.objects.create(duree=5)
        event = Event.objects.create(
            client=client, event_details=details, event_product=product,
            event_option=option, prix_brut=0, num_devis=100,
        )
        response = self.client.get(self.url, {"event": event.pk}, follow=True)
        self.assertContains(response, "400")
        self.assertFalse(AutoQuoteLog.objects.exists())
        event.refresh_from_db()
        self.assertEqual(event.prix_brut, 0)
        pdf_url = reverse("admin_auto_quotes_preview_pdf", kwargs={"event_id": event.pk})
        pdf = self.client.get(pdf_url)
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        event.refresh_from_db()
        self.assertEqual(event.prix_brut, 0)

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(pdf_url).status_code, 302)

    def test_service_leaves_disabled_request_untouched(self):
        event = fake_event(photobooth=True)
        event.pk = 99
        event.save = Mock()
        sender = Mock()
        self.assertFalse(process_instant_quote(event, sender))
        sender.assert_not_called()
        event.save.assert_not_called()
        self.assertFalse(AutoQuoteLog.objects.exists())
