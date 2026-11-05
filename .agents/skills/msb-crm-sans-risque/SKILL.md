---
name: msb-crm-sans-risque
description: Développer et relire le CRM Django MySelfieBooth sans toucher aux données de production ni déclencher involontairement des e-mails ou paiements.
---

# Modification du CRM
1. Inspecter les fichiers et tests réels sur la branche actuelle ; lire `docs/ux-guidelines-crm.md`, `docs/catalogue-commercial.md`, `docs/admin-devis-auto.md`.
2. Reformuler la règle métier, distinguer le backend, le catalogue commercial, le PDF historique, le frontend et les données existantes.
3. Changer le moins de fichiers possible dans une branche de travail. Éviter toute écriture ou mail de production.
4. Garder la logique : entreprise et recommandation -> devis manuel, minimum 350 €, source/durée/pack éligibles, activation explicite des devis automatiques.
5. Une simulation montre le scénario (machine, options, prix calculé et statut) sans envoyer de mail ni modifier le dossier.
6. Exécuter les tests pertinents en base de test isolée et signaler ceux qui ne peuvent être exécutés. Si migration : documenter sauvegarde, restauration en base distincte, activation et retour arrière avant tout déploiement.
7. Livrer fichiers modifiés, tests, risques, état réel (PR créée ≠ fusion ≠ déploiement).

Référence : https://app.notion.com/p/40f481b9179581bd9ac4f353c311eaf9
