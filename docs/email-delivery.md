# Suivi unifié des mails

## Modèles

Un mail correspond désormais à une ligne **EmailTracking** :

| Champs | Fonction |
| --- | --- |
| `uuid`, `event_traced`, `status_devis`, `sent_at` | Identité, dossier, statut du devis et date initiale |
| `opened`, `opened_at`, `opening_tracked` | Ouverture et activation effective du pixel |
| `message_id`, `recipient`, `mail_type` | Identité SMTP, destinataire et type de mail |
| `delivery_status`, `accepted_at` | Résultat de la soumission ou du rapport technique |
| `smtp_code`, `diagnostic`, `copy_refused`, `feedback_at` | Erreurs, copies et retours reçus |

Les anciens champs et UUID sont conservés. Les anciens suivis gardent une
livraison `legacy` (inconnue), sans inventer une acceptation historique.
`message_id` est nullable et unique : plusieurs anciens mails peuvent ne pas en avoir.
Le constructeur réutilise cette ligne pour le pixel ; il ne crée pas une seconde ligne.
Les mails sans pixel sont suivis pour la livraison et exclus du taux d'ouverture.
Les tentatives en préparation, refusées ou en erreur sont exclues de ce taux.

**EmailDelivery n'est plus un modèle actif.** EmailMailboxCheck reste séparé,
car il décrit le dernier contrôle global de la boîte, indépendamment d'un mail.

## Activation PythonAnywhere — conserver l'historique et les données

Ne pas utiliser un `makemigrations` ordinaire pour cette fusion si une table
EmailDelivery a déjà été créée : Django pourrait proposer de la supprimer.
Une commande prépare la migration depuis les fichiers de migration privés du
serveur, valide qu'elle ne contient que les changements attendus, et conserve
physiquement l'ancienne table. Elle n'applique aucun changement à la base.

Depuis le dépôt et l'environnement virtuel habituels, après sauvegarde de la base :

```bash
git pull
python manage.py prepare_email_tracking_migration --dry-run
python manage.py prepare_email_tracking_migration
python manage.py migrate app --plan
python manage.py migrate app
python manage.py sync_email_bounces
```

Puis **Reload** de l'application web.

La commande traite les deux cas : l'ancien EmailDelivery déjà migré, ou seulement
l'ancien EmailTracking. Elle ajoute les champs à EmailTracking et crée
EmailMailboxCheck si nécessaire. Si EmailDelivery existe dans l'historique, son
retrait se fait uniquement dans l'état Django, avec `SeparateDatabaseAndState` :
sa table n'est pas supprimée. Les données y sont copiées vers EmailTracking :
la ligne liée est enrichie en gardant son UUID, ses ouvertures et sa date ; un
mail sans ancien pixel obtient une nouvelle ligne avec `opening_tracked=False`.
Un identifiant SMTP déjà fusionné est ignoré pour préserver les retours plus récents.
Un conflit d'association interrompt le transfert au lieu d'écraser des données.
La table ancienne reste une archive de sécurité, sans être lue par les pages du CRM.

La préparation refuse un historique absent, des branches de migrations en conflit
ou des changements métier sans rapport. Elle n'écrit aucune migration initiale
arbitraire et ne remplace pas de fichier existant. Dans ce cas, réconcilier
l'historique serveur ; ne pas supprimer de migration ni utiliser `--fake` par défaut.
Garder le module `app.module.mail.tracking_upgrade` importable : les migrations
privées générées y font référence. Le transfert n'a pas de rétrotransfert automatique.

## Pages et API

**Analyses → Livraison des mails** : `/backend/graph/email-delivery/`.
La page affiche les anciens suivis et les nouveaux mails, leurs résultats SMTP,
rapports techniques et ouvertures, avec filtres et pagination.
Les routes API `resources/email-tracking/` et `resources/email-deliveries/`
exposent le même modèle unifié (identifiants EmailTracking). La seconde reste
une entrée de consultation par `delivery_status` via le paramètre `status`.
La première conserve `status` comme filtre de `status_devis`.

## Copie visible (Cc) des e-mails de MySelfieBooth

La copie automatique est désactivée à la demande du propriétaire.
`MAIL_ADMIN_CC` est fixé à une chaîne vide dans `settings.py`, même si une
ancienne valeur existe dans `settings.yaml`. Recharger le site PythonAnywhere
après la mise à jour. Les éventuelles copies BCC existantes restent inchangées.

Les alertes internes restent adressées à `CRM_ALERT_EMAIL`, avec
`contact@myselfiebooth-paris.fr` comme valeur par défaut indépendante des copies.

## Lecture des retours IONOS

Configuration serveur uniquement : `MAIL_MYSELFIEBOOTH` et `MP`.
SMTP TLS vérifié : `smtp.ionos.fr:465` ; IMAP : `imap.ionos.fr:993`.
Référence : https://www.ionos.fr/assistance/email/sujets-generaux/messagerie-ionos-donnees-de-serveur-pour-imap-pop3-et-smtp/
La commande sélectionne INBOX en lecture seule et lit avec `BODY.PEEK[]` :
aucune suppression, déplacement ou marque de lecture.
Elle parcourt les rapports structurés des 14 derniers jours, au plus 500 candidats,
limités à 1 Mio. Les dossiers Spam et les erreurs en texte libre ne sont pas analysés.
Les rapports sont rapprochés par Message-ID exact et adresse client, jamais par
le seul sujet. Les corps de mails reçus ne sont pas conservés.

```bash
python manage.py sync_email_bounces --days 30 --limit 2000
```

Le script existant `myselfiebooth/sheduled_tasks/hourly.py` appelle cette commande.
Si ce script n'est pas déjà planifié sur PythonAnywhere, planifier la commande
avec le Python de l'environnement virtuel ; GitHub ne crée pas cette tâche.
Le dernier contrôle et ses erreurs sont visibles dans le CRM.

## Résultats et limites

Une acceptation de la copie BCC ne masque pas un refus du client. Une copie
refusée est signalée séparément. Les rapports DSN sont demandés si le serveur
annonce cette capacité. L'absence de retour ne prouve pas la réception ; une
confirmation technique ne distingue pas boîte principale et spam.
Un résultat incertain bloque un nouvel envoi du même type au même dossier et
à la même adresse. Après vérification des journaux IONOS :

```bash
python manage.py resolve_email_delivery 123 --result accepted --confirm
```

L'identifiant est maintenant celui d'EmailTracking. Choisir `refused` seulement
si la non-acceptation a été vérifiée. La commande n'envoie aucun mail.

## Validation

`python -m tests_api.run` : tests sur base temporaire, SMTP capturé et IMAP simulé,
constructeur réel des mails, pixel unique, pièce jointe PDF simulée, erreurs SMTP,
rapports DSN, droits, statistiques et rendu HTML.
La fusion teste la conservation des UUID, ouvertures et dates, les mails sans
pixel, l'idempotence, la préservation de la table archive et la génération de
migration depuis les deux historiques possibles.
Aucun mail réel n'est envoyé. Migration, connexion IMAP, tâche horaire et rendu
navigateur en production restent à vérifier après activation. SPF/DKIM/DMARC et
le classement réel Gmail/Outlook nécessitent une vérification séparée.

## Alertes et conservation des prospects (correctif novembre 2026)

- Dès le premier clic sur « Vérifier ma demande de devis », la demande est
  enregistrée dans le CRM avec la mention
  `Formulaire : confirmation non terminée`. La page finale de confirmation
  réutilise ce dossier, même après correction du formulaire. Un double clic
  final ne doit plus créer de second événement.
- La liste des devis affiche le nombre de pré-demandes à confirmer et le nombre
  d'erreurs de livraison enregistrées sur les 30 derniers jours. Elle prévient
  si la dernière vérification IONOS est absente, a échoué ou date de plus de 3 h.
- `python manage.py notify_pending_quotes` signale en un e-mail interne les
  pré-demandes non confirmées depuis plus d'une heure et marque les dossiers
  signalés afin de ne pas répéter la notification. Une panne d'alerte laisse les
  dossiers non marqués pour le prochain passage.
- Lors d'un premier refus SMTP (immédiat), ou lors d'un rapport IONOS structuré
  de non-livraison / retard, un e-mail interne résume le dossier et le
  destinataire. Aucune relance client n'est envoyée automatiquement.
- `CRM_ALERT_EMAIL` est facultatif dans `settings.yaml`. Si absent, les
  notifications vont à `contact@myselfiebooth-paris.fr` par défaut,
  indépendamment de la désactivation des copies automatiques. L'envoi d'alerte utilise SMTP IONOS,
  sans le suivi client et sans copie visible au prospect. Une panne SMTP peut
  aussi empêcher l'alerte e-mail : les incidents restent alors visibles
  dans l'interface d'administration.

### Activation sur PythonAnywhere

Aucune migration de schéma supplémentaire n'est nécessaire pour ce correctif.
Après sauvegarde et vérification de la version déployée :

```bash
python manage.py sync_email_bounces --days 14
python manage.py notify_pending_quotes
```

Le script existant `myselfiebooth/sheduled_tasks/hourly.py` appelle les deux
commandes, **uniquement s'il est réellement planifié sur PythonAnywhere**.
Vérifier la tâche dans le panneau Tasks et la réception de l'adresse d'alerte.
La synchronisation IMAP en lecture seule ne traite que les rapports
`multipart/report` avec adresse et Message-ID exacts. Une capture d'écran ou
un texte de rejet transféré par un client ne suffit pas à changer un statut.
Un code 554 ne permet pas à lui seul d'identifier la cause d'un rejet iCloud :
contrôler aussi SPF, DKIM, DMARC et les journaux IONOS.

Le présent changement protège les demandes faites sur le formulaire **devis**
du CRM. Le formulaire **Contact** du site vitrine utilise toujours Web3Forms :
l'intégrer séparément au CRM avant de garantir une couverture de 100 %.
