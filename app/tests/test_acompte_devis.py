from decimal import Decimal
from unittest import TestCase

from app.module.devis_pdf.make_table import acompte_particulier


class AcompteDevisTests(TestCase):
    def test_seuils_du_total_net(self):
        for total, attendu in [('599.99', 50), ('600', 100), ('999.99', 100), ('1000', 150)]:
            with self.subTest(total=total):
                self.assertEqual(acompte_particulier(Decimal(total)), attendu)
