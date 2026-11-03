import imaplib
import re
import ssl
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from app.models import EmailMailboxCheck
from app.module.mail.bounces import apply_report


class Command(BaseCommand):
    help = "Lire les rapports de livraison IONOS sans modifier la boîte de réception."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14)
        parser.add_argument("--limit", type=int, default=500)

    def handle(self, *args, **options):
        if not 1 <= options["days"] <= 90 or not 1 <= options["limit"] <= 2000:
            raise CommandError("days doit être entre 1 et 90 ; limit entre 1 et 2000.")
        account = getattr(settings, "MAIL_MYSELFIEBOOTH", "")
        password = getattr(settings, "MP", "")
        if not account or not password:
            raise CommandError("Identifiants de messagerie absents de la configuration serveur.")
        check, _ = EmailMailboxCheck.objects.get_or_create(key="ionos")
        client = None
        totals = {"scanned": 0, "matched": 0, "unmatched": 0, "skipped": 0}
        incomplete = False
        try:
            client = imaplib.IMAP4_SSL("imap.ionos.fr", 993, ssl_context=ssl.create_default_context(), timeout=30)
            client.login(account, password)
            status, _ = client.select("INBOX", readonly=True)
            if status != "OK":
                raise ValueError("Cannot select inbox")
            since = timezone.now().date() - timedelta(days=options["days"])
            month = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[since.month - 1]
            status, data = client.uid("search", None, "SINCE", f"{since.day:02d}-{month}-{since.year}", "HEADER", "Content-Type", '"multipart/report"')
            if status != "OK":
                raise ValueError("Cannot search inbox")
            identifiers = (data[0] or b"").split()
            incomplete = len(identifiers) > options["limit"]
            totals["skipped"] += max(0, len(identifiers) - options["limit"])
            for identifier in identifiers[-options["limit"]:]:
                status, meta = client.uid("fetch", identifier, "(RFC822.SIZE)")
                sizes = re.findall(rb"RFC822.SIZE\s+(\d+)", b" ".join(value for value in meta if isinstance(value, bytes)))
                if status != "OK" or not sizes or int(sizes[0]) > 1024 * 1024:
                    totals["skipped"] += 1
                    continue
                status, parts = client.uid("fetch", identifier, "(BODY.PEEK[])")
                if status != "OK":
                    totals["skipped"] += 1
                    continue
                raw = next((part[1] for part in parts if isinstance(part, tuple) and isinstance(part[1], bytes)), None)
                if raw is None or len(raw) > 1024 * 1024:
                    totals["skipped"] += 1
                    continue
                matched, unmatched = apply_report(raw)
                totals["scanned"] += 1
                totals["matched"] += matched
                totals["unmatched"] += unmatched
            check.success = True
            check.diagnostic = "Contrôle partiel : augmenter --limit ou réduire la période." if incomplete else "Contrôle des rapports structurés dans INBOX terminé."
        except Exception:
            check.success = False
            check.diagnostic = "Échec de lecture IMAP. Vérifier les identifiants et l'accès réseau sur le serveur."
            raise CommandError(check.diagnostic) from None
        finally:
            check.checked_at = timezone.now()
            for key, value in totals.items():
                setattr(check, key, value)
            check.save()
            if client is not None:
                try:
                    client.logout()
                except (OSError, imaplib.IMAP4.error):
                    pass
        self.stdout.write(f"Rapports lus : {totals['scanned']} ; correspondances : {totals['matched']} ; non rattachés : {totals['unmatched']} ; ignorés : {totals['skipped']}.")
