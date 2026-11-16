---
name: myselfiebooth-design
description: "Utiliser pour créer ou améliorer des interfaces Django du CRM, de l'espace client et de l'espace équipe MySelfieBooth."
---

# UI/UX du CRM

1. Inspecter les templates et styles existants avant de dessiner une nouvelle interface. Respecter les identités déjà en place: backend dans app/static/css/backend.css (primaire #5b34d6), espace équipe dans app/static/css/team.css (primaire #1565d8), et styles propres à l'espace client.
2. Favoriser une interface professionnelle, compacte et lisible; ne pas importer aveuglément la charte noir/or du site vitrine dans les écrans de gestion.
3. Placer les informations prioritaires avant les détails. Pour une carte événement, rendre le nom, le produit et le prix lisibles; regrouper la durée près du produit; éviter les dates répétées et les horaires superflus sauf demande explicite.
4. Sur mobile, privilégier la lecture ligne par ligne, sans défilement horizontal inutile. Garder contrastes, focus clavier, libellés et zones tactiles utilisables.
5. Réutiliser les composants/classes et structures en place. Éviter les réécritures globales et les CSS qui affectent des écrans sans rapport.
6. Ne jamais inventer prix, statuts ou informations événement: les afficher depuis le backend avec gestion des valeurs manquantes.
7. Tester les états vides, chargement, erreurs, très longs noms et petits écrans; si aucune prévisualisation n'est possible, le dire.
8. Vérifier les changements avec safe-code-modification et test-and-deploy avant tout push.

Ne pas utiliser ce skill pour la direction artistique du site vitrine Next.js.
