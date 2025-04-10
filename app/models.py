import uuid
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from datetime import datetime


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
    nb_relance_devis = models.IntegerField(default=0, null=True)
    nb_relance_avis = models.IntegerField(default=0, null=True)
    autorisation_mail = models.BooleanField(default=True)
    code_espace_client = models.CharField(max_length=6, unique=True, null=True, blank=True)
    mail_sondage = models.BooleanField(default=False)


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
    directory_name = models.CharField(max_length=100, null=True)
    image_name = models.CharField(max_length=100, null=True)
    num_template = models.IntegerField(default=1)
    link_media_shared = models.URLField(null=True, blank=True)


class EventProduct(models.Model):
    photobooth = models.BooleanField(default=False)
    miroirbooth = models.BooleanField(default=False)
    videobooth = models.BooleanField(default=False)
    voguebooth = models.BooleanField(default=False)
    ipadbooth = models.BooleanField(default=False)
    airbooth = models.BooleanField(default=False)

    def get_selected_booths(self):
        booths = {
            "photobooth": self.photobooth,
            "miroirbooth": self.miroirbooth,
            "videobooth": self.videobooth,
            "voguebooth": self.voguebooth,
            "ipadbooth": self.ipadbooth,
            "airbooth": self.airbooth
        }

        # Filtrer les booths sélectionnés
        selected_booths = [name for name, selected in booths.items() if selected]
        # Gérer le formatage pour une liste de plus de 1 élément
        if len(selected_booths) > 1:
            return ', '.join(selected_booths[:-1]) + ' et ' + selected_booths[-1]
        elif selected_booths:
            return selected_booths[0]


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
        return magnets * 2

    def total_reduction(self):
        reduction_fields = [
            self.MurFloral_reduc_prix or 0,
            self.Phonebooth_reduc_prix or 0,
            self.LivreOr_reduc_prix or 0,
            self.Fond360_reduc_prix or 0,
            self.PanneauBienvenue_reduc_prix or 0,
            self.PhotographeVoguebooth_reduc_prix or 0,
            self.ImpressionVoguebooth_reduc_prix or 0,
            self.DecorVoguebooth_reduc_prix or 0,
            self.Holo3D_reduc_prix or 0,
            self.magnets_reduc_prix or 0
        ]
        return sum(reduction_fields)

    livraison = models.BooleanField(default=False)
    duree = models.IntegerField(null=True, blank=True)


class EventPostPrestation(models.Model):
    paid = models.BooleanField(default=False)
    feedback_message = models.BooleanField(default=False)
    feedback_google = models.BooleanField(default=False)
    feedback_posted = models.BooleanField(default=False)
    membre_paid = models.BooleanField(default=False)
    collected = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
    date_media_sent = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.sent and self.date_media_sent is None:
            self.date_media_sent = datetime.now()
        super().save(*args, **kwargs)


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
        ('N26', 'N26'),
        ('Sumup', 'Sumup'),
    ]
    mode_payement = models.CharField(max_length=255, default='PayPal', choices=MOYEN_PAIEMENT, null=True, blank=True)
    date_payement = models.DateField(null=True, blank=True)
    montant_restant = models.IntegerField(null=True, blank=True)


class Event(models.Model):
    id_card = models.CharField(max_length=100, null=True)
    num_devis = models.IntegerField(null=True)
    event_token = models.CharField(max_length=100, null=True)

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    event_details = models.ForeignKey(EventDetails, on_delete=models.CASCADE)
    event_product = models.ForeignKey(EventProduct, on_delete=models.CASCADE, null=True)
    event_option = models.ForeignKey(EventOption, on_delete=models.CASCADE, null=True)
    event_acompte = models.ForeignKey(EventAcompte, on_delete=models.CASCADE, null=True)
    event_template = models.ForeignKey(EventTemplate, on_delete=models.CASCADE, null=True)
    event_post_presta = models.ForeignKey(EventPostPrestation, on_delete=models.CASCADE, null=True)

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
        ('Sent Media', 'Sent Media'),
        ('Resended', 'Resended'),
        ('Last Chance', 'Last Chance'),
        ('First Rappel', 'First Rappel'),
        ('Last Rappel', 'Last Rappel'),
        ('Prolongation', 'Prolongation'),
        ('Temoignage', 'Temoignage'),
        ('Phonebooth Offert', 'Phonebooth Offert'),
    ]
    status = models.CharField(max_length=255, default='Initied', choices=STATUS, null=True)
    history_status = models.TextField(default="", blank=True)  # Stocke l'historique des statuts
    def save(self, *args, **kwargs):
        if self.pk:
            previous_event = Event.objects.get(pk=self.pk)
            if previous_event.status != self.status:
                self.history_status = f"{self.history_status}, {self.status}".strip(", ") if self.history_status else self.status

        super().save(*args, **kwargs)


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
        ('Marketing', 'Marketing'),
        ('Delegation', 'Delegation'),
    ]
    type_cost = models.CharField(max_length=255, default='Charge', choices=TYPE, null=True)
    price_cost = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    FREQUENCY = [
        ('Ponctuel', 'Ponctuel'),
        ('Mensuel', 'Mensuel'),
        ('Annuel', 'Annuel'),
    ]
    frecency = models.CharField(max_length=50, choices=FREQUENCY, default='Ponctuel', null=True)


class EmailTracking(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    event_traced = models.IntegerField(null=True, blank=True)
    status_devis = models.CharField(max_length=100, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)


class EventRelance(models.Model):
    event = models.ForeignKey("Event", on_delete=models.CASCADE, related_name="relances")
    membre = models.CharField(max_length=100, null=True)
    date_relance = models.DateTimeField(null=True, blank=True)
    commentaire = models.TextField(blank=True, null=True)
    qualification = models.PositiveSmallIntegerField(default=0)  # Valeur entre 0 et 5