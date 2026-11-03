# Performance commerciale

Page CRM : **Analyses → Performance commerciale**, `/backend/graph/commercial/`.
Accès administrateur par session, lecture seule, réponses sans cache.
Aucune migration ni dépendance supplémentaire.

## Périmètre et calculs

Les filtres `start_date` et `end_date` portent sur `Event.created_at`, bornes
inclusives en Europe/Paris. Sans dates : tout l'historique. `segment` accepte
`all`, `individual` et `business` selon `client.raison_sociale`.
Les résultats décrivent la situation actuelle de cette cohorte de demandes.

| Indicateur | Règle |
| --- | --- |
| Demandes reçues | Tous les événements de la sélection |
| Devis traités | Signature, ligne de tracking ou statut d'envoi/relance/refus/confirmation dans le statut courant ou l'historique |
| Signés | Date `signer_at` renseignée |
| Taux de signature | Signés / devis traités, incluant les dossiers encore en attente |
| Taux sur décisions connues | Signés / (signés + refusés non signés) |
| Montant signé | Somme `prix_valided`, sinon `prix_proposed` |
| Panier moyen | Montant signé / nombre de signés |
| Devis sans signature | Traités, sans `signer_at`, statut courant différent de `Refused` |
| Montant refusé | Somme des prix proposés des refusés non signés |
| Délai avant signature | Moyenne de `signer_at - created_at` en jours, dates négatives exclues |
| Soldes à récupérer | Restants positifs des statuts `Presta FINI`, `Post Presta`, `Sent Media`, `Media KO` |

Les valeurs nulles de montant comptent pour zéro et sont signalées. Un prix
réellement égal à zéro est conservé. Sans dénominateur, un taux est absent (tiret).
Le montant signé n'est pas un montant encaissé et le prix brut ne remplace pas
automatiquement un prix proposé manquant. Les dossiers confirmés/terminés sans
date de signature sont signalés : aucun statut ne crée artificiellement une signature.

## Relances et statut

La répartition par statut courant affiche dossiers, part des demandes et montant.
Le montant est celui signé pour un dossier signé, sinon le prix proposé.

Le tableau des relances repère les statuts exacts dans l'historique (séparateur
virgule), le statut courant et les lignes `EmailTracking`. Un événement compte
une fois par type de relance, même après plusieurs mails identiques.
Les groupes peuvent se recouper. La part signée n'est pas une attribution
causale ni un taux d'efficacité incrémentale : l'historique ne date pas chaque
transition et le tracking est créé avant l'envoi SMTP.

La liste des soldes contient les 30 premiers dossiers, triés par date de prestation,
avec lien vers la fiche. Les compteurs incluent tous les dossiers de la sélection.
L'existence d'un solde ne signifie pas nécessairement un retard contractuel.

## Modules de pilotage commercial

Les données de la page commerciale sont enrichies avec quatre modules, sans écriture
dans les dossiers clients :

- **Tunnel de conversion** : demandes, devis traités, devis soumis au SMTP avec
  suivi, ouvertures détectées et signatures. Chaque étape représente un nombre
  de dossiers uniques et un pourcentage des demandes. Les ouvertures sont
  indépendantes de la signature ; la présence d'un pixel ne prouve pas une
  lecture. Les e-mails sans type historique sont pris en compte uniquement si
  le statut du suivi correspond à un devis / une relance. Les messages
  transactionnels non liés au devis sont exclus du tunnel.
- **Performance par produit** : les six équipements de `EventProduct`, avec
  demandes, devis traités, signatures, attentes, refus, taux et montants.
  Un devis combinant plusieurs équipements apparaît sur chaque ligne :
  les sommes par produit ne sont pas additionnables et ne correspondent
  pas à du revenu réellement attribué à une machine.
- **Devis refusés** : statut actuel `Refused` sans date de signature.
  Nombre, montant, taux sur les devis traités, ventilation par type de
  client et tranche de prix, accès aux dix plus gros refus.
  Les motifs de refus ne sont pas enregistrés de façon structurée :
  aucune cause n'est devinée. Les dossiers toujours en attente sont exclus.
- **Prospects prioritaires** : maximum vingt devis traités en attente,
  événements non passés, `autorisation_mail=True`. Le tri repose sur
  un score explicable de 0 à 100 : valeur du devis (0–25), proximité
  de l'événement (0–25), ancienneté (0–10), pixel d'ouverture (0–10),
  dernière qualification manuelle (0–20), pénalité en cas de contact
  très récent (-15). Ce score n'est pas une probabilité de signature.
  Les incidents de livraison e-mail historiques sont signalés, mais
  aucun envoi ni relance automatique n'est déclenché.

Les suivis d'e-mails et la dernière relance sont chargés en deux requêtes
supplémentaires sans accès SQL par dossier. Le rapport repose désormais
sur **trois requêtes SQL** : dossiers, suivi e-mail, relances.

## Alertes commerciales (lecture seule)

Les alertes sont visibles en haut de **Analyses → Performance commerciale**,
avec un accès direct par le menu Analyses, les compteurs par catégorie et un
lien vers chaque fiche. Les filtres de cohorte (`start_date`, `end_date`) et
de clientèle (`segment`) continuent de s'appliquer. Le paramètre facultatif
`alert` accepte `all`, `delivery`, `upcoming`, `followup`, `high_value`.
Une autre valeur est refusée avec HTTP 400.

Seuls les dossiers avec devis **traité**, **non signé**, **non refusé**, dont
l'événement n'est pas passé sont évalués. Un dossier répondant à plusieurs
critères est affiché une seule fois dans la liste, même s'il est comptabilisé
dans plusieurs catégories. La liste est triée par urgence puis date
d'événement et montant, avec un maximum de 30 lignes par filtre.

| Catégorie | Règle par défaut |
| --- | --- |
| Devis importants | Prix proposé ≥ 900 € |
| Événement proche | Date de prestation dans 14 jours maximum |
| Relance à vérifier | Aucun contact enregistré récent depuis au moins 3 jours |
| Incident d'envoi | Dernier e-mail **de devis** non préparatoire en état `error`, `refused`, `bounced`, `unknown` ou `delayed` |

La date du dernier contact est le maximum entre la dernière relance manuelle
déjà effectuée et le dernier envoi de devis enregistré comme `accepted`,
`delivered` ou `legacy` (statut historique incertain). Un envoi échoué
ne remet pas à zéro le délai de relance. Une nouvelle tentative de devis
acceptée ou livrée remplace un ancien échec pour l'alerte d'envoi.
Une demande sans historique de contact commence à être signalée après
3 jours à compter de sa création ; l'interface parle alors de **contact
non confirmé**, pas d'absence de contact certaine.

Priorités : *Urgente* si incident d'envoi ou événement dans les 7 jours ;
*À traiter* si événement dans les 14 jours ou devis important associé
à un contact à vérifier ; sinon *À surveiller*. Il ne s'agit ni d'une
probabilité de signature ni d'un motif de contacter automatiquement.

Les dossiers avec `autorisation_mail=False` peuvent apparaître pour
examen manuel, mais sont signalés **« Ne pas envoyer d'e-mail »**. Aucune
opération d'écriture, aucune relance SMTP, aucun cron et aucune modification
de la base de données ne sont introduits. La page reste protégée par
l'authentification staff, le GET uniquement et `Cache-Control: no-store`.

Les seuils sont modifiables dans
`app/module/lib_graph/commercial_alerts.py` ;
la page réutilise les trois requêtes d'analyse déjà existantes
(dossiers, suivis de mails, dernières relances), sans requête par dossier.

## Validation

`python -m tests_api.run` vérifie l'API, les ouvertures et ces statistiques sur une
base temporaire : cohortes, bornes de dates, segments, signatures, montants nuls
ou à zéro, doublons de tracking, délais incohérents, accès et rendu HTML.
Les calculs commerciaux utilisent trois requêtes SQL, sans requête par dossier.

Après publication : `git pull`, puis Reload sur PythonAnywhere. Pas de migration.
