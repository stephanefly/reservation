from datetime import date
from unittest import TestCase

from app.module.lib_graph.potentiel_statique import prepare_potentiel_charts


class StaticPotentielChartTests(TestCase):
    def test_three_comparisons_and_same_week_aggregation(self):
        rows = [
            (date(2024, 1, 1), 100),
            (date(2024, 1, 7), 50),
            (date(2024, 1, 8), 40),
            (date(2025, 1, 2), 200),
            (date(2025, 1, 4), 60),
            (date(2026, 1, 3), 320),
            (date(2027, 1, 1), 500),
        ]
        charts = prepare_potentiel_charts(rows)
        self.assertEqual([chart['year'] for chart in charts], [2025, 2026, 2027])
        self.assertEqual(len(charts[0]['weeks']), 53)
        self.assertEqual(len(charts[1]['months']), 12)
        self.assertEqual(charts[0]['total_previous'], '190 €')
        self.assertEqual(charts[0]['total_current'], '260 €')
        self.assertEqual(charts[0]['weeks'][0]['current_height'], 65)
        self.assertGreater(charts[1]['weeks'][0]['current_height'], 0)
        self.assertGreater(charts[2]['weeks'][0]['current_height'], 0)
        self.assertIn('2024', charts[0]['weeks'][0]['tooltip'])

    def test_prior_year_remains_visible_without_any_2027_booking(self):
        charts = prepare_potentiel_charts([
            (date(2025, 4, 10), 400),
            (date(2026, 4, 10), 1000),
        ])
        self.assertEqual(charts[2]['total_current'], '0 €')
        self.assertEqual(charts[2]['total_previous'], '1 000 €')
        self.assertFalse(charts[2]['is_empty'])
        self.assertTrue(any(week['previous_height'] > 0 for week in charts[2]['weeks']))

    def test_empty_or_malformed_data_produces_visible_empty_states(self):
        charts = prepare_potentiel_charts([
            (None, 500),
            ('bad date', 100),
            (date(2028, 1, 1), 200),
            (date(2024, 1, 1), 'bad price'),
        ])
        self.assertEqual(len(charts), 3)
        self.assertTrue(all(chart['is_empty'] for chart in charts))
        self.assertTrue(all(len(chart['y_ticks']) == 5 for chart in charts))

    def test_leap_year_end_of_december(self):
        charts = prepare_potentiel_charts([
            (date(2024, 12, 31), 250),
            (date(2025, 12, 31), 180),
        ])
        self.assertEqual(charts[0]['total_previous'], '250 €')
        self.assertEqual(charts[0]['total_current'], '180 €')
        self.assertGreater(charts[0]['weeks'][52]['previous_height'], 0)
        self.assertGreater(charts[0]['weeks'][52]['current_height'], 0)
