from datetime import date
from types import SimpleNamespace
from unittest import TestCase

from app.module.espace_client.dashboard import build_dashboard_context, format_time


class ClientDashboardContextTests(TestCase):
    @staticmethod
    def make_event(
        *,
        event_date=date(2026, 8, 15),
        start='18:30',
        duration=4,
        text='Stéphane & Camille',
        design='https://example.com/modele',
        music='https://example.com/musique',
        need_design=True,
        need_music=True,
        floral=True,
        floral_style='gatsby',
    ):
        return SimpleNamespace(
            event_details=SimpleNamespace(date_evenement=event_date, horaire=start),
            event_product=SimpleNamespace(
                need_design=lambda: need_design,
                need_music=lambda: need_music,
            ),
            event_option=SimpleNamespace(
                duree=duration,
                MurFloral=floral,
                mur_floral_style=floral_style,
            ),
            event_template=SimpleNamespace(
                text_template=text,
                url_modele=design,
                url_music_360=music,
            ),
        )

    def test_complete_event_summary(self):
        event = self.make_event()

        context = build_dashboard_context(event, reference_date=date(2026, 7, 31))

        self.assertEqual(context['completion_percentage'], 100)
        self.assertEqual(context['completed_steps'], 5)
        self.assertEqual(context['missing_steps'], 0)
        self.assertEqual(context['event_countdown'], 'Dans 15 jours')
        self.assertEqual(context['event_date_display'], 'samedi 15 août 2026')
        self.assertEqual(context['installation_time'], '17h30')
        self.assertEqual(context['start_time'], '18h30')
        self.assertEqual(context['end_time'], '22h30')

    def test_missing_information_and_midnight_rollover(self):
        event = self.make_event(
            event_date=date(2026, 7, 31),
            start='00:30',
            duration=2,
            text='',
            design='',
            need_music=False,
            floral=False,
        )

        context = build_dashboard_context(event, reference_date=date(2026, 7, 31))

        self.assertEqual(context['completion_percentage'], 33)
        self.assertEqual(context['missing_steps'], 2)
        self.assertEqual(context['event_countdown'], "C'est aujourd'hui")
        self.assertEqual(context['installation_time'], '23h30')
        self.assertEqual(context['end_time'], '02h30')

    def test_invalid_time_is_ignored(self):
        self.assertIsNone(format_time('à définir'))
