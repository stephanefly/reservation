# Catalogue commercial administrable du CRM

## Acces et usage

L'administration est reservee aux comptes Django staff :
https://reservation.myselfiebooth-paris.fr/backend/catalogue/

- Creer une prestation, une option ou un pack.
- Modifier nom, description, prix TTC et activation.
- Modifier la composition des packs en cochant des machines et options.
- Choisir les quantites incluses de porte-cles ou magnets.
- Desactiver une ancienne offre sans supprimer sa fiche.
- Pour une offre existante, le code et le type sont immuables : ils peuvent deja
  etre utilises par un autre systeme.

La migration 0002 importe les 6 prestations, 14 options et 6 packs deja definis
dans le code. Elle ne modifie aucune table de l'application app et ne touche
aucun devis existant. La migration 0001 est toujours un pre-requis si les tables
devis automatiques ne sont pas encore creees sur PythonAnywhere.

**Important :** les nouvelles prestations/options qui n'ont pas de champ dans
EventProduct/EventOption sont des offres commerciales pour **devis manuels** :
leur creation dans le catalogue ne modifie pas le formulaire client, les modeles
historiques, ni les lignes PDF.

## Activation facultative de la tarification catalogue

Dans le CRM, ouvrir /backend/devis-auto/ et cocher
« Utiliser les tarifs des machines et packs du catalogue commercial ».
Le mode est **OFF par defaut** (AutoQuoteSettings.catalog_enabled=False).

Deux autres validations independantes sont requises pour envoyer un devis :
- « Activer les devis automatiques » dans le meme ecran ;
- « Eligible aux devis automatiques » dans les offres du catalogue.

Le module conserve toutes les protections : entreprises et recommandations
manuelles, sources autorisees uniquement, durees 3 h/5 h, prix minimum 350 €,
codes postaux a verifier, montants non representables dans le PDF refuses.

Les prix des machines et packs en mode catalogue ne remplacent PAS
automatiquement les tarifs historiques 3 h ou ceux des options. Pour les options,
le prix du catalogue sert de reference commerciale manuelle. Si une option
active a un prix different du prix historique du PDF, le moteur refuse son
calcul automatique plutot que de produire un PDF incoherent.
Les tarifs de panneaux XXL par quantite restent ceux de l'application actuelle.
Pour harmoniser le formulaire et tous les PDF sur de nouveaux tarifs options,
une refonte de la tarification globale sera necessaire, avec tests de
non-regression supplementaires.

Les devis et factures deja etablis ne sont pas recalcules.

## Prealables obligatoires a la production

1. Fusionner seulement apres tous les tests CI verts.
2. Verifier l'etat du depot PythonAnywhere (aucune modification locale en cours).
3. **Executer la sauvegarde reelle** introduite par la PR #121 :
   python scripts/backup_mysql.py --retain-days 0
4. Verifier le SHA-256 et copier l'archive hors de PythonAnywhere (stockage chiffre).
5. Verifier la restauration sur une base de test distincte.
6. Dans le bon virtualenv, avec les bons parametres :
   python manage.py showmigrations quote_control
   python manage.py migrate quote_control
7. Recharger l'application PythonAnywhere via l'onglet Web.
8. Ouvrir le catalogue et verifier les valeurs initiales, puis la simulation
   du devis avec le mode automatique conserve OFF.
9. Activer le mode catalogue et les offres une par une, uniquement apres
   validation des PDF et de la delivrabilite.

Ne pas executer de migration sans sauvegarde, et ne pas faire de
migrate --fake ou de reset en production.

## Retour arriere

En cas d'anomalie sur les envois automatiques, DECOCHER d'abord
« Activer les devis automatiques ». Ce choix n'efface ni catalogue ni devis.
Decocher « Utiliser les tarifs du catalogue » suffit ensuite a revenir
aux regles et prix precedents, apres enregistrement.
Ne pas supprimer les tables ni revenir en arriere sur les migrations si
elles contiennent des offres deja saisies.

## Limites

- Pas de gestion des stocks ou des disponibilites humaines.
- Pas de generation automatique de nouvelles lignes PDF pour les codes sans
  champ existant.
- Pas de recalcul des devis precedents.
- Pas de sauvegarde de fichiers media (uniquement MySQL via la PR #121).


## Synchronisation de l'affichage public

Les pages /tarifs/ et /tarifs/brochure/ lisent maintenant directement
les prix des offres actives du catalogue commercial, a chaque requete.
Changer le prix d'une machine ou d'un pack dans /backend/catalogue/
met a jour ses montants publics, sans devoir activer les devis automatiques.
Exemple : iPad Booth a 200 EUR => 200 EUR sur les deux pages.

Une offre desactivee est masquee sur les pages publiques pour les machines
et packs qui y ont deja une carte. Les formules entierement nouvelles creees
dans le catalogue ne creent pas automatiquement une nouvelle carte publique.
Les tarifs 3 h restent les tarifs historiques (le catalogue administre les
prix standards/5 h des machines).

Pour eviter des montants trompeurs, les anciennes promotions soustraites
en dur (-50 EUR et -100 EUR) ainsi que les economies des packs calculees
en dur ont ete retirees des cartes publiques. Le prix affiche est
directement celui de l'offre active. Les packs VIP et Duo VIP partagent
le meme tarif. Si les tables quote_control ne sont pas encore installees
ou si la lecture de catalogue echoue, un prix commercial de repli est
utilise pour ne pas faire tomber la vitrine.

**Attention a la separation existante entre vitrine et devis :** ceci
ne change PAS automatiquement le calcul d'un devis manuel, la grille de
prix 3 h, les lignes PDF, ni le modele de devis deja enregistre. Les tarifs
des options sont toujours indicatifs dans le catalogue. Avant de promettre
un nouveau prix public, harmoniser le processus de devis manuel si necessaire.
En particulier, la grille historique iPad dans PRIX_PRODUITS reste a 250 EUR
meme si son prix public est modifie a 200 EUR. Les envois automatiques
conservent leurs garde-fous et leur activation separee.

Cette synchronisation n'exige aucune migration supplementaire, uniquement
un rechargement du code apres la mise en production et les sauvegardes
prealables si les migrations originales restent en attente.

## Affichage des prix de base et des remises

Une seule valeur reste modifiable dans chaque offre du catalogue :
**le prix final TTC**. La remise est calculee a l'affichage, sans
changer les modeles ou les calculs de devis :

- Machine : ancien prix brut utilise par le PDF (PRIX_PRODUITS) moins
  le prix final du catalogue. Exemple : Photobooth 450 - 50 = 400 EUR.
- Pack : somme des **prix bruts** des machines et des options incluses
  (y compris les quantites de porte-cles et magnets), moins le prix final
  du pack. Exemple : Pack Duo VIP (550 + 500 + 50 + 50) - 300 = 850 EUR.
- Le detail des elements du pack est consultable dans le Catalogue.
- Si le prix final depasse le prix de reference, **aucune fausse remise**
  n'est presentee. Un code de machine ou d'option inconnu masque le calcul
  de remise plutot que d'afficher un prix invente.
- Les pages Tarifs et Brochure continuent d'afficher les prix finaux
  du catalogue, mais pas les remises ou prix barres automatiques.
  Une annonce publique de reduction de prix ne doit etre ajoutee qu'avec
  un prix de reference reel et justifiable selon la reglementation.
  Les remises calculees ici restent visibles uniquement dans le CRM.
- Le simulateur affiche le prix avant remise, la remise reellement
  appliquee par le moteur et le prix final TTC. Les frais et options
  additionnels eventuels sont inclus dans le prix avant remise du devis.

Cela n'harmonise toujours pas les prix d'options ou les tarifs de devis
manuels qui ne passent pas par le moteur automatique. Les devis existants
ne sont pas recalcules et l'envoi automatique reste independant.
