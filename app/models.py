from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Client(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    mail = models.CharField(max_length=100)
    numero_telephone = models.CharField(max_length=15)

    HOW_FIND = [
        ('INSTAGRAM', 'INSTAGRAM'),
        ('SITE INTERNET', 'SITE INTERNET'),
        ('LEBONCOIN', 'LEBONCOIN'),
        ('RECOMMENDATION', 'RECOMMENDATION'),
    ]
    how_find = models.CharField(max_length=255, default='', choices=HOW_FIND, null=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

class EventDetails(models.Model):
    date_evenement = models.DateField()
    adresse_evenement = models.CharField(max_length=100)
    ville_evenement = models.CharField(max_length=100)
    code_postal_evenement = models.IntegerField()

class ServiceDetails(models.Model):
    PRODUIT = [
        ('Photobooth', 'Photobooth'),
        ('Miroirbooth', 'Miroirbooth'),
        ('360Booth', '360Booth'),
    ]
    produit = models.CharField(max_length=255, default='', choices=PRODUIT, null=True)
    livraison = models.BooleanField(default=False)
    mur_floral = models.BooleanField(default=False)

class Event(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    event_details = models.ForeignKey(EventDetails, on_delete=models.CASCADE)
    service_details = models.ForeignKey(ServiceDetails, on_delete=models.CASCADE)
    prix_brut = models.IntegerField()
    prix_proposed = models.IntegerField(null=True, blank=True)
    prix_valided = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    signer_at = models.DateTimeField(null=True, blank=True)

    STATUS = [
        ('Initied', 'Initied'),
        ('Send', 'Send'),
        ('OK', 'OK'),
        ('Prio', 'Prio'),
        ('Refused', 'Refused'),
    ]
    status = models.CharField(max_length=255, default='', choices=STATUS, null=True)