# Journal SMTP et rapports de livraison

**Analyses → Livraison des mails** (`/backend/graph/email-delivery/`) affiche les
nouveaux envois clients réalisés via `send_mail_event` : préparation, acceptation
par IONOS, refus SMTP, erreur, résultat incertain et rapports techniques reçus.
L'ouverture, lorsqu'elle est suivie, reste un indicateur séparé.

## Déploiement PythonAnywhere

Cette modification ajoute deux modèles : `EmailDelivery` et `EmailMailboxCheck`.
L'historique privé des migrations PythonAnywhere n'est pas suivi dans GitHub :
ne pas remplacer ses fichiers ni créer une migration initiale arbitraire.
Depuis le dépôt et l'environnement virtuel habituels :

```bash
git pull
python manage.py showmigrations app
python manage.py makemigrations app --name email_delivery_tracking --dry-run --verbosity 3
```

Vérifier que le plan ajoute seulement les deux modèles ci-dessus, sans suppression
ni recréation des tables existantes, puis :

```bash
python manage.py makemigrations app --name email_delivery_tracking
python manage.py migrate app --plan
python manage.py migrate app
python manage.py sync_email_bounces
```

Recharger ensuite l'application web (Reload). Une sauvegarde de la base et les
fichiers de migration existants doivent être conservés avant application.
Si Django propose une migration initiale pour les modèles existants ou d'autres
opérations inattendues, arrêter et réconcilier l'historique serveur ; ne pas
supprimer de migration ni utiliser `--fake` par défaut.

La tâche existante `myselfiebooth/sheduled_tasks/hourly.py` appelle désormais
`sync_email_bounces` avant ses autres opérations. Si ce script n'est pas déjà
planifié, ajouter une tâche PythonAnywhere exécutant `python manage.py sync_email_bounces`
depuis le dépôt avec le Python de l'environnement virtuel. GitHub ne configure pas
les tâches PythonAnywhere. Une erreur IMAP ne bloque pas le traitement des médias.

## Configuration et lecture IMAP

Utilise uniquement `MAIL_MYSELFIEBOOTH` et `MP` depuis la configuration serveur,
avec TLS vérifié : SMTP `smtp.ionos.fr:465`, IMAP `imap.ionos.fr:993`.
Référence : https://www.ionos.fr/assistance/email/sujets-generaux/messagerie-ionos-donnees-de-serveur-pour-imap-pop3-et-smtp/
Aucun nouveau secret n'est stocké dans le journal, GitHub ou le navigateur.

La commande sélectionne **INBOX en lecture seule**, cherche les messages
`multipart/report` des 14 derniers jours et lit avec `BODY.PEEK[]` (aucun marquage lu,
déplacement ou suppression). Limites : 500 candidats et 1 Mio par message.
Une exécution élargie est possible :

```bash
python manage.py sync_email_bounces --days 30 --limit 2000
```

Les rapports classés dans Spam ou un autre dossier ne sont pas parcourus.
Les retours en texte libre, anciens ou sans identifiant ne sont pas devinés.
Le tableau indique le dernier contrôle, son succès et les messages ignorés ou
non rattachés. Les scans répétés sont idempotents.

## Interprétation et sécurité des envois

Chaque tentative reçoit un `Message-ID` unique. Une acceptation de la copie BCC
ne masque jamais le refus du client. Une copie refusée est signalée séparément.
Les destinataires Cc prévus sont désormais inclus dans l'enveloppe SMTP.
Les retours sont rapprochés par `Message-ID` **et** adresse client, uniquement
pour un rapport structuré `message/delivery-status` avec Action/Status cohérents.
Les corps de messages reçus et leurs pièces jointes ne sont pas conservés.

Les rapports de livraison sont demandés lorsque le serveur annonce l'extension
DSN ; le fonctionnement reste compatible avec un serveur sans cette extension.
Un rapport de livraison réussi n'indique pas boîte principale ou spam.
L'absence de retour d'erreur ne prouve pas la réception. Les anciens mails
n'ont pas de résultat SMTP historique : aucune confirmation n'est inventée.

Une panne de connexion après le début de soumission produit l'état `unknown`.
Les nouvelles tentatives du même type vers ce client et ce dossier sont bloquées
tant que cet état n'est pas résolu. Vérifier les journaux IONOS, puis utiliser :

```bash
python manage.py resolve_email_delivery 123 --result accepted --confirm
```

Remplacer `123` par l'identifiant du journal et choisir `refused` uniquement si
la non-acceptation a été vérifiée. Cette commande n'envoie aucun message.
L'état de préparation des médias et le compteur de demande d'avis ne sont mis
à jour qu'après acceptation SMTP. Les exceptions restent propagées pour que les
appelants n'avancent pas leurs statuts après un refus d'envoi.

## Vérifications effectuées et restantes

`python -m tests_api.run` couvre 30 cas avec base temporaire, SMTP capturé et IMAP
simulé. Cela inclut le constructeur réel des messages et le lien avec le pixel,
une pièce jointe PDF simulée, les refus partiels, les erreurs réseau/authentification,
la fermeture SMTP, les rapports différés/échoués/réussis, le rapprochement strict,
l'absence de modification IMAP, les droits et le rendu HTML du journal.
Le parcours navigateur/PDF réel demeure couvert par le workflow existant.

Non vérifiés en production depuis cet environnement : migration serveur, connexion
à la boîte IONOS, tâche horaire effective, rendu navigateur et classement réel
sur Gmail/Outlook. Aucun mail réel n'a été envoyé. SPF/DKIM/DMARC ne sont pas modifiés
par ce code ; leur contrôle et un test de placement nécessitent une vérification
séparée des DNS et des en-têtes reçus.
