"""Read structured delivery reports; never infer a bounce from subject text."""
import email
from email import policy
from email.parser import Parser
from email.utils import parseaddr

from django.utils import timezone

from app.models import EmailTracking


def reports(raw):
    message = email.message_from_bytes(raw, policy=policy.default)
    if message.get_content_type() != "multipart/report" or message.get_param("report-type") != "delivery-status":
        return []
    original_ids = set()
    recipients = []
    for part in message.walk():
        if part.get_content_type() == "message/rfc822":
            for original in part.get_payload() if isinstance(part.get_payload(), list) else []:
                if original.get("Message-ID"):
                    original_ids.add(str(original["Message-ID"]).strip())
        elif part.get_content_type() == "text/rfc822-headers":
            payload = part.get_payload(decode=True) or b""
            original = Parser(policy=policy.default).parsestr(payload.decode("utf-8", errors="replace"))
            if original.get("Message-ID"):
                original_ids.add(str(original["Message-ID"]).strip())
        elif part.get_content_type() == "message/delivery-status":
            for block in part.get_payload() if isinstance(part.get_payload(), list) else []:
                if block.get("Original-Message-ID"):
                    original_ids.add(str(block["Original-Message-ID"]).strip())
                action = str(block.get("Action", "")).lower().strip()
                code = str(block.get("Status", "")).strip()
                address = str(block.get("Original-Recipient") or block.get("Final-Recipient") or "")
                address = parseaddr(address.partition(";")[2].strip())[1]
                if action in ("failed", "delayed", "delivered") and address:
                    if code.startswith({"failed": "5.", "delayed": "4.", "delivered": "2."}[action]):
                        recipients.append((address, action, code))
    # Never guess between different original messages in one malformed report.
    if len(original_ids) != 1:
        return []
    message_id = original_ids.pop()
    return [(message_id, address, action, code) for address, action, code in recipients]


def apply_report(raw):
    matched = 0
    unmatched = 0
    for message_id, recipient, action, code in reports(raw):
        delivery = EmailTracking.objects.filter(message_id=message_id, recipient__iexact=recipient).first()
        if delivery is None:
            unmatched += 1
            continue
        matched += 1
        status = {"failed": "bounced", "delayed": "delayed", "delivered": "delivered"}[action]
        # Conditional updates keep repeated scans and concurrent reports safe.
        eligible = ["accepted", "unknown", "delayed"]
        if status == "bounced":
            eligible += ["delivered"]
        EmailTracking.objects.filter(pk=delivery.pk, delivery_status__in=eligible).update(
            delivery_status=status, feedback_at=timezone.now(),
            diagnostic=f"Rapport technique reçu : {action}, code {code[:30]}.",
        )
    return matched, unmatched
