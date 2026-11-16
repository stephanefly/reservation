# Codex — MySelfieBooth CRM

Projet Django 4.2 / MySQL. Le fichier myselfiebooth/settings.py charge une configuration YAML locale non versionnée. Ne jamais afficher, créer avec de vraies valeurs, ni versionner de secrets.

- Lire le code et les tests liés à la demande avant toute modification. Réduire le diff au nécessaire; conserver les comportements existants hors du périmètre demandé.
- Protéger réservations, acomptes, statuts, prix, devis, relances, emails/SMS et accès par rôle. Ne pas envoyer de véritables communications pendant les tests.
- Ne pas appliquer de migration à une base de production, modifier des données réelles ou déployer sur PythonAnywhere sans instruction explicite.
- Tests: privilégier app/tests, signaler ce qui n'a pas été exécuté faute de configuration/dépendances.
- Les procédures spécialisées sont dans .agents/skills/: safe-code-modification, myselfiebooth-design, test-and-deploy. Les charger lorsqu'elles sont pertinentes.
- À la fin, résumer les fichiers changés, résultats des tests, points non vérifiés et actions manuelles nécessaires.
