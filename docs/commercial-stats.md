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

## Validation

`python -m tests_api.run` vérifie l'API, les ouvertures et ces statistiques sur une
base temporaire : cohortes, bornes de dates, segments, signatures, montants nuls
ou à zéro, doublons de tracking, délais incohérents, accès et rendu HTML.
Les calculs commerciaux utilisent deux requêtes SQL, sans requête par dossier.

Après publication : `git pull`, puis Reload sur PythonAnywhere. Pas de migration.
