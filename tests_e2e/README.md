# Test du formulaire au devis envoyé

Le workflow « Test formulaire et devis » démarre sur les push vers main, les pull requests et le bouton Run workflow dans GitHub Actions.

Il utilise Chromium, les véritables vues Django, modèles, calculs, templates et générateurs de PDF. MySQL 8 est créé dans le job GitHub et détruit à sa fin. Les migrations privées, permissions et authentification de production sont hors scénario. Les routes commerciales viennent des fichiers d'URL du projet. Les autres liens de navigation sont neutralisés.

Le transport SMTP est remplacé par une capture en mémoire du message MIME complet. Aucun mail réel n'est envoyé. Google Contacts, Trello, Notion et pCloud sont simulés aux frontières. Les requêtes Python vers des services externes sont bloquées et le navigateur charge uniquement le serveur local. Aucun secret ni donnée de client réel n'est utilisé.

Les captures, PDF, mail fictif et rapport sont conservés comme artefacts du job, y compris en cas d'échec.

## Lancer en local

Depuis un environnement de développement dédié, dans le dépôt :

    python -m pip install -r tests_e2e/requirements.txt
    python -m playwright install chromium
    python -m tests_e2e.run_quote_flow

Le mode local utilise une base SQLite temporaire, supprimée à la fin. Réserver le mode MySQL au service jetable du workflow, avec son nom et ses identifiants de test fixes.

Pour un Chromium déjà installé, définir CRM_E2E_BROWSER_EXECUTABLE avec son chemin.

Ajouter les cas propres à une future option après son intégration. Un test réussi confirme le parcours isolé et le mail capturé. La délivrabilité IONOS, la migration PythonAnywhere et les services simulés doivent être vérifiés séparément.
