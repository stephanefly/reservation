from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Event(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    mail = models.CharField(max_length=100)
    date_evenement = models.DateField() #Supérieur au jour d'aujourd'hui
    adresse_evenement = models.CharField(max_length=100) #une adresse exact
    ville_evenement = models.CharField(max_length=100) #une ville en france
    code_postal_evenement = models.IntegerField() #Supérieur à 9999 et Inférieur à 99999
    numero_telephone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.prenom} {self.nom}"