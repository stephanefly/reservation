import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Configuration(models.Model):
    enabled = models.BooleanField(default=False)
    sender = models.EmailField(blank=True)
    hourly_limit = models.PositiveIntegerField(
        default=100, validators=[MinValueValidator(1), MaxValueValidator(10000)]
    )


class Consent(models.Model):
    client = models.OneToOneField("app.Client", on_delete=models.CASCADE)
    email = models.EmailField(db_index=True)
    granted_at = models.DateTimeField(auto_now_add=True)


class Unsubscribe(models.Model):
    email = models.EmailField(unique=True)
    delivery = models.ForeignKey("Delivery", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class Template(models.Model):
    name = models.CharField(max_length=150)
    html = models.TextField()

    def __str__(self):
        return self.name


class Campaign(models.Model):
    class Audience(models.TextChoices):
        ALL = "all", "Tous les contacts éligibles"
        BUSINESS = "business", "Professionnels"
        INDIVIDUAL = "individual", "Particuliers"

    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        QUEUED = "queued", "En file"
        FINISHED = "finished", "Terminée"

    audience = models.CharField(max_length=12, choices=Audience.choices)
    name = models.CharField(max_length=150, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    html = models.TextField(blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    step = models.PositiveSmallIntegerField(default=1)
    confirmed_at = models.DateTimeField(null=True, blank=True)


class Delivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        SENDING = "sending", "Envoi en cours"
        SENT = "sent", "Accepté par le SMTP"
        FAILED = "failed", "Erreur"
        UNCERTAIN = "uncertain", "Résultat SMTP incertain"
        EXCLUDED = "excluded", "Exclu"

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="deliveries")
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    attempted_at = models.DateTimeField(null=True, db_index=True)
    sent_at = models.DateTimeField(null=True)
    opened_at = models.DateTimeField(null=True)
    clicked_at = models.DateTimeField(null=True)
    error = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["campaign", "email"], name="newsletter_unique_email")
        ]


class Attribution(models.Model):
    event = models.OneToOneField("app.Event", on_delete=models.CASCADE)
    delivery = models.ForeignKey(Delivery, on_delete=models.PROTECT)


class TestAttempt(models.Model):
    attempted_at = models.DateTimeField(db_index=True)
