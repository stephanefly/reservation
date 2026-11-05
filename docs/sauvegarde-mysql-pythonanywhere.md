# Sauvegardes MySQL du CRM MySelfieBooth sur PythonAnywhere

## Regle imperatives avant migration

Le module de devis automatiques est dans main (PR #120), mais necessite
la migration manuelle de deux tables quote_control. NE PAS appliquer cette
migration tant que les trois controles ne sont pas effectues : une sauvegarde
MySQL valide, une copie hors du serveur et une restauration testee sur une
base distincte.

Le script est en lecture seule pour la base : aucune migration, aucune
creation de devis, aucun changement de donnees clients et aucune restauration.

## Premiere sauvegarde manuelle

Se connecter en console Bash PythonAnywhere avec le compte stephanefly.

1. Activer le meme environnement virtuel que le site Django (voir onglet Web).
2. Verifier le depot et synchroniser seulement s'il est propre :
   cd /home/stephanefly/reservation && git status && git pull --ff-only
3. Verifier le client SQL : mysqldump --version.
   Le script utilise des options MySQL 8 recommandees par PythonAnywhere.
   En cas de client MariaDB, ne pas poursuivre si une option est inconnue.
4. Lancer la premiere sauvegarde SANS suppression :
   python scripts/backup_mysql.py --retain-days 0
5. Une archive est creee dans :
   /home/stephanefly/private-backups/reservation/
   avec une extension .sql.gz et un fichier .sql.gz.sha256.
6. Reverifier l'archive produite :
   python scripts/backup_mysql.py --verify /home/stephanefly/private-backups/reservation/NOM_ARCHIVE.sql.gz
7. Copier les DEUX fichiers hors de PythonAnywhere. Sur pCloud,
   chiffrer le dump avant transfert et conserver la cle ailleurs.
   AUCUN transfert pCloud automatique n'est configure ici.

Les identifiants MySQL sont places dans un fichier temporaire 0600 supprime
ensuite, pas dans les arguments du processus. Le dossier est prive (0700).
Ne jamais commiter une archive de production dans GitHub.

## Planification et retention

Dans PythonAnywhere > Tasks, si le compte autorise les taches planifiees,
creer une tache quotidienne avec le Python du virtualenv :

cd /home/stephanefly/reservation && /CHEMIN/DU/VIRTUALENV/bin/python scripts/backup_mysql.py --retain-days 30

Remplacer CHEMIN/DU/VIRTUALENV par le chemin exact visible dans l'onglet Web.
Les 30 jours sont une retention locale et NON une sauvegarde hors site.
La suppression n'a lieu qu'apres un nouveau dump reussi et verifie ; seuls
les dumps anciens du script avec checksum sont concernes. La toute premiere
sauvegarde ne doit pas purger les precedentes.

Surveiller les logs PythonAnywhere Tasks, l'espace disque, la date de la
derniere archive et la copie externe. Un test GitHub reussi NE prouve pas
qu'un dump a tourne en production.

## Exercice de restauration : indispensable

1. Creer une base MySQL de TEST vide, differente de la base CRM.
2. Reprendre un fichier depuis le stockage hors site ; verifier son SHA256
   et sa decompression avec --verify.
3. Importer vers cette base de TEST uniquement, avec les identifiants
   propres a celle-ci, suivant la documentation officielle PythonAnywhere.
4. Controler les tables, clients, evenements, devis et les volumes de lignes.
5. Consigner date, fichier, taille, duree et resultat du test.

Ne JAMAIS pointer une commande de restauration vers la base de production :
une restauration peut ecraser ses donnees.

## Activation ulterieure du catalogue des devis

Une fois les trois controles (backup local, hors site, restauration test)
confirmes et apres validation des tests GitHub :

1. Verifier la copie Git sur PythonAnywhere puis l'actualiser sans reset force.
2. Dans le virtualenv, inspecter : python manage.py showmigrations quote_control
3. Appliquer uniquement : python manage.py migrate quote_control
4. Recharger le site depuis PythonAnywhere > Web.
5. Tester la page privee :
   https://reservation.myselfiebooth-paris.fr/backend/devis-auto/
6. Garder les devis automatiques DESACTIVES tant que les tarifs, PDF,
   frais et exceptions Recommandation/entreprises ne sont pas controles.

Le dump MySQL ne contient ni les medias/photos du NAS ou de pCloud, ni les
fichiers de facture, ni le settings.yaml prive. Il faut les sauvegarder
separement.

Documentation PythonAnywhere :
https://help.pythonanywhere.com/pages/MySQLBackupRestore/
https://help.pythonanywhere.com/pages/ScheduledTasks/
