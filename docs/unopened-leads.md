# Onglet À relancer

Accès administrateur depuis la navigation principale : **À relancer**,
`/backend/leads/`. Aucun envoi de mail ni appel n'est déclenché automatiquement.

## Sélection des prospects

- Une ligne par dossier, sans signature enregistrée, avec un statut commercial actif.
- Date de prestation aujourd'hui ou à venir et contact autorisé.
- Au moins un devis ou une relance enregistré dans EmailTracking.
- Les statuts de confirmation, de refus et de prestation terminée sont exclus,
  même si leur date de signature manque.
- Les seuls envois en préparation ne sont pas présentés comme envoyés.

Les types de devis et relance sont sélectionnés explicitement. Les anciens
trackings sans `mail_type` sont reconnus lorsqu'ils disposent d'un suivi d'ouverture.
Un mail ouvert de confirmation, d'avis ou de médias ne compte pas comme devis ouvert.

**Sans ouverture détectée** : aucune ouverture sur les devis/relances du dossier,
et dernier suivi en état historique inconnu, accepté par IONOS ou livraison confirmée.
L'absence d'ouverture n'est pas une preuve de non-lecture ni de non-livraison.

**Problèmes de livraison** : dernier devis ou relance refusé, en erreur, incertain,
différé ou revenu en échec. Ce groupe peut inclure un dossier dont un ancien devis
a été ouvert : le problème concerne alors le dernier envoi.

## Actions et filtres

Coordonnées actuelles, prestation, ville, produits/options, prix proposé, date
et état du dernier envoi, ancien compte rendu et liens vers la fiche et le journal.
Une adresse d'envoi différente de l'adresse actuelle est signalée.
« Appeler » ouvre le téléphone ; « Écrire un mail » ouvre le logiciel de messagerie.
L'utilisateur choisit et effectue lui-même le contact.

Filtres : recherche nom/mail/téléphone/ville, particuliers/entreprises, délai depuis
le dernier devis/relance (sans minimum, 24 h, 48 h, 3 ou 7 jours), suivi à faire,
déjà contacté ou tous. Par défaut : **à contacter**, dernier envoi d'au moins **24 h**.
Tri : derniers envois les plus anciens en premier, puis date d'événement.
Pagination de 25 dossiers. Les compteurs de chaque groupe respectent les filtres.

## Historique manuel

Le formulaire ajoute un **EventRelance** existant, sans nouveau modèle : canal,
compte rendu obligatoire de 1 à 2000 caractères et qualification de 0 à 5.
Le membre et la date du contact sont fixés côté serveur depuis l'utilisateur connecté.
La fiche est revérifiée au POST pour ne pas enregistrer un contact sur un lead
désormais signé, refusé, expiré ou désabonné.
Les formulaires utilisent la protection CSRF existante et une redirection après POST.
Cette action ne change pas le statut commercial, le nombre de mails envoyés,
l'ouverture ou l'autorisation de contact.

Un dossier est « déjà contacté » si sa dernière entrée EventRelance passée est
postérieure ou égale au dernier devis/relance. Il revient à contacter si un nouvel
envoi intervient après ce contact. Une entrée future n'est pas traitée comme un
contact déjà effectué. L'historique existant équipe et API retrouve ces mêmes notes.

## Validation et activation

`python -m tests_api.run` vérifie la sélection, les doublons, les ouvertures
antérieures, les erreurs de livraison, les coordonnées, les filtres, la sauvegarde,
les droits administrateur et les dossiers signés entre affichage et sauvegarde.

`git pull` puis Reload PythonAnywhere. **Aucune migration supplémentaire pour
cet onglet**, mais il requiert les champs du modèle EmailTracking unifié, décrits
dans `docs/email-delivery.md`. Le rendu navigateur en production reste à vérifier.
