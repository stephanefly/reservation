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
3. **Avant toute migration**, créer une sauvegarde MySQL réelle, vérifier son intégrité, conserver une copie chiffrée hors site et tester une restauration isolée (voir `docs/sauvegarde-mysql-pythonanywhere.md`). Ensuite, appliquer les migrations `quote_control` nécessaires :
   `python manage.py migrate quote_control`
4. Recharger l'application `reservation.myselfiebooth-paris.fr` depuis l'onglet Web.
5. Ouvrir `https://reservation.myselfiebooth-paris.fr/backend/devis-auto/`, connecté avec un compte administrateur.
6. Vérifier les tarifs et simuler des demandes fictives (machines, options, durée, code postal) **avant activation**. Le simulateur affiche le montant ou le motif de traitement manuel, sans générer de PDF ni enregistrer de client.
7. Activer l'envoi seulement après validation de la facturation, des frais de déplacement et de la réception des e-mails.

Le module est **OFF par défaut**, avec uniquement le Photobooth pré-sélectionné ; tous les packs sont **OFF** jusqu'à activation explicite.
L'ancien drapeau `INSTANT_QUOTES_ENABLED` de `settings.yaml` n'est plus utilisé : la base de données pilote désormais le module.

En cas de doute : décocher « Activer les devis automatiques » dans le CRM et enregistrer. Les demandes suivantes restent manuelles.

## Sécurité et supervision

- Les routes de paramétrage et d'aperçu PDF exigent `is_staff`.
- Le formulaire POST est protégé par CSRF, et ses prix sont validés côté serveur.
- Le nouveau simulateur n'envoie aucun e-mail, ne crée ni dossier client ni PDF et n'écrit aucun montant en base. Il utilise le même moteur d'éligibilité que les demandes réelles, en mode aperçu.
- L'historique des tentatives envoyées, manuelles et des erreurs est visible sur la page.
- Les incidents d'envoi SMTP nécessitent encore une intervention manuelle ; aucun réenvoi automatique pour éviter les doublons.

## Tests

Le workflow GitHub vérifie le parcours du formulaire et :
`python -m django test quote_control.tests` en base isolée de test.

**Limites avant mise en service** : le système ne vérifie pas les stocks ou les équipes (choix commercial explicite), ne gère pas Stripe et ne réserve pas de matériel. Les formulaires soumis deux fois peuvent toujours créer deux demandes distinctes ; l'envoi de chaque demande reste traité séparément.

## Nouvelle interface simplifiée

Deux blocs seulement : **Paramétrage** et **Simulation**.
Les sources, les packs de l'ancien mode, les anciens prix et l'historique sont accessibles via des sections repliées à l'intérieur de Paramétrage.

Dans Simulation, sélectionner directement une ou plusieurs machines (exemple : Photobooth + Miroirbooth), la durée 3 h ou 5 h, un code postal, les options éventuelles et la source de la demande, puis cliquer sur **Calculer le devis**.
Le moteur indique le prix TTC lorsque la demande est éligible et le motif lorsque le dossier doit être traité manuellement. **Aucun e-mail et aucun PDF client ne sont créés.** L'ancien aperçu d'un véritable dossier reste accessible aux tests internes et à son URL privée, sans être présenté comme la simulation principale.

Une simulation ne contourne pas les règles : le mode catalogue, l'éligibilité des produits/packs, le seuil minimum de 350 €, les entreprises et recommandations restent pris en compte. Elle n'active pas l'envoi réel.


## Navigation depuis le Catalogue

La page Devis auto n'a plus de lien propre dans le menu. Toutes ses
fonctions sont accessibles depuis **Catalogue > Paramètres et simulation**,
sur /backend/catalogue/?tab=automation.

La configuration des envois et la simulation restent dans deux sections
simples ; les réglages avancés et les logs sont dépliables. Le Catalogue
conserve l'onglet **Offres et tarifs** pour l'édition des machines, options,
packs et remises.

L'ancienne URL /backend/devis-auto/ redirige vers le Catalogue, en
préservant les paramètres de simulation. L'ancienne URL d'aperçu PDF
privée et les POST historiques restent compatibles.

Le nom de client ou d'entreprise dans la simulation est facultatif,
n'est pas sauvegardé, et le nom d'entreprise fait passer le résultat
en traitement manuel conformément aux règles existantes.

Le passage en production implique toujours sauvegarde MySQL
vérifiée et restauration testée en environnement isolé ; la fusion
GitHub ne constitue pas un déploiement PythonAnywhere.
