# Newsletter MySelfieBooth sur PythonAnywhere

Le CRM utilise les contacts existants. La case facultative de la page de confirmation du devis enregistre l’adresse et la date du consentement. La valeur historique `autorisation_mail` et une demande de devis seule ne valent pas consentement Newsletter. La population initiale est donc vide. Un contact doit avoir consenti pour son adresse actuelle, être autorisé dans le CRM et ne pas être désabonné de la Newsletter. Les doublons sont regroupés par adresse normalisée. Si le CRM contient plusieurs fiches consentantes pour la même adresse, la fiche consentante valide la plus récente détermine son segment.

## Migration et configuration

1. Déployer le code dans le checkout PythonAnywhere selon la procédure du dépôt. Le workflow existant recharge le code sans migrer. Avec `NEWSLETTER_AVAILABLE` absent, le menu et les routes de suivi restent inactifs.
2. Sauvegarder MySQL. Dans le checkout et le virtualenv du CRM, vérifier puis appliquer la migration additive.

   ```bash
   python manage.py migrate newsletter --plan
   python manage.py migrate newsletter
   ```

3. Renseigner les variables suivantes dans l’environnement du processus web WSGI et dans celui de la tâche. Utiliser un fichier d’environnement privé hors dépôt si les deux processus doivent charger les mêmes valeurs. Donner à ce fichier des permissions `0600`.

   | Variable | Valeur |
   | --- | --- |
   | `NEWSLETTER_AVAILABLE` | `1` après la migration |
   | `NEWSLETTER_HOST` | Nom DNS du relais SMTP marketing |
   | `NEWSLETTER_PORT` | `587` par défaut, avec STARTTLS. `465` utilise TLS implicite. |
   | `NEWSLETTER_USER` | Identifiant SMTP dédié |
   | `NEWSLETTER_PASSWORD` | Mot de passe SMTP dédié |
   | `NEWSLETTER_PUBLIC_URL` | `https://reservation.myselfiebooth-paris.fr` |

   Le relais doit être joignable depuis le compte PythonAnywhere. Autoriser l’adresse d’expédition sur le relais et configurer SPF, DKIM et DMARC côté domaine. Les en-têtes de désabonnement en un clic doivent être couverts par la signature DKIM du relais pour les clients mail qui l’exigent.

4. Recharger l’application web. Dans **Newsletter → Paramètres**, saisir l’adresse d’expédition et la limite horaire. L’envoi est désactivé à l’installation. Le commutateur suspend la file et les emails de test. Il laisse les pages publiques de suivi et de désabonnement accessibles. Laisser `NEWSLETTER_AVAILABLE=1` pour préserver les liens d’emails déjà expédiés.

## Tâche d’envoi

Créer un script Bash privé sur PythonAnywhere et adapter les chemins du virtualenv et du fichier d’environnement.

```bash
#!/usr/bin/env bash
set -euo pipefail
set -a
source /home/stephanefly/.newsletter.env
set +a
cd /home/stephanefly/reservation
exec /home/stephanefly/.virtualenvs/CRM/bin/python manage.py send_newsletters \
  --lock-file /home/stephanefly/.newsletter-send.lock --batch-size 50
```

Dans **Tasks**, appeler ce script avec `bash /home/stephanefly/send-newsletter.sh`. Une tâche horaire donne une précision d’environ une heure. Pour une cadence à la minute, si le compte le permet, utiliser une tâche **Always-on** qui appelle la même commande, journalise les échecs puis attend 60 secondes avant le prochain passage. Faire exécuter la file sur un seul hôte et conserver le même fichier de verrou pour chaque invocation. Avec un lot de 50 et une fréquence horaire, le débit plafonne à 50 tentatives par passage, même si la limite CRM est supérieure.

L’envoi immédiat rejoint la file dès sa confirmation et part au prochain passage. Une programmation est saisie en heure de Paris. La tâche revalide l’éligibilité avant chaque envoi et applique une fenêtre glissante de 60 minutes pour les tentatives de campagne et de test. Un email de test adressé manuellement à une seule adresse est envoyé depuis la page de campagne et exclu des statistiques de campagne. Pendant les vérifications, employer des réglages fictifs et le SMTP simulé des tests. Aucune campagne réelle n’est nécessaire.

L’historique affiche les adresses exclues, les refus SMTP et les résultats incertains. Une interruption après la prise en charge d’un destinataire reste incertaine et ne déclenche pas de renvoi automatique. Vérifier les journaux du relais SMTP pour établir si le message a été accepté. Les autres destinataires restent traitables.

## Vérifier le SMTP depuis le CRM

Dans **Newsletter → Test**, envoyer le message de vérification SMTP ou sélectionner une campagne déjà renseignée. Le destinataire est fixé à l’adresse de Stéphane côté serveur. Ce test utilise le même compte SMTP et le même quota horaire que les campagnes. Il ne crée aucun envoi dans leur file.

## Mesure des résultats

Les taux distinguent chaque destinataire une seule fois et prennent pour dénominateur les messages acceptés par le SMTP. Les bloqueurs d’images, proxys et robots de messagerie peuvent affecter les chiffres. Pour l’attribution, insérer un lien HTTPS absolu vers le CRM dans le HTML. Le dernier clic vers le CRM peut être attribué à une demande confirmée depuis le même navigateur avec la même adresse dans les 30 jours. Le tableau distingue les demandes et les devis chiffrés. Le chiffre d’affaires est la somme des montants validés des dossiers signés.

## Vérification locale

```bash
python -m tests_e2e.run_newsletter
python -m tests_e2e.run_quote_capture
```
