import logging
import os
from datetime import timedelta
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit

from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.core.validators import validate_email
from django.db.models.functions import Lower, Trim
from django.urls import reverse
from django.utils import timezone

from app.models import Client

from .models import Attribution, Campaign, Consent, Delivery, TestAttempt, Unsubscribe

logger = logging.getLogger(__name__)
CLICK_SALT = "newsletter.click"


def normalize(email):
    return email.strip().lower()


def authorized_individuals():
    return Client.objects.filter(autorisation_mail=True, raison_sociale=False).annotate(
        normalized_mail=Lower(Trim("mail"))
    )


def valid_address(email):
    try:
        validate_email(email)
    except ValidationError:
        return False
    return True


def eligible(audience=Campaign.Audience.ALL):
    blocked = set(Unsubscribe.objects.values_list("email", flat=True))
    if audience == Campaign.Audience.CRM_ALLOWED:
        addresses = authorized_individuals().values_list("normalized_mail", flat=True).iterator()
        return {email for email in addresses if email not in blocked and valid_address(email)}

    clients = Consent.objects.select_related("client").order_by("-granted_at", "-pk")
    result = {}
    for consent in clients.iterator():
        client = consent.client
        email = normalize(client.mail)
        if email != consent.email or email in blocked or not client.autorisation_mail:
            continue
        if valid_address(email):
            result.setdefault(email, client.raison_sociale)
    if audience == Campaign.Audience.ALL:
        return set(result)
    return {email for email, business in result.items()
            if business == (audience == Campaign.Audience.BUSINESS)}


def still_eligible(email, audience):
    if Unsubscribe.objects.filter(email=email).exists():
        return False
    if audience == Campaign.Audience.CRM_ALLOWED:
        return valid_address(email) and authorized_individuals().filter(normalized_mail=email).exists()
    for consent in Consent.objects.filter(email=email, client__autorisation_mail=True
                                         ).select_related("client").order_by("-granted_at", "-pk"):
        if normalize(consent.client.mail) == email:
            return (audience == Campaign.Audience.ALL or
                    consent.client.raison_sociale == (audience == Campaign.Audience.BUSINESS))
    return False


def has_capacity(config, now):
    since = now - timedelta(hours=1)
    campaigns = Delivery.objects.filter(attempted_at__gt=since).count()
    tests = TestAttempt.objects.filter(attempted_at__gt=since).count()
    return campaigns + tests < config.hourly_limit


def record_quote(event, opted_in, click):
    email = normalize(event.client.mail)
    if opted_in:
        try:
            Consent.objects.get_or_create(client=event.client, defaults={"email": email})
        except Exception:
            logger.exception("Consentement newsletter non enregistré pour dossier %s", event.pk)
    if click:
        try:
            if click["at"] < (timezone.now() - timedelta(days=30)).timestamp():
                return
            clicked = Delivery.objects.filter(
                token=click["token"], email=email, sent_at__isnull=False, clicked_at__isnull=False,
            ).first()
            if clicked:
                Attribution.objects.get_or_create(event=event, defaults={"delivery": clicked})
        except Exception:
            logger.exception("Attribution newsletter non enregistrée pour dossier %s", event.pk)


def http_url(value):
    try:
        parsed = urlsplit(value)
        if (parsed.scheme in ("http", "https") and parsed.hostname and
                not parsed.username and not parsed.password and
                not any(ord(char) < 33 or char == "\\" for char in value)):
            return parsed
    except ValueError:
        pass
    return None


def smtp_settings():
    required = ("HOST", "USER", "PASSWORD", "PUBLIC_URL")
    values = {key: os.environ.get("NEWSLETTER_" + key, "") for key in required}
    if not all(values.values()):
        raise ValueError("Configuration SMTP Newsletter incomplète.")
    origin = http_url(values["PUBLIC_URL"])
    if not origin or origin.scheme != "https" or origin.path not in ("", "/") or origin.query or origin.fragment:
        raise ValueError("NEWSLETTER_PUBLIC_URL doit être une origine HTTPS.")
    values["PUBLIC_URL"] = values["PUBLIC_URL"].rstrip("/")
    values["PORT"] = int(os.environ.get("NEWSLETTER_PORT", "587"))
    if not 1 <= values["PORT"] <= 65535:
        raise ValueError("Port SMTP invalide.")
    values["SSL"] = values["PORT"] == 465
    return values


class TrackedHTML(HTMLParser):
    def __init__(self, origin, token):
        super().__init__(convert_charrefs=False)
        self.origin = origin
        self.token = token
        self.parts = []

    def handle_starttag(self, tag, attrs):
        self.start(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self.start(tag, attrs, " /")

    def start(self, tag, attrs, suffix=""):
        target = dict(attrs).get("href") if tag == "a" else None
        if not target or not http_url(target) or len(target) > 2000:
            self.parts.append(self.get_starttag_text())
            return
        signed = signing.dumps(target, salt=f"{CLICK_SALT}.{self.token}")
        link = self.origin + reverse("newsletter_public:click", args=[self.token, signed])
        attributes = "".join(
            f' {key}="{escape(link if key == "href" else value, quote=True)}"'
            if value is not None else f" {key}"
            for key, value in attrs
        )
        self.parts.append(f"<{tag}{attributes}{suffix}>")

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.parts.append(f"<!{decl}>")


def build_message(campaign, email, config, smtp, delivery=None):
    origin = smtp["PUBLIC_URL"]
    html = campaign.html
    headers = {}
    if delivery is not None:
        token = delivery.token
        unsubscribe = origin + reverse("newsletter_public:unsubscribe", args=[token])
        pixel = origin + reverse("newsletter_public:open", args=[token])
        parser = TrackedHTML(origin, token)
        parser.feed(html)
        parser.close()
        html = "".join(parser.parts)
        footer = (f'<p><a href="{escape(unsubscribe)}">Se désabonner de la Newsletter</a></p>'
                  f'<img src="{escape(pixel)}" width="1" height="1" alt="">')
        index = html.lower().rfind("</body>")
        html = html + footer if index == -1 else html[:index] + footer + html[index:]
        headers = {"List-Unsubscribe": f"<{unsubscribe}>",
                   "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}
        body = f"{campaign.subject}\n\nSe désabonner : {unsubscribe}"
        subject = campaign.subject
    else:
        body = "Message de prévisualisation."
        subject = "[TEST] " + campaign.subject
    connection = EmailBackend(
        host=smtp["HOST"], port=smtp["PORT"], username=smtp["USER"],
        password=smtp["PASSWORD"], use_tls=not smtp["SSL"], use_ssl=smtp["SSL"],
        timeout=20, fail_silently=False,
    )
    message = EmailMultiAlternatives(subject, body, config.sender, [email],
                                     connection=connection, headers=headers)
    message.attach_alternative(html, "text/html")
    return message
