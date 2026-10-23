from unittest import TestCase

import pandas as pd

from app.module.lib_graph.lib_graph_all import (
    _potentiel_totaux_hebdomadaires,
    tracage_figure_bar_potentiel,
)


class PotentielGraphTests(TestCase):
    def test_totaux_par_semaine_et_annee(self):
        evenements = pd.DataFrame({
            'Date-Event': [
                '2024-01-01', '2024-01-07', '2024-01-08',
                '2025-01-02', '2025-01-09',
                '2026-12-31', '2027-07-01', None,
            ],
            'Prix': [100, 50, 25, 200, 70, 400, 500, 600],
        })

        totaux = _potentiel_totaux_hebdomadaires(evenements)

        self.assertEqual(totaux[(2024, 0)], 150)
        self.assertEqual(totaux[(2024, 1)], 25)
        self.assertEqual(totaux[(2025, 0)], 200)
        self.assertEqual(totaux[(2025, 1)], 70)
        self.assertEqual(totaux[(2026, 52)], 400)
        self.assertNotIn((2027, 0), totaux)

    def test_trois_graphes_sont_generes_meme_sans_reservation_2027(self):
        evenements = pd.DataFrame({
            'Date-Event': ['2024-04-15', '2025-04-15', '2026-04-15'],
            'Prix': [400, 500, 700],
        })

        script, divs = tracage_figure_bar_potentiel(evenements)

        self.assertIsInstance(script, str)
        self.assertEqual(len(divs), 3)
        # Une seule ressource embarquée, contenant les trois titres.
        for index, annee in enumerate((2025, 2026, 2027)):
            self.assertIn(f"Potentiel pour {annee} par rapport", script)
            self.assertIn('<div', divs[index])

    def test_dataframe_vide_ne_fait_pas_echouer_les_graphes(self):
        evenements = pd.DataFrame(columns=['Date-Event', 'Prix'])

        self.assertEqual(_potentiel_totaux_hebdomadaires(evenements), {})
        script, divs = tracage_figure_bar_potentiel(evenements)

        self.assertIsInstance(script, str)
        self.assertEqual(len(divs), 3)
