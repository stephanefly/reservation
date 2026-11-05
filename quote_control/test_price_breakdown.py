"""Remises conformes aux grilles brutes du PDF, sans ecriture ni fausses promotions."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from quote_control.models import AutoQuoteSettings, CatalogEntry
from quote_control.price_breakdown import decorate_offers, get_offer_breakdown
from quote_control.public_pricing import get_public_catalogue


class DiscountBreakdownTests(TestCase):
    def test_photobooth_base_450_discount_50_final_400(self):
        photo = CatalogEntry.objects.get(code="photobooth")
        details = get_offer_breakdown(photo, {"photobooth": photo})
        self.assertTrue(details["available"])
        self.assertEqual(details["reference"], 450)
        self.assertEqual(details["discount"], 50)
        self.assertEqual(details["final"], 400)

    def test_all_six_pack_bases_and_discounts_include_options(self):
        expected = {
            "souvenirs": (700, 100, 600),
            "immersion-360": (800, 100, 700),
            "signature": (950, 150, 800),
            "duo-vip": (1150, 300, 850),
            "vogue-premium": (800, 100, 700),
            "mariage-prestige": (1750, 550, 1200),
        }
        offers = decorate_offers(CatalogEntry.objects.all())
        by_code = {x.code: x for x in offers}
        for code, (base, saving, final) in expected.items():
            with self.subTest(pack=code):
                info = by_code[code].pricing
                self.assertEqual((info["reference"], info["discount"], info["final"]),
                                 (base, saving, final))
                self.assertEqual(sum(p["total"] for p in info["components"]), base)

    def test_edit_pack_price_recomputes_saving_without_extra_migration(self):
        pack = CatalogEntry.objects.get(code="duo-vip")
        pack.price = 900
        pack.save(update_fields=["price"])
        offers = decorate_offers(CatalogEntry.objects.all())
        item = next(x for x in offers if x.code == "duo-vip")
        self.assertEqual(item.pricing["reference"], 1150)
        self.assertEqual(item.pricing["discount"], 250)
        self.assertEqual(item.pricing["final"], 900)

    def test_unknown_machine_does_not_forge_a_discount(self):
        item = CatalogEntry(kind="product", code="new-booth", name="New", price=300)
        self.assertFalse(get_offer_breakdown(item, {})["available"])

    def test_price_above_reference_is_not_misrepresented_as_discount(self):
        photo = CatalogEntry.objects.get(code="photobooth")
        photo.price = 470
        info = get_offer_breakdown(photo, {photo.code: photo})
        self.assertEqual(info["discount"], 0)
        self.assertTrue(info["above_reference"])

    def test_catalogue_displays_before_discount_after_and_pack_composition(self):
        staff = User.objects.create_user("discount-staff", password="test", is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(reverse("admin_catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prix de base")
        self.assertContains(response, "450 €")
        self.assertContains(response, "Remise −50 €")
        self.assertContains(response, "Éléments séparés")
        self.assertContains(response, "Remise pack −300 €")
        self.assertContains(response, "Voir le détail des éléments")

    def test_public_prices_remain_current_without_unverified_promotion(self):
        prices = get_public_catalogue()
        self.assertEqual(prices["data_price"]["photobooth"], 400)
        self.assertEqual(prices["pack_prices"]["duo_vip"], 850)
        for page in ("tarifs", "brochure"):
            response = self.client.get(reverse(page))
            with self.subTest(page=page):
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "Remise −50 €")
                self.assertNotContains(response, "Remise −300 €")

    def test_public_price_follows_catalogue_without_promo_claim(self):
        offer = CatalogEntry.objects.get(code="photobooth")
        offer.price = 420
        offer.save(update_fields=["price"])
        prices = get_public_catalogue()
        self.assertEqual(prices["data_price"]["photobooth"], 420)
        for page in ("tarifs", "brochure"):
            response = self.client.get(reverse(page))
            self.assertContains(response, "420")
            self.assertNotContains(response, "Remise −30 €")

    def test_simulated_quote_uses_exact_engine_discounts(self):
        AutoQuoteSettings.objects.create(pk=1)
        staff = User.objects.create_user("discount-sim", password="test", is_staff=True)
        self.client.force_login(staff)
        result = self.client.get(reverse("admin_catalog"), {
            "simulate": "1", "products": ["photobooth"], "duration": "5",
            "postal_code": "75001", "source": "INSTAGRAM",
        })
        self.assertEqual(result.status_code, 200)
        data = result.context["simulation"]["price_detail"]
        self.assertEqual((data["reference"], data["discount"], data["final"]), (450, 50, 400))
        self.assertContains(result, "Prix avant remise")
        self.assertContains(result, "Remise machine")
        self.assertContains(result, "Prix final TTC")

    def test_pack_simulation_shows_pack_discount(self):
        config = AutoQuoteSettings.objects.create(pk=1)
        config.packs = ["vogue-premium"]
        config.save(update_fields=["packs"])
        staff = User.objects.create_user("pack-discount-sim", password="test", is_staff=True)
        self.client.force_login(staff)
        result = self.client.get(reverse("admin_catalog"), {
            "simulate": "1", "products": ["voguebooth"], "duration": "5",
            "options": ["PhotographeVoguebooth", "ImpressionVoguebooth"],
            "postal_code": "75001", "source": "INSTAGRAM",
        })
        self.assertEqual(result.status_code, 200)
        data = result.context["simulation"]["price_detail"]
        self.assertEqual((data["reference"], data["pack_discount"], data["final"]), (800, 100, 700))
        self.assertContains(result, "Remise pack")
