# API privée CRM — lecture complète

Base : `/api/private/`. Authentification : header `X-Private-Api-Token`.
Toutes les routes sont en GET uniquement. Conserver le token hors des URL et des journaux.
Les anciennes routes et leurs champs sont conservés.
Aucune migration ni nouvelle dépendance n'est nécessaire.

## Routes

Le CRM propose aussi la page **Analyses → Ouverture des mails**
(`/backend/graph/emails/`) : anneau du taux global, compteurs, barres par statut
lors de l'envoi et évolution mensuelle, avec filtre de dates inclusives.
Cette page utilise la session administrateur, sans transmettre de token API au navigateur.
L'API et la page partagent les mêmes calculs. Le rendu HTML fonctionne sans JavaScript.

| Route | Résultat |
| --- | --- |
| `schema/` | Ressources et liste explicite des champs disponibles |
| `resources/<resource>/` | Liste paginée, y compris les données historiques |
| `resources/<resource>/<id>/` | Détail d'un objet |
| `event/<id>/` | Ancien format + `event.details_complets` avec objets liés, équipe et statistiques mail |
| `email-stats/` | Taux d'ouverture global, par statut lors de l'envoi et par mois |

Ressources : `clients`, `events`, `event-details`, `products`, `options`,
`payments`, `templates`, `post-prestation`, `team`, `cost-names`, `costs`,
`email-tracking`, `follow-ups`.

Chaque liste accepte `page` (défaut 1) et `page_size` (défaut 50, maximum 100).
Réponse : `items`, `total`, `page`, `page_size`, `has_next`.
L'ordre est celui des identifiants croissants. Continuer jusqu'à `has_next=false`.
Les objets événements exposent les identifiants des objets liés et `team_ids`.
Les codes d'espace client, tokens d'événement, UUID de tracking et secrets de configuration sont exclus.
Les informations métier (coordonnées, commentaires et liens médias) sont privées.

## Filtres

| Ressource | Paramètres |
| --- | --- |
| `events` | `q` (nom, mail, ville), `status`, `client_id`, `start_date`, `end_date` |
| `clients` | `q` (nom, mail, téléphone) |
| `email-tracking` | `event_id`, `status`, `opened=true/false`, `start_date`, `end_date` |
| `follow-ups` | `event_id`, `start_date`, `end_date` |
| `costs` | `start_date`, `end_date` |
| `email-stats/` | `event_id`, `status`, `start_date`, `end_date` |

Dates inclusives au format `AAAA-MM-JJ`, en Europe/Paris. Elles portent sur
la date de prestation pour les événements, d'envoi pour le tracking, de relance
pour les relances et de création pour les dépenses. Sans dates : tout l'historique.
Les statistiques n'acceptent pas `opened`, afin de garder les non ouverts au dénominateur.
Exemple : `email-stats/?start_date=2026-11-01&end_date=2026-11-30`.
Erreurs : 400 pour les valeurs invalides, 403 pour le token absent/invalide,
404 pour un objet/une ressource absent, 405 pour une méthode d'écriture.

## Interprétation du taux

`totals.opening_rate_percent = 100 × opened / tracked`, arrondi à deux décimales.
Le résultat est `null` lorsqu'il n'y a aucun enregistrement, et non 0 %.
`by_status` et `by_month` reprennent les mêmes compteurs (`tracked`, `opened`,
`not_opened`) et le même calcul. Les mois sont ceux de la date d'envoi.

Le tracking actuel porte sur les devis et leurs relances. Une ligne est créée
avant l'envoi SMTP : ce total ne prouve ni l'envoi réussi ni la livraison.
Une ouverture correspond au chargement de l'image ; les protections de messagerie
peuvent charger automatiquement ou bloquer cette image. `opened_at` contient
le dernier chargement enregistré, pas forcément la première ouverture.
Le taux ne mesure pas les réponses des clients. Les comptes rendus manuels sont
disponibles dans `follow-ups` ; aucun corps de mail reçu n'est stocké dans ces modèles.

## Validation et déploiement

Tests isolés, base SQLite temporaire, modèles et vues réels, aucun service externe :
`python -m tests_api.run` (Django 4.2).
Le lanceur évite uniquement les initialisations globales de vues/URL qui chargent
les intégrations externes sans rapport avec l'API.

Sur PythonAnywhere : récupérer `main` avec `git pull`, puis Reload de l'application web.
Pas de `makemigrations` ni de `migrate` pour cette modification.
Vérifier ensuite `schema/` et `email-stats/` avec le header privé.
