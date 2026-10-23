"""Données des comparaisons Potentiel, rendues directement côté serveur.

Aucune dépendance JavaScript/Bokeh pour les histogrammes de cette page.
Les montants restent basés sur prix_proposed comme l'ancien graphique.
"""
from datetime import date, datetime, timedelta
from math import ceil


MONTH_NAMES = (
    "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
    "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
)


def _format_euros(value):
    return f"{value:,.0f}".replace(",", " ") + " €"


def _parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def prepare_potentiel_charts(events):
    """Construit 2025/2024, 2026/2025, 2027/2026 à partir des événements signés.

    events : itérable de tuples (date_evenement, prix_proposed).
    Index hebdomadaire = groupes de 7 jours à partir du 1er janvier de chaque
    année (0..52) afin de comparer les mêmes périodes calendaires.
    """
    totals = {}
    for event_date, amount in events:
        event_date = _parse_date(event_date)
        if event_date is None or event_date.year not in (2024, 2025, 2026, 2027):
            continue
        try:
            amount = float(amount or 0)
        except (ValueError, TypeError):
            continue
        if amount < 0:
            continue
        week_index = (event_date.timetuple().tm_yday - 1) // 7
        key = (event_date.year, week_index)
        totals[key] = totals.get(key, 0.0) + amount

    charts = []
    for current_year in (2025, 2026, 2027):
        previous_year = current_year - 1
        current_values = [totals.get((current_year, i), 0) for i in range(53)]
        previous_values = [totals.get((previous_year, i), 0) for i in range(53)]
        peak = max(current_values + previous_values)
        scale = max(100, ceil(peak / 100) * 100)

        week_rows = []
        for index in range(53):
            current_start = date(current_year, 1, 1) + timedelta(days=7 * index)
            previous_start = date(previous_year, 1, 1) + timedelta(days=7 * index)
            current_end = min(current_start + timedelta(days=6), date(current_year, 12, 31))
            previous_end = min(previous_start + timedelta(days=6), date(previous_year, 12, 31))

            week_rows.append({
                "current_height": round(100 * current_values[index] / scale, 2),
                "previous_height": round(100 * previous_values[index] / scale, 2),
                "tooltip": (
                    f"Période {index + 1} : "
                    f"{current_year} ({current_start:%d/%m}–{current_end:%d/%m}) : "
                    f"{_format_euros(current_values[index])} | "
                    f"{previous_year} ({previous_start:%d/%m}–{previous_end:%d/%m}) : "
                    f"{_format_euros(previous_values[index])}"
                ),
            })

        months = [
            {
                "label": MONTH_NAMES[month - 1],
                "left": round(
                    100 * (date(current_year, month, 1) - date(current_year, 1, 1)).days / 371,
                    2,
                ),
            }
            for month in range(1, 13)
        ]
        y_ticks = [
            {"bottom": tick * 25, "label": _format_euros(scale * tick / 4)}
            for tick in range(5)
        ]
        charts.append({
            "year": current_year,
            "previous_year": previous_year,
            "weeks": week_rows,
            "months": months,
            "y_ticks": y_ticks,
            "total_current": _format_euros(sum(current_values)),
            "total_previous": _format_euros(sum(previous_values)),
            "is_empty": peak == 0,
        })

    return charts
