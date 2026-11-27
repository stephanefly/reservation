from smtplib import SMTPResponseException
import fcntl
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

from newsletter.models import Campaign, Configuration, Delivery
from newsletter.services import build_message, has_capacity, smtp_settings, still_eligible


class Command(BaseCommand):
    help = "Traite un lot de newsletters confirmées sur cet hôte."

    def add_arguments(self, parser):
        parser.add_argument("--lock-file", type=Path, required=True)
        parser.add_argument("--batch-size", type=int, default=50)

    def handle(self, *args, lock_file, batch_size, **options):
        if not getattr(settings, "NEWSLETTER_AVAILABLE", False):
            return
        if not 1 <= batch_size <= 1000:
            raise CommandError("La taille du lot doit être comprise entre 1 et 1000.")
        with lock_file.open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return
            self.process(batch_size)

    def process(self, batch_size):
        config = Configuration.objects.filter(pk=1, enabled=True, sender__gt="").first()
        if not config:
            return
        try:
            smtp = smtp_settings()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        status = Delivery.Status
        Delivery.objects.filter(status=status.SENDING).update(
            status=status.UNCERTAIN, error="Interruption pendant l'envoi SMTP."
        )
        due = Campaign.objects.filter(status=Campaign.Status.QUEUED,
                                      scheduled_at__lte=timezone.now(),
                                      confirmed_at__isnull=False)
        pending = Delivery.objects.filter(campaign__in=due, status=status.PENDING)
        for delivery in pending.select_related("campaign").order_by(
            "campaign__scheduled_at", "pk"
        )[:batch_size]:
            with transaction.atomic():
                config = Configuration.objects.select_for_update().filter(
                    pk=1, enabled=True, sender__gt=""
                ).first()
                now = timezone.now()
                if not config or not has_capacity(config, now):
                    break
                delivery_rows = Delivery.objects.filter(pk=delivery.pk, status=status.PENDING)
                if not still_eligible(delivery.email, delivery.campaign.audience):
                    delivery_rows.update(status=status.EXCLUDED, error="Contact devenu inéligible.")
                    continue
                if not delivery_rows.update(status=status.SENDING, attempted_at=now):
                    continue
            row = Delivery.objects.filter(pk=delivery.pk)
            try:
                count = build_message(delivery.campaign, delivery.email, config, smtp, delivery).send()
            except SMTPResponseException as exc:
                row.update(status=status.FAILED, error=f"Réponse SMTP {exc.smtp_code}.")
            except Exception as exc:
                row.update(status=status.UNCERTAIN, error=f"Résultat incertain ({type(exc).__name__}).")
            else:
                if count == 1:
                    row.update(status=status.SENT, sent_at=timezone.now())
                else:
                    row.update(status=status.FAILED, error="Aucun message accepté par le SMTP.")
        due.filter(~Exists(Delivery.objects.filter(
            campaign_id=OuterRef("pk"), status__in=[status.PENDING, status.SENDING]
        ))).update(status=Campaign.Status.FINISHED)
