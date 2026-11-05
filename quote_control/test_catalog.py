"""Tests du catalogue dans une base de test, sans identifiants PythonAnywhere."""
from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .catalog import PACKS
from .catalog_forms import CatalogEntryForm
from .engine import analyse_quote
from .models import AutoQuoteSettings, CatalogEntry
from .tests import fake_event, settings_stub


class CatalogueAdminTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("catalog-staff", password="test", is_staff=True)
        self.visitor = User.objects.create_user("catalog-visitor", password="test")
        self.url = reverse("admin_catalog")

    def test_seed_contains_all_current_products_options_packs(self):
        self.assertEqual(CatalogEntry.objects.filter(kind="product").count(), 6)
        self.assertGreaterEqual(CatalogEntry.objects.filter(kind="option").count(), 14)
        self.assertEqual(CatalogEntry.objects.filter(kind="pack").count(), len(PACKS))
        self.assertFalse(CatalogEntry.objects.filter(auto_enabled=True).exists())

    def test_staff_required_get_and_post(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.client.post(self.url, {"name": "Refuse"}).status_code, 302)
        self.client.force_login(self.visitor)
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Catalogue commercial")

    def test_create_new_manual_offer_and_edit_without_changing_identity(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, {
            "kind": "product", "code": "booth-premium-nouveau",
            "name": "Booth Premium", "price": 999, "active": "on",
        })
        self.assertEqual(response.status_code, 302)
        entry = CatalogEntry.objects.get(code="booth-premium-nouveau")
        self.assertFalse(entry.auto_enabled)
        response = self.client.post(self.url, {
            "entry": entry.pk, "kind": "pack", "code": "tentative-renommage",
            "name": "Booth Premium 2", "price": 899,
        })
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.code, "booth-premium-nouveau")
        self.assertEqual(entry.kind, "product")
        self.assertEqual(entry.price, 899)
        self.assertFalse(entry.active)

    def test_create_custom_pack_composition(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, {
            "kind": "pack", "code": "pack-personnalise", "name": "Pack Personnalise",
            "price": 990, "active": "on", "product_codes": ["photobooth"],
            "option_codes": ["Phonebooth"], "quantity_PorteCles": 60,
        })
        self.assertEqual(response.status_code, 302)
        item = CatalogEntry.objects.get(code="pack-personnalise")
        self.assertEqual(item.product_codes, ["photobooth"])
        self.assertEqual(item.option_codes, ["Phonebooth"])
        self.assertEqual(item.quantities, {"PorteCles": 60})
        self.assertFalse(item.auto_enabled)

    def test_catalog_auto_rejects_unsupported_and_too_cheap_offers(self):
        for data in (
            {"kind": "product", "code": "inconnu", "name": "Inconnu",
             "price": 800, "active": True, "auto_enabled": True},
            {"kind": "product", "code": "photobooth", "name": "Trop bas",
             "price": 200, "active": True, "auto_enabled": True},
            {"kind": "option", "code": "Phonebooth", "name": "Phonebooth",
             "price": 100, "active": True, "auto_enabled": True},
            {"kind": "pack", "code": "pack-invalide", "name": "Pack invalide",
             "price": 900, "active": True, "auto_enabled": True,
             "product_codes": ["machine-inconnue"]},
        ):
            form = CatalogEntryForm(data=data)
            with self.subTest(code=data["code"]):
                self.assertFalse(form.is_valid())

    def test_nonexistent_or_invalid_id_fails_closed(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url + "?edit=abc").status_code, 404)
        self.assertEqual(self.client.get(self.url + "?edit=999999").status_code, 404)


class CatalogueEngineTests(TestCase):
    def test_legacy_prices_unchanged_until_switch(self):
        item = CatalogEntry.objects.get(code="photobooth")
        item.price = 375
        item.auto_enabled = True
        item.save()
        config = settings_stub()
        config.catalog_enabled = False
        result = analyse_quote(fake_event(photobooth=True), config, preview=True)
        self.assertEqual(result["amount"], 400)

    def test_product_price_from_catalogue_only_after_opt_in(self):
        item = CatalogEntry.objects.get(code="photobooth")
        item.price = 375
        item.auto_enabled = True
        item.save()
        config = settings_stub()
        config.catalog_enabled = True
        result = analyse_quote(fake_event(photobooth=True), config, preview=True)
        self.assertTrue(result["eligible"], result)
        self.assertEqual(result["amount"], 375)
        self.assertEqual(result["calculation"]["reduc_product"], 75)
        # 3 h : toujours le tarif historique valide.
        result3 = analyse_quote(fake_event(photobooth=True, duree=3), config, preview=True)
        self.assertEqual(result3["amount"], 350)

    def test_pack_composition_can_be_edited_without_touching_legacy(self):
        item = CatalogEntry.objects.get(code="vogue-premium")
        item.price = 690
        item.auto_enabled = True
        item.save()
        config = settings_stub()
        config.catalog_enabled = True
        event = fake_event(voguebooth=True, PhotographeVoguebooth=True, ImpressionVoguebooth=True)
        result = analyse_quote(event, config, preview=True)
        self.assertTrue(result["eligible"], result)
        self.assertEqual(result["amount"], 690)
        self.assertEqual(result["pack"], "vogue-premium")

    def test_ambiguous_duplicate_packs_stay_manual(self):
        item = CatalogEntry.objects.get(code="vogue-premium")
        item.auto_enabled = True
        item.save()
        CatalogEntry.objects.create(
            kind="pack", code="vogue-premium-bis", name="Pack bis", price=700,
            product_codes=["voguebooth"],
            option_codes=["PhotographeVoguebooth", "ImpressionVoguebooth"],
            auto_enabled=True,
        )
        config = settings_stub()
        config.catalog_enabled = True
        result = analyse_quote(fake_event(voguebooth=True,
                               PhotographeVoguebooth=True, ImpressionVoguebooth=True),
                               config, preview=True)
        self.assertFalse(result["eligible"])
        self.assertIn("Plusieurs", result["reason"])

    def test_disabled_pack_never_falls_back_to_machine(self):
        pack = CatalogEntry.objects.get(code="vogue-premium")
        pack.auto_enabled = False
        pack.save()
        machine = CatalogEntry.objects.get(code="voguebooth")
        machine.auto_enabled = True
        machine.save()
        config = settings_stub()
        config.catalog_enabled = True
        result = analyse_quote(fake_event(voguebooth=True,
                               PhotographeVoguebooth=True, ImpressionVoguebooth=True),
                               config, preview=True)
        self.assertFalse(result["eligible"])
        self.assertIn("Pack", result["reason"])

    def test_invalid_option_prices_force_manual_to_protect_pdf(self):
        option = CatalogEntry.objects.get(code="Phonebooth")
        option.price = 90
        option.save()
        machine = CatalogEntry.objects.get(code="photobooth")
        machine.auto_enabled = True
        machine.save()
        config = settings_stub()
        config.catalog_enabled = True
        result = analyse_quote(fake_event(photobooth=True, Phonebooth=True), config, preview=True)
        self.assertFalse(result["eligible"])
        self.assertIn("PDF", result["reason"])

    def test_recommendations_and_businesses_stay_manual(self):
        config = settings_stub()
        config.catalog_enabled = True
        for e in (fake_event(source="RECOMMENDATION", photobooth=True),
                  fake_event(source="INSTAGRAM", entreprise=True, photobooth=True)):
            self.assertFalse(analyse_quote(e, config, preview=True)["eligible"])

    def test_catalogue_off_by_default_after_create_settings(self):
        config = AutoQuoteSettings.objects.create(pk=1)
        self.assertFalse(config.catalog_enabled)
        self.assertFalse(config.enabled)
