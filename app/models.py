from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Event(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_evenement = models.DateField()
    adresse_evenement = models.CharField(max_length=100)
    ville_evenement = models.CharField(max_length=100, null=True)
    code_postal_evenement = models.IntegerField(default=75000,
        validators=[
            MaxValueValidator(99999),  # Limite maximale à 999999
            MinValueValidator(9999),       # Limite minimale à 0 (si nécessaire)
        ])
    numero_telephone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.prenom} {self.nom}"