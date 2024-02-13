from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Client(models.Model):
    nom = models.CharField(max_length=100)
    mail = models.CharField(max_length=100)
    numero_telephone = models.CharField(max_length=15)

    HOW_FIND = [
        ('INSTAGRAM', 'INSTAGRAM'),
        ('SITE INTERNET', 'SITE INTERNET'),
        ('LEBONCOIN', 'LEBONCOIN'),
        ('RECOMMENDATION', 'RECOMMENDATION'),
    ]
    how_find = models.CharField(max_length=255, default='', choices=HOW_FIND, null=True)
    raison_sociale = models.BooleanField(default=False)


class EventDetails(models.Model):
    date_evenement = models.DateField()
    adresse_evenement = models.CharField(max_length=100)
    ville_evenement = models.CharField(max_length=100)
    code_postal_evenement = models.IntegerField()


class EventProduct(models.Model):
    photobooth = models.BooleanField(default=False)
    miroirbooth = models.BooleanField(default=False)
    videobooth = models.BooleanField(default=False)


class EventOption(models.Model):
    mur_floral = models.BooleanField(default=False)
    mur_floral_reduc_prix = models.IntegerField(null=True, default=False)

    def prix_base_mur_floral(self):
        return 50

    phonebooth = models.BooleanField(default=False)
    phonebooth_reduc_prix = models.IntegerField(null=True, default=False)

    def prix_base_phonebooth(self):
        return 50

    magnets = models.IntegerField(null=True, blank=True)
    magnets_reduc_prix = models.IntegerField(null=True, default=False)

    def prix_base_magnets(self, magnets):
        return (magnets / 50)*20

    livraison = models.BooleanField(default=False)
    duree = models.IntegerField(null=True, blank=True)


class Event(models.Model):

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    event_details = models.ForeignKey(EventDetails, on_delete=models.CASCADE)
    event_product = models.ForeignKey(EventProduct, on_delete=models.CASCADE, null=True)
    event_option = models.ForeignKey(EventOption, on_delete=models.CASCADE, null=True)

    prix_brut = models.IntegerField()
    reduc_product = models.IntegerField(null=True, blank=True)
    reduc_all = models.IntegerField(null=True, blank=True)

    prix_proposed = models.IntegerField(null=True, blank=True)
    prix_valided = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    signer_at = models.DateTimeField(null=True, blank=True)

    STATUS = [
        ('Initied', 'Initied'),
        ('Calculed', 'Calculed'),
        ('Sended', 'Sended'),
        ('OK', 'OK'),
        ('Refused', 'Refused'),
    ]
    status = models.CharField(max_length=255, default='Initied', choices=STATUS, null=True)

