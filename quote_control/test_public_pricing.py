"""Garantir que les prix affiches suivent le catalogue sans ecrire sur les devis."""
from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from app.module.data_bdd.price import PRIX_PRODUITS
from quote_control.models import AutoQuoteSettings, CatalogEntry
from quote_control.public_pricing import get_public_catalogue


class PublicCataloguePricingTests(TestCase):
    def test_ipad_price_updates_tarifs_and_brochure_without_auto_activation(self):
        ipad = CatalogEntry.objects.get(kind="product", code="ipadbooth")
        ipad.price = 200
        ipad.save(update_fields=["price"])

        # Le mode automatique n'a pas besoin d'etre active.
        config = AutoQuoteSettings.objects.create(pk=1)
        self.assertFalse(config.enabled)
        self.assertFalse(config.catalog_enabled)

        tarifs = self.client.get(reverse("tarifs"))
        self.assertEqual(tarifs.status_code, 200)
        self.assertEqual(tarifs.context["data_price"]["ipadbooth"], 200)
        ipad_card = tarifs.content.decode().split('<h3>Ipad Booth</h3>', 1)[1].split('</article>', 1)[0]
        self.assertIn("<strong>200€</strong>", ipad_card)
        self.assertNotIn("250€", ipad_card)

        brochure = self.client.get(reverse("brochure"))
        self.assertEqual(brochure.status_code, 200)
        self.assertEqual(brochure.context["data_price"]["ipadbooth"], 200)
        ipad_brochure_card = brochure.content.decode().split('<h3>Ipad Booth</h3>', 1)[1].split('</article>', 1)[0]
        self.assertIn("200 € TTC", ipad_brochure_card)
        self.assertNotIn("250 € TTC", ipad_brochure_card)

    def test_product_price_updates_without_extra_fake_discount(self):
        photo = CatalogEntry.objects.get(code="photobooth")
        photo.price = 390
        photo.save(update_fields=["price"])
        tarifs = self.client.get(reverse("tarifs"))
        photo_card = tarifs.content.decode().split('<h3>Photobooth</h3>', 1)[1].split('</article>', 1)[0]
        self.assertIn("<strong>390€</strong>", photo_card)
        self.assertNotIn("-50€", photo_card)
        self.assertNotIn("340€", photo_card)
        self.assertIn("350€", photo_card)  # La duree 3 h reste independante.

    def test_pack_changes_update_both_cards_and_no_false_savings(self):
        pack = CatalogEntry.objects.get(code="duo-vip")
        pack.price = 910
        pack.save(update_fields=["price"])
        tarifs = self.client.get(reverse("tarifs"))
        self.assertEqual(tarifs.context["pack_prices"]["duo_vip"], 910)
        self.assertContains(tarifs, "<strong>910€</strong>", html=True)
        self.assertContains(tarifs, "<strong>910 €</strong>", html=True)
        self.assertNotContains(tarifs, "300 € économisés")
        brochure = self.client.get(reverse("brochure"))
        self.assertContains(brochure, "910 € TTC")
        self.assertContains(brochure, "<strong>910 €</strong>", html=True)

    def test_inactive_items_are_hidden_but_other_items_remain(self):
        ipad = CatalogEntry.objects.get(code="ipadbooth")
        ipad.active = False
        ipad.save(update_fields=["active"])
        pack = CatalogEntry.objects.get(code="souvenirs")
        pack.active = False
        pack.save(update_fields=["active"])
        for page in ("tarifs", "brochure"):
            response = self.client.get(reverse(page))
            self.assertNotContains(response, "<h3>Ipad Booth</h3>", html=True)
            self.assertNotContains(response, "<h3>Pack Souvenirs</h3>", html=True)
            self.assertContains(response, "<h3>Photobooth</h3>", html=True)

    def test_safe_fallback_when_catalogue_table_unavailable(self):
        with patch("quote_control.public_pricing.CatalogEntry.objects.filter", side_effect=DatabaseError("table absente")):
            data = get_public_catalogue()
        self.assertEqual(data["data_price"]["ipadbooth"], 250)
        self.assertEqual(data["pack_prices"]["duo_vip"], 850)
        self.assertTrue(data["public_active"]["ipadbooth"])

    def test_public_price_change_does_not_change_historical_pdf_base(self):
        entry = CatalogEntry.objects.get(code="ipadbooth")
        entry.price = 200
        entry.save(update_fields=["price"])
        self.assertEqual(get_public_catalogue()["data_price"]["ipadbooth"], 200)
        self.assertEqual(PRIX_PRODUITS["ipadbooth"], 250)



    def test_options_render_with_photos_on_tarifs_and_brochure(self):
        CatalogEntry.objects.filter(code="MurFloral").update(image_url="")
        CatalogEntry.objects.filter(code="Fond360").update(public_enabled=False)
        for page in ("tarifs", "brochure"):
            with self.subTest(page=page):
                response = self.client.get(reverse(page))
                self.assertContains(response, 'src="/static/img/allmur.jpg"')
                self.assertContains(response, 'src="/static/img/panneaux-xxl-cinema-duo.webp"')
                self.assertNotContains(response, 'src="/static/img/fond360.jpg"')

    def test_missing_publication_columns_keep_photos_and_existing_prices(self):
        original_filter = CatalogEntry.objects.filter
        CatalogEntry.objects.filter(code="MurFloral").update(active=False)
        CatalogEntry.objects.filter(code="photobooth").update(price=390)

        def filter_catalogue(**kwargs):
            if "public_enabled" in kwargs:
                raise DatabaseError("colonne absente")
            return original_filter(**kwargs)

        with patch("quote_control.public_pricing.CatalogEntry.objects.filter", side_effect=filter_catalogue):
            data = get_public_catalogue()

        self.assertEqual(data["data_price"]["photobooth"], 390)
        images = {option["image_url"] for option in data["public_options"]}
        self.assertIn("/static/img/phonebooth.jpg", images)
        self.assertNotIn("/static/img/allmur.jpg", images)
