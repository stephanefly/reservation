from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from app.models import EmailTracking


class Command(BaseCommand):
    help = "Résoudre manuellement un envoi incertain après vérification des journaux IONOS."

    def add_arguments(self, parser):
        parser.add_argument("id", type=int)
        parser.add_argument("--result", required=True, choices=["accepted", "refused"])
        parser.add_argument("--confirm", action="store_true")

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError("Vérifier le résultat de cet envoi chez IONOS, puis ajouter --confirm.")
        values = {"delivery_status": options["result"], "diagnostic": "État SMTP confirmé manuellement après vérification des journaux IONOS.", "feedback_at": timezone.now()}
        count = EmailTracking.objects.filter(pk=options["id"], delivery_status="unknown").update(**values)
        if not count:
            raise CommandError("Envoi incertain introuvable ; aucune modification.")
        self.stdout.write("État mis à jour. Aucun mail envoyé.")
