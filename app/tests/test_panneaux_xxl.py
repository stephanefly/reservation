import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.module.data_bdd.panneau_xxl import appliquer_panneaux, quantite_panneaux
from app.module.data_bdd.event_pricing import calculate_option_total
from app.module.devis_pdf.make_table import prix_ligne_option
from app.tests.test_event_pricing import FakeEventOption


class PanneauxXXLTests(unittest.TestCase):
    def test_opt_in_and_default(self):
        self.assertEqual(quantite_panneaux({"panneaux_xxl": "6"}), 0)
        self.assertEqual(quantite_panneaux({"avec_panneaux": "on"}), 4)
        for valeur in ("0", "-1", "7", "1.5", "quatre"):
            with self.assertRaises(ValueError):
                quantite_panneaux({"avec_panneaux": "on", "panneaux_xxl": valeur})

    def test_forfaits_match_quote_after_discount(self):
        option = FakeEventOption()
        for q, prix in enumerate((150, 300, 350, 400, 450, 500), start=1):
            appliquer_panneaux(option, q, 25)
            lignes, total = prix_ligne_option(SimpleNamespace(event_option=option), [])
            self.assertEqual(total, prix - 25)
            self.assertEqual(calculate_option_total(option), total)
            self.assertEqual(lignes[0][2:], [str(q), "25 €", f"{total} €"])

    def test_keep_agreed_price_and_clear_when_removed(self):
        option = FakeEventOption()
        appliquer_panneaux(option, 4)
        with patch.dict("app.module.data_bdd.panneau_xxl.TARIFS_PANNEAUX", {4: 499}):
            appliquer_panneaux(option, 4, 50)
        self.assertEqual(calculate_option_total(option), 350)
        with self.assertRaises(ValueError):
            appliquer_panneaux(option, 4, 401)
        appliquer_panneaux(option, 0, 50)
        self.assertEqual(calculate_option_total(option), 0)
        self.assertEqual(option.panneaux_remise, 0)
