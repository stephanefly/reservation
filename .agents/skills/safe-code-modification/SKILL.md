---
name: safe-code-modification
description: "Utiliser pour modifier ou corriger du code Django CRM MySelfieBooth sans casser réservations, tarification, emails, statuts ou données."
---

# Changement ciblé et sûr — CRM

1. Localiser la fonctionnalité et suivre le flux complet: routes, vues, modèles, utilitaires, templates, JS et tests. Lire les fichiers avant de les changer.
2. Identifier les invariants métier touchés: événement, date, produit, durée, prix, acompte, statuts, remises, devis, relances, accès équipe/client. Vérifier les effets de bord, en particulier les emails et SMS.
3. Corriger la cause plutôt que masquer le symptôme. Modifier le moins de fichiers possible; préserver les interfaces, routes et données existantes.
4. Pour les statistiques/graphiques, comparer les résultats aux données source et tester les cas vides, années absentes et changements de millésime. Ne pas afficher un graphe vide en prétendant qu'il fonctionne.
5. Ajouter ou adapter des tests ciblés dans app/tests si le comportement change. Tester valeurs normales, limites et régressions pertinentes.
6. Si le schéma ou les données changent, proposer une migration Django explicite et un plan de sauvegarde/retour arrière. Ne jamais lancer migration ou écriture sur la base de production de manière implicite.
7. Ne pas déclencher de vrais envois d'emails/SMS, de paiements ou d'appels externes en test; utiliser simulations/isolations.
8. Vérifier avec le skill test-and-deploy. Donner le diff fonctionnel, les commandes réellement exécutées et les limitations.

Ne pas utiliser ce skill pour une simple demande d'explication sans modification de code.
