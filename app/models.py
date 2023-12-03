from django.db import models

class Devis(models.Model):
    date = models.DateField()
    adresse = models.CharField(max_length=255)
    code_postal = models.CharField(max_length=10)
    ville = models.CharField(max_length=100)

class Client(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)