from django.db import models
from django.utils import timezone


QUOTE_EMAIL_TEXT = "J'accepte de recevoir mon devis et les e-mails de suivi de ma demande."
NEWSLETTER_TEXT = "J'accepte de recevoir les nouveautés et offres exclusives de MySelfieBooth."


class QuoteEmailConsent(models.Model):
    # Pas de dépendance aux migrations privées historiques de l'application CRM.
    event_id = models.PositiveBigIntegerField(unique=True)
    email = models.EmailField()
    accepted_at = models.DateTimeField(default=timezone.now)
    consent_text = models.CharField(max_length=255)


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    accepted_at = models.DateTimeField(default=timezone.now)
    consent_text = models.CharField(max_length=255)
    source = models.CharField(max_length=50)
    event_id = models.PositiveBigIntegerField()
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def subscribed(cls):
        return cls.objects.filter(unsubscribed_at__isnull=True)


def record_quote_consent(event):
    QuoteEmailConsent.objects.update_or_create(
        event_id=event.pk,
        defaults={"email": event.client.mail.strip().lower(),
                  "accepted_at": timezone.now(), "consent_text": QUOTE_EMAIL_TEXT},
    )


def subscribe_from_quote(event):
    NewsletterSubscriber.objects.update_or_create(
        email=event.client.mail.strip().lower(),
        defaults={"accepted_at": timezone.now(), "consent_text": NEWSLETTER_TEXT,
                  "source": "formulaire_devis", "event_id": event.pk,
                  "unsubscribed_at": None},
    )


def unsubscribe_email(email):
    NewsletterSubscriber.subscribed().filter(email=email.strip().lower()).update(
        unsubscribed_at=timezone.now()
    )
