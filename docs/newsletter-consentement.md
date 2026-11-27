# Consentements e-mail du formulaire de devis

- La case du devis et des messages de suivi est obligatoire, vérifiée côté serveur et dans le navigateur. Elle n'autorise pas une inscription à la newsletter.
- La newsletter dispose d'une case distincte, facultative et non précochée. Le consentement est enregistré seulement après confirmation définitive de la demande, par adresse e-mail normalisée (sans doublon).
- Les anciens clients ne sont pas importés : `Client.autorisation_mail` était vrai par défaut et ne prouve pas un consentement aux offres commerciales.
- Les deux consentements conservent le texte accepté, l'adresse, la date et le dossier. Les abonnés sont visibles dans l'administration Django. La désinscription existante retire également l'adresse de la newsletter.
- Une demande ultérieure sans inscription à la newsletter ne réinscrit jamais un abonné désinscrit et ne désinscrit pas un abonné existant. Un nouvel accord explicite permet de se réinscrire.

La future fonctionnalité d'envoi devra utiliser exclusivement `NewsletterSubscriber.subscribed()` et inclure son propre lien de désinscription. Aucun envoi de newsletter n'est ajouté ici.

## Déploiement

Cette modification crée deux tables dans une nouvelle application Django indépendante des migrations historiques du CRM. Le déploiement automatique actuel ne lance pas les migrations. Suivre `docs/sauvegarde-mysql-pythonanywhere.md` pour la sauvegarde et les vérifications, puis appliquer exclusivement `python manage.py migrate newsletter` avant de servir la nouvelle version. Ne pas utiliser `migrate --fake`. Ne pas fusionner vers `main` tant que cette étape de déploiement n'a pas été préparée.
