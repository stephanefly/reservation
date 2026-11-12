---
name: test-and-deploy
description: "Utiliser avant de valider, committer, pousser ou déployer un changement du CRM Django MySelfieBooth."
---

# Vérification et livraison — CRM Django

1. Examiner git status et git diff; rechercher fichiers sensibles, secrets, migrations ou modifications hors sujet.
2. Exécuter si les outils sont disponibles:
    git diff --check
    python -m compileall -q app myselfiebooth
    python -m unittest discover -s app/tests -p "test_*.py"
3. Si la configuration YAML locale et les dépendances sont disponibles, exécuter aussi:
    python manage.py check
   En cas d'échec dû à une configuration/secrets/DB absents, indiquer « non vérifié », pas « tests réussis ».
4. Pour les modifications de modèles, inspecter les migrations et utiliser uniquement des vérifications hors production; ne pas exécuter migrate contre MySQL réel sans autorisation et sauvegarde confirmée.
5. Vérifier le comportement ciblé et ses régressions; distinguer tests unitaires, tests manuels et vérifications impossibles.
6. Branche principale du dépôt: main. Aucun pipeline de déploiement CRM n'est présumé; PythonAnywhere doit faire l'objet d'une procédure explicitement demandée.
7. Ne pas effectuer de push, fusion, publication, redémarrage ou déploiement sans instruction explicite. Si la demande inclut un push, vérifier la branche cible et annoncer tout risque de production.
8. Livrer un résumé: fichiers touchés, tests exécutés/résultats, risques résiduels et éventuelles étapes de déploiement.

Un fichier SKILL.md seul ne remplace pas l'exécution réelle des tests.
