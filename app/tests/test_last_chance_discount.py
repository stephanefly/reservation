import unittest
from types import SimpleNamespace

from bs4 import BeautifulSoup

from app.module.mail.complete_mail import _handle_reduc
from app.module.mail.send_mail_event import get_mail_template


class FakeEvent:
    def __init__(self, enterprise, reduc_all=20):
        self.client = SimpleNamespace(
            nom="Entreprise Exemple" if enterprise else "Client Exemple",
            raison_sociale=enterprise,
        )
        self.reduc_all = reduc_all
        self.reduc_product = 10
        self.prix_proposed = 500
        self.event_option = SimpleNamespace(total_reduction=lambda: 0)
        self.save_count = 0

    def save(self):
        self.save_count += 1


def make_mail_soup():
    return BeautifulSoup(
        '''
        <p class="last-chance-offer">
            Nouvelle offre exclusive de <a class="reduc_all_title">-0€</a> !
        </p>
        <p class="last-chance-offer-details">
            Profitez de cette réduction avant qu'elle ne disparaisse.
        </p>
        <a class="txt_reduc"></a>
        <a class="reduc_all"></a>
        ''',
        "html.parser",
    )


class LastChanceDiscountTests(unittest.TestCase):
    def test_enterprise_keeps_price_and_agreed_discount(self):
        event = FakeEvent(enterprise=True)
        soup = make_mail_soup()

        _handle_reduc(event, soup, "last_chance_devis")

        self.assertEqual(event.reduc_all, 20)
        self.assertEqual(event.prix_proposed, 500)
        self.assertEqual(event.save_count, 0)
        self.assertIn("conditions convenues", soup.get_text(" ", strip=True))
        self.assertNotIn("Nouvelle offre exclusive", soup.get_text(" ", strip=True))
        self.assertNotIn("50€", soup.get_text(" ", strip=True))
        self.assertEqual(soup.find("a", class_="reduc_all").get_text(), "30€")

    def test_enterprise_without_prior_discount_stays_at_zero(self):
        event = FakeEvent(enterprise=True, reduc_all=0)
        event.reduc_product = 0
        soup = make_mail_soup()

        _handle_reduc(event, soup, "last_chance_devis")

        self.assertEqual(event.prix_proposed, 500)
        self.assertEqual(event.reduc_all, 0)
        self.assertEqual(event.save_count, 0)
        self.assertNotIn("réduction", soup.get_text(" ", strip=True).lower())

    def test_individual_still_receives_extra_fifty_euros(self):
        event = FakeEvent(enterprise=False)
        soup = make_mail_soup()

        _handle_reduc(event, soup, "last_chance_devis")

        self.assertEqual(event.reduc_all, 70)
        self.assertEqual(event.prix_proposed, 450)
        self.assertEqual(event.save_count, 1)
        self.assertIn("Nouvelle offre exclusive", soup.get_text(" ", strip=True))
        self.assertEqual(
            soup.find("a", class_="reduc_all_title").get_text(), "-80€"
        )

    def test_individual_with_null_discount_still_works(self):
        event = FakeEvent(enterprise=False, reduc_all=None)
        event.reduc_product = 0

        _handle_reduc(event, make_mail_soup(), "last_chance_devis")

        self.assertEqual(event.reduc_all, 50)
        self.assertEqual(event.prix_proposed, 450)

    def test_subject_only_promises_fifty_euros_to_individuals(self):
        corporate_subject = get_mail_template(
            FakeEvent(enterprise=True), "last_chance_devis"
        )[0]
        personal_subject = get_mail_template(
            FakeEvent(enterprise=False), "last_chance_devis"
        )[0]
        self.assertNotIn("50€", corporate_subject)
        self.assertIn("50€", personal_subject)


if __name__ == "__main__":
    unittest.main()
