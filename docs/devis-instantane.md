# Devis instantané : déploiement progressif

## Fonctionnement prévu

- Le client remplit le formulaire public actuel. Le devis est calculé côté serveur à partir du catalogue `app/module/data_bdd/price.py`, des options et des frais de livraison déjà présents dans le CRM.
- Les choix multiples d'animations sont traités comme une formule combinée calculée depuis les produits sélectionnés ; **le tarif générique `pack=850` n'est pas appliqué automatiquement**, car il n'existe actuellement aucune correspondance sûre entre un pack commercial et les combinaisons du formulaire.
- Le client particulier provenant de `INSTAGRAM`, `LINKEDIN`, `SITE INTERNET` ou `LEBONCOIN` peut recevoir son devis PDF par e-mail, sans valider automatiquement une réservation.
- La valeur exacte `RECOMMANDATION` (quelle que soit la casse ou les espaces autour) est **toujours manuelle** : la demande est stockée, aucun prix ni e-mail de devis ne sont générés automatiquement.
- Les entreprises restent également manuelles (facture totale sans acompte selon le processus habituel).
- Une source inconnue, l'absence de prestation, une durée inhabituelle, un code postal douteux ou un montant inférieur à 350 € conduisent au traitement manuel.
- Si la préparation ou l'envoi échoue, la demande n'est pas supprimée ; elle reste dans le CRM. Le résultat des tests SMTP est suivi séparément.

## Activation

Le moteur est **désactivé par défaut**. Ne l'activer qu'après validation des prix des packs et des scénarios d'e-mails en environnement de test.

Dans le fichier PythonAnywhere `/home/stephanefly/reservation/myselfiebooth/settings.yaml` (exclu de Git) :

```yaml
INSTANT_QUOTES_ENABLED: true
```

Supprimer cette entrée ou la définir à `false` pour désactiver immédiatement les envois automatiques au prochain rechargement Django.

Le déploiement du code seul ne déclenche **aucun envoi automatique**. Il n'y a ni migration de base, ni encaissement ni réservation confirmée.

## Vérifications avant activation

1. Pour un client trouvé par **Recommandation**, le CRM garde le dossier à traiter manuellement.
2. Tester un Photobooth 3 h, 5 h, et un combo de plusieurs animations avec options.
3. Vérifier la cohérence du prix final avec le PDF du devis, notamment le prix des packs commerciaux.
4. Vérifier les frais de livraison (codes postaux commençant par 0 = traitement manuel tant que la colonne est numérique).
5. Vérifier que les e-mails envoyés passent l'authentification et sont correctement reçus.
6. Vérifier que les doubles soumissions de formulaire ne génèrent pas deux demandes.

Fichiers : `app/module/data_bdd/instant_quote.py`, `app/views/frontend_views.py`, `app/tests/test_instant_quote.py`.
