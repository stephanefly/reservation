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
    comment = models.TextField(null=True)
    comment_client = models.TextField(null=True)
    horaire = models.CharField(max_length=100, null=True)
    url_modele = models.TextField(null=True)


class EventProduct(models.Model):
    photobooth = models.BooleanField(default=False)
    miroirbooth = models.BooleanField(default=False)
    videobooth = models.BooleanField(default=False)


class EventOption(models.Model):

    MurFloral = models.BooleanField(default=False)
    MurFloral_reduc_prix = models.IntegerField(null=True, default=False)
    def prix_base_MurFloral(self):
        return 50

    Phonebooth = models.BooleanField(default=False)
    Phonebooth_reduc_prix = models.IntegerField(null=True, default=False)
    def prix_base_Phonebooth(self):
        return 50

    LivreOr = models.BooleanField(default=False)
    LivreOr_reduc_prix = models.IntegerField(null=True, default=False)
    def prix_base_LivreOr(self):
        return 70

    Fond360 = models.BooleanField(default=False)
    Fond360_reduc_prix = models.IntegerField(null=True, default=False)
    def prix_base_Fond360(self):
        return 100

    PanneauBienvenue = models.BooleanField(default=False)
    PanneauBienvenue_reduc_prix = models.IntegerField(null=True, default=False)
    def prix_base_PanneauBienvenue(self):
        return 70

    Holo3D = models.BooleanField(default=False)
    Holo3D_reduc_prix = models.IntegerField(null=True, default=False)
    def prix_base_Holo3D(self):
        return 50

    magnets = models.IntegerField(null=True, blank=True)
    magnets_reduc_prix = models.IntegerField(null=True, default=False)

    def prix_base_magnets(self, magnets):
        return (magnets // 50) * 25

    livraison = models.BooleanField(default=False)
    duree = models.IntegerField(null=True, blank=True)


class Event(models.Model):
    id_card = models.CharField(max_length=100, null=True)
    num_devis = models.CharField(max_length=100, null=True)

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
        ('Acompte OK', 'Acompte OK'),
        ('Refused', 'Refused'),
        ('Presta FINI', 'Presta FINI'),
    ]
    status = models.CharField(max_length=255, default='Initied', choices=STATUS, null=True)


class NameCost(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name


class Cost(models.Model):
    name_cost = models.ForeignKey(NameCost, on_delete=models.CASCADE)
    TYPE = [
        ('Membre', 'Membre'),
        ('Invest', 'Invest'),
        ('Charge', 'Charge'),
    ]
    type_cost = models.CharField(max_length=255, default='Charge', choices=TYPE, null=True)
    price_cost = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)



