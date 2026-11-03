# Administration des devis automatiques — CRM MySelfieBooth

## Objet

Nouvelle page privée **Devis auto** accessible aux membres du personnel (compte Django `is_staff`) via la navigation ou :

`/backend/devis-auto/`

Les nouvelles demandes sont conservées dans le CRM comme auparavant. Si le module est activé et les règles sont respectées, un devis PDF est préparé et envoyé par e-mail **sans valider la réservation ni encaisser d'acompte**.

## Règles non négociables

- Les clients dont la source est `RECOMMANDATION` ou `RECOMMENDATION` sont **toujours manuels**, même si quelqu'un modifie les valeurs transmises par le navigateur.
- Les entreprises sont **toujours manuelles** (pas de demande d'acompte automatique).
- Seules les sources activées (Instagram, LinkedIn, Site internet, Leboncoin) sont autorisées.
- Les autres sources sont manuelles. Les durées autres que 3 h ou 5 h sont manuelles.
- Les codes postaux incomplets ou perdant un zéro initial sont manuels.
- Les combinaisons de plusieurs machines doivent correspondre à un pack commercial activé.
- Les machines seules doivent être explicitement activées.
- Si le prix calculé est inférieur à 350 €, l'envoi reste manuel.
- Toute erreur de calcul ou d'envoi est journalisée pour vérification.
- **Aucune réservation signée, paiement, acompte ou facture n'est validé par ce module.**

## Tarifs des six packs (5 h)

| Pack | Contenu requis | Tarif initial |
|---|---|---:|
| Souvenirs | Photobooth + Phonebooth audio + 100 porte-clés | 600 € |
| Immersion 360 | 360 Booth + Livre d'or vidéo + Fond 360 | 700 € |
| Signature | Miroirbooth + Livre d'or vidéo + Panneau Fontaine | 800 € |
| Duo VIP | Miroirbooth + 360 Booth + Phonebooth + Mur Floral | 850 € |
| Vogue Premium | Vogue Booth + Photographe + Impressions | 700 € |
| Mariage Prestige | Miroirbooth + 360 Booth + Vogue Booth + Fond 360 + Mur Floral | 1 200 € |

Les options supplémentaires et frais de déplacement sont ajoutés.
Les prix des éléments sont calculés sur le serveur depuis le catalogue CRM.
Les remises de pack apparaissent sur le PDF. Les prix peuvent être modifiés dans l'administration.

Prix de vente initiaux à 5 h : Photobooth 400 €, Miroirbooth 500 €, 360 Booth 450 €, Vogue Booth 550 €, 360 AirBooth 450 €, iPad Booth 250 €.
La formule iPad à 250 € passe manuellement en raison du seuil commercial à 350 €.
Les tarifs à 3 h restent gérés par le code existant du CRM.

## Mise en service sur PythonAnywhere

**Cette livraison GitHub ne fait aucune migration ni modification des données de production.**

1. Vérifier que les tests de la PR sont tous verts.
2. Depuis la console PythonAnywhere, dans l'environnement virtuel du site, mettre à jour le dépôt :
   `cd /home/stephanefly/reservation && git pull --ff-only`
3. Créer les **deux nouvelles tables uniquement** :
   `python manage.py migrate quote_control`
4. Recharger l'application `reservation.myselfiebooth-paris.fr` depuis l'onglet Web.
5. Ouvrir `https://reservation.myselfiebooth-paris.fr/backend/devis-auto/`, connecté avec un compte administrateur.
6. Vérifier les tarifs, simuler plusieurs devis et prévisualiser leurs PDF **avant activation**.
7. Activer l'envoi seulement après validation de la facturation, des frais de déplacement et de la réception des e-mails.

Le module est **OFF par défaut**, avec uniquement le Photobooth pré-sélectionné ; tous les packs sont **OFF** jusqu'à activation explicite.
L'ancien drapeau `INSTANT_QUOTES_ENABLED` de `settings.yaml` n'est plus utilisé : la base de données pilote désormais le module.

En cas de doute : décocher « Activer les devis automatiques » dans le CRM et enregistrer. Les demandes suivantes restent manuelles.

## Sécurité et supervision

- Les routes de paramétrage et d'aperçu PDF exigent `is_staff`.
- Le formulaire POST est protégé par CSRF, et ses prix sont validés côté serveur.
- La simulation n'envoie aucun e-mail et n'écrit aucun montant sur le dossier client.
- L'historique des tentatives envoyées, manuelles et des erreurs est visible sur la page.
- Les incidents d'envoi SMTP nécessitent encore une intervention manuelle ; aucun réenvoi automatique pour éviter les doublons.

## Tests

Le workflow GitHub vérifie le parcours du formulaire et :
`python -m django test quote_control.tests` en base isolée de test.

**Limites avant mise en service** : le système ne vérifie pas les stocks ou les équipes (choix commercial explicite), ne gère pas Stripe et ne réserve pas de matériel. Les formulaires soumis deux fois peuvent toujours créer deux demandes distinctes ; l'envoi de chaque demande reste traité séparément.
