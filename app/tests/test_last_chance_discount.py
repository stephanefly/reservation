import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bs4 import BeautifulSoup

from app.module.mail.complete_mail import complete_mail
from app.module.mail.send_mail_event import get_mail_template


MAIL_TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "templates" / "mail"


class FakeEvent:
    def __init__(self, enterprise, reduc_all=20):
        self.id = 1
        self.client = SimpleNamespace(
            nom="Entreprise Exemple" if enterprise else "Client Exemple",
            mail="client@example.com",
            raison_sociale=enterprise,
        )
        self.event_details = SimpleNamespace(date_evenement=date(2026, 12, 12))
        self.event_token = "token-test"
        self.reduc_all = reduc_all
        self.reduc_product = 10
        self.prix_proposed = 500
        self.event_option = SimpleNamespace(total_reduction=lambda: 0)
        self.save_count = 0

    def save(self):
        self.save_count += 1


def render_last_chance(event):
    subject, path, files, _ = get_mail_template(event, "last_chance_devis")
    html = (MAIL_TEMPLATE_ROOT / path).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    # Le traceur nécessite une base Django ; hors de ce test unitaire.
    with patch("app.module.mail.complete_mail._handle_tracer"):
        completed = complete_mail(event, soup, "last_chance_devis")
    return subject, files, completed


class LastChanceDiscountTests(unittest.TestCase):
    def test_enterprise_no_new_discount_and_no_promotion_in_email(self):
        event = FakeEvent(enterprise=True)
        subject, attachments, soup = render_last_chance(event)
        text = soup.get_text(" ", strip=True).lower()

        self.assertEqual(event.reduc_all, 20)
        self.assertEqual(event.prix_proposed, 500)
        self.assertEqual(event.save_count, 0)
        self.assertEqual(attachments, ["devis_file"])
        self.assertIn("dernier suivi", text)
        self.assertIn("conditions commerciales", text)
        self.assertIn("12/12/2026", text)
        for forbidden in ("réduction", "remise", "nouvelle offre", "50 €", "50€"):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("50", subject)
        self.assertNotIn("réduction", subject.lower())

        self.assertEqual(
            soup.find("a", class_="mail_desabonnement")["href"],
            "https://reservation.myselfiebooth-paris.fr/desabonner/token-test"
        )

    def test_business_template_reuses_original_last_chance_visuals(self):
        private_template = BeautifulSoup(
            (MAIL_TEMPLATE_ROOT / "devis/mail_last_chance.html").read_text(encoding="utf-8"),
            "html.parser",
        )
        business_template = BeautifulSoup(
            (MAIL_TEMPLATE_ROOT / "devis/mail_last_chance_entreprise.html").read_text(encoding="utf-8"),
            "html.parser",
        )

        # Same logo, four photos, client reviews, contact block and footer.
        self.assertEqual(
            [img.get("src") for img in private_template.find_all("img", class_="image")],
            [img.get("src") for img in business_template.find_all("img", class_="image")],
        )
        self.assertEqual(
            private_template.find("img", class_="logo").get("src"),
            business_template.find("img", class_="logo").get("src"),
        )
        for class_name in ("image-table", "avis_clients", "text_fin", "contact_block", "footer"):
            self.assertIsNotNone(business_template.find(class_=class_name))
        self.assertIsNotNone(business_template.find(class_="acompte_entreprise"))
        self.assertIsNone(business_template.find("div", class_="acompte_particulier"))
        self.assertNotIn("Nouvelle offre exclusive", business_template.get_text(" ", strip=True))
        self.assertNotIn("profitez de cette réduction", business_template.get_text(" ", strip=True))

    def test_enterprise_without_prior_discount_also_keeps_price(self):
        event = FakeEvent(enterprise=True, reduc_all=0)
        event.reduc_product = 0

        _, _, soup = render_last_chance(event)
        self.assertEqual(event.reduc_all, 0)
        self.assertEqual(event.prix_proposed, 500)
        self.assertEqual(event.save_count, 0)
        self.assertNotIn("réduction", soup.get_text(" ", strip=True).lower())

    def test_private_client_keeps_existing_extra_fifty_euros(self):
        event = FakeEvent(enterprise=False)
        subject, attachments, soup = render_last_chance(event)

        self.assertEqual(event.reduc_all, 70)
        self.assertEqual(event.prix_proposed, 450)
        self.assertEqual(event.save_count, 1)
        self.assertEqual(attachments, ["devis_file"])
        self.assertIn("50€", subject)
        self.assertIn("Nouvelle offre exclusive", soup.get_text(" ", strip=True))
        self.assertEqual(soup.find("a", class_="reduc_all_title").get_text(), "-80€")

    def test_private_client_with_null_discount(self):
        event = FakeEvent(enterprise=False, reduc_all=None)
        event.reduc_product = 0
        render_last_chance(event)
        self.assertEqual(event.reduc_all, 50)
        self.assertEqual(event.prix_proposed, 450)


if __name__ == "__main__":
    unittest.main()
