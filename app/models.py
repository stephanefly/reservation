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


class EventTemplate(models.Model):
    url_modele = models.TextField(null=True)
    text_template = models.TextField(null=True)
    statut = models.BooleanField(default=False)


class EventProduct(models.Model):
    photobooth = models.BooleanField(default=False)
    miroirbooth = models.BooleanField(default=False)
    videobooth = models.BooleanField(default=False)
    voguebooth = models.BooleanField(default=False)
    ipadbooth = models.BooleanField(default=False)
    airbooth = models.BooleanField(default=False)

    def get_selected_booths(self):
        selected_booths = []
        if self.photobooth:
            selected_booths.append("photobooth")
        if self.miroirbooth:
            selected_booths.append("miroirbooth")
        if self.videobooth:
            selected_booths.append("videobooth")
        if self.voguebooth:
            selected_booths.append("voguebooth")
        if self.ipadbooth:
            selected_booths.append("ipadbooth")
        if self.airbooth:
            selected_booths.append("airbooth")
        return ', '.join(selected_booths[:-1]) + ' et ' + selected_booths[-1]

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

    PhotographeVoguebooth = models.BooleanField(default=False)
    PhotographeVoguebooth_reduc_prix = models.IntegerField(null=True, default=False)
    def prix_base_PhotographeVoguebooth(self):
        return 100

    ImpressionVoguebooth = models.BooleanField(default=False)
    ImpressionVoguebooth_reduc_prix = models.IntegerField(null=True, default=False)
    def prix_base_ImpressionVoguebooth(self):
        return 50

    DecorVoguebooth = models.BooleanField(default=False)
    DecorVoguebooth_reduc_prix = models.IntegerField(null=True, default=False)
    def prix_base_DecorVoguebooth(self):
        return 50

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

class EventPostPrestation(models.Model):
    paid = models.BooleanField(default=False)
    feedback = models.BooleanField(default=False)
    feedback_posted = models.BooleanField(default=False)
    membre_paid = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)

class EventAcompte(models.Model):
    montant_acompte = models.IntegerField(null=True, blank=True)
    MOYEN_PAIEMENT = [
        ('', ''),
        ('PayPal', 'PayPal'),
        ('Virement SG', 'Virement SG'),
        ('Virement LCL', 'Virement LCL'),
        ('Espece', 'Espece'),
        ('Lydia', 'Lydia'),
        ('Revolut', 'Revolut'),
        ('Boursorama', 'Boursorama'),
    ]
    mode_payement = models.CharField(max_length=255, default='PayPal', choices=MOYEN_PAIEMENT, null=True, blank=True)
    date_payement = models.DateField(null=True, blank=True)
    montant_restant = models.IntegerField(null=True, blank=True)


class Event(models.Model):
    id_card = models.CharField(max_length=100, null=True)
    num_devis = models.CharField(max_length=100, null=True)

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    event_details = models.ForeignKey(EventDetails, on_delete=models.CASCADE)
    event_product = models.ForeignKey(EventProduct, on_delete=models.CASCADE, null=True)
    event_option = models.ForeignKey(EventOption, on_delete=models.CASCADE, null=True)
    event_acompte = models.ForeignKey(EventAcompte, on_delete=models.CASCADE, null=True)
    event_template = models.ForeignKey(EventTemplate, on_delete=models.CASCADE, null=True)
    post_presta = models.ForeignKey(EventPostPrestation, on_delete=models.CASCADE, null=True)

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
        ('Post Presta', 'Post Presta'),
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
        ('Delegation', 'Delegation'),
    ]
    type_cost = models.CharField(max_length=255, default='Charge', choices=TYPE, null=True)
    price_cost = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

