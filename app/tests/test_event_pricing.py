import unittest
from types import SimpleNamespace

from app.module.data_bdd.event_pricing import (
    OPTION_NAMES,
    calculate_option_total,
    parse_int,
    update_event_option,
)


class FakeEventOption:
    def __init__(self):
        self.saved = 0
        self.magnets = 0
        self.PorteCles = 0
        self.MagnetsSimple = 0
        self.magnets_reduc_prix = 0
        self.PorteCles_reduc_prix = 0
        self.MagnetsSimple_reduc_prix = 0
        self.mur_floral_style = None
        self.livraison = False
        self.duree = 0

        for option_name in OPTION_NAMES:
            setattr(self, option_name, False)
            setattr(self, f"{option_name}_reduc_prix", 0)
            setattr(self, f"prix_base_{option_name}", lambda: 50)

    def prix_base_magnets(self, quantity):
        return quantity * 2

    def prix_base_PorteCles(self, quantity):
        return quantity * 2

    def prix_base_MagnetsSimple(self, quantity):
        return quantity * 2

    def save(self):
        self.saved += 1


class EventPricingTests(unittest.TestCase):
    def test_parse_int_accepts_numbers_and_defaults_invalid_values(self):
        self.assertEqual(parse_int(" 12 "), 12)
        self.assertEqual(parse_int(7), 7)
        self.assertEqual(parse_int(""), 0)
        self.assertEqual(parse_int("invalide", 3), 3)

    def test_calculate_total_uses_quantity_reductions(self):
        option = FakeEventOption()
        option.Phonebooth = True
        option.Phonebooth_reduc_prix = 10
        option.magnets = 10
        option.magnets_reduc_prix = 2
        option.PorteCles = 20
        option.PorteCles_reduc_prix = 5

        self.assertEqual(calculate_option_total(option), 93)

    def test_update_clears_inactive_options_and_saves_once(self):
        option = FakeEventOption()
        option.Phonebooth = True
        option.mur_floral_style = "gatsby"
        request = SimpleNamespace(POST={"LivreOr": "on", "LivreOr_reduc_prix": "5", "duree": "4"})

        total = update_event_option(request, option)

        self.assertFalse(option.Phonebooth)
        self.assertTrue(option.LivreOr)
        self.assertIsNone(option.mur_floral_style)
        self.assertEqual(option.duree, 4)
        self.assertEqual(option.saved, 1)
        self.assertEqual(total, 45)


if __name__ == "__main__":
    unittest.main()
