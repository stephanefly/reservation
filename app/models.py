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
    def __init__(self, *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)
        self.prix_brut_calculs()

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
        ('Send', 'Send'),
        ('OK', 'OK'),
        ('Prio', 'Prio'),
        ('Refused', 'Refused'),
    ]
    status = models.CharField(max_length=255, default='Initied', choices=STATUS, null=True)

    def prix_brut_calculs(self):
        # Définition des prix de base pour chaque produit pour 5 heures
        prix_photobooth_5h = 450  # Prix hypothétique du photobooth pour 5h
        prix_miroirbooth_5h = 600  # Prix hypothétique du miroirbooth pour 5h
        prix_videobooth_5h = 500  # Prix hypothétique du videobooth pour 5h

        # Prix spécial pour le combo Miroirbooth + Videobooth
        prix_combo_miroir_videobooth = 1100  # Prix combiné pour Miroirbooth et Videobooth avant réduction
        reduction_combo = 200  # Réduction appliquée au prix du combo

        # Réduction supplémentaire pour les durées de 5 heures
        reduction_5h = 50  # Réduction de 50 euros pour les événements de 5 heures

        # Définition des prix de base pour chaque produit pour 3 heures
        prix_photobooth_3h = 350  # Prix hypothétique du photobooth pour 3h
        prix_miroirbooth_3h = 450  # Prix hypothétique du miroirbooth pour 3h
        prix_videobooth_3h = 400  # Prix hypothétique du videobooth pour 3h

        # Vérifier la durée de l'événement dans les options de l'événement
        duree_evenement = self.event_option.duree if self.event_option.duree else 5  # Utilise 5h par défaut si non spécifié

        # Sélectionner les prix en fonction de la durée
        if duree_evenement == 3:
            prix_photobooth = prix_photobooth_3h
            prix_miroirbooth = prix_miroirbooth_3h
            prix_videobooth = prix_videobooth_3h
        else:  # Utiliser les prix pour 5 heures par défaut si la durée est différente de 3 heures
            prix_photobooth = prix_photobooth_5h
            prix_miroirbooth = prix_miroirbooth_5h
            prix_videobooth = prix_videobooth_5h

        # Initialisation du prix brut
        prix_brut = 0

        # Vérification de la sélection de Miroirbooth et Videobooth pour appliquer le prix spécial du combo
        if self.event_product.miroirbooth and self.event_product.videobooth:
            prix_brut += prix_combo_miroir_videobooth - reduction_combo
            # Si Photobooth est également sélectionné, ajouter son prix
            if self.event_product.photobooth:
                prix_brut += prix_photobooth
        else:
            # Calcul du prix brut en fonction des produits sélectionnés sans le combo spécial
            if self.event_product.photobooth:
                prix_brut += prix_photobooth
            if self.event_product.miroirbooth:
                prix_brut += prix_miroirbooth
            if self.event_product.videobooth:
                prix_brut += prix_videobooth

        # Appliquer la réduction supplémentaire pour les événements de 5 heures
        if duree_evenement == 5:
            prix_brut -= reduction_5h

        # Mise à jour du champ reduc de l'objet Event avec le montant total de la réduction
        self.reduc_product = reduction_combo + reduction_5h

        # Mise à jour du prix brut de l'événement
        self.prix_brut = prix_brut
        self.save()  # Enregistrement des modifications dans la base de données

        # Retourne le prix brut pour une utilisation ultérieure si nécessaire
        return prix_brut
