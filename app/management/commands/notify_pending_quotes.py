"""Signaler les devis laissés à l'étape de confirmation sans envoi client."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import Event
from app.module.mail.alerts import send_admin_alert
from app.views.frontend_views import FORM_PENDING

ALERTED = FORM_PENDING + " - équipe alertée"


class Command(BaseCommand):
    help = "Notifier les devis dont la confirmation n'a pas été terminée."

    def handle(self, *args, **options):
        pending = list(Event.objects.select_related("client").filter(
            status="Initied",
            event_token__isnull=True,
            history_status=FORM_PENDING,
            created_at__lte=timezone.now() - timedelta(hours=1),
        ).order_by("created_at")[:50])
        if not pending:
            self.stdout.write("Aucune pré-demande abandonnée non signalée.")
            return

        lines = [
            f"Dossier #{event.id} - {event.client.nom} - {event.client.mail}\n"
            f"https://reservation.myselfiebooth-paris.fr/backend/info-event/{event.id}/"
            for event in pending
        ]
        body = (
            "Ces prospects ont rempli le formulaire mais n'ont pas validé "
            "la page de confirmation depuis au moins une heure.\n"
            "Les dossiers sont conservés dans le CRM.\n\n"
            + "\n\n".join(lines)
            + "\n\nVérifier manuellement avant toute prise de contact."
        )
        if not send_admin_alert(
            f"[ALERTE CRM] {len(pending)} demande(s) de devis non confirmée(s)", body
        ):
            self.stderr.write("Alerte non envoyée ; les dossiers restent visibles et seront réessayés.")
            return
        count = Event.objects.filter(
            pk__in=[event.pk for event in pending],
            status="Initied", history_status=FORM_PENDING,
            event_token__isnull=True,
        ).update(history_status=ALERTED)
        self.stdout.write(f"{count} pré-demande(s) signalée(s).")
