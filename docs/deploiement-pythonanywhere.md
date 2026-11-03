# Déploiement du CRM MySelfieBooth sur PythonAnywhere (sans supplément)

Le dépôt `stephanefly/reservation` déclenche déjà les tests sur chaque `push` vers `main`. Le workflow `.github/workflows/deploy-pythonanywhere.yml` attend leur **réussite** puis peut automatiquement :

1. Se connecter en SSH à PythonAnywhere avec une clé dédiée.
2. Vérifier que la copie distante est bien sur `main`, sans modifications locales.
3. Faire un `git fetch`, puis une mise à jour `git merge --ff-only` vers **le commit testé**, sans jamais écraser les changements locaux.
4. Demander le **reload** de `reservation.myselfiebooth-paris.fr` via l'API officielle PythonAnywhere.

Il n'exécute **ni `migrate`**, ni `pip install`, ni `collectstatic` : il reproduit la procédure actuelle « git pull + reload ». Si un changement requiert une migration, traiter ce cas séparément avant la mise en production.

## Configuration initiale (une seule fois)

### 1. Vérifier PythonAnywhere

Dans une console Bash PythonAnywhere :

```bash
whoami
pwd
git -C /home/VOTRE_UTILISATEUR/chemin/du/projet branch --show-current
```

Le dossier doit être celui où `git pull` fonctionne actuellement, et la branche doit être `main`.

L'hôte SSH/API est **global** (`ssh.pythonanywhere.com` + `www.pythonanywhere.com`) ou **EU** (`ssh.eu.pythonanywhere.com` + `eu.pythonanywhere.com`), selon l'URL de connexion à votre compte.

### 2. Créer une clé SSH *dédiée* sur votre ordinateur

Ouvrir PowerShell :

```powershell
ssh-keygen -t ed25519 -C "github-actions-reservation" -f "$HOME\.ssh\pythonanywhere_deploy"
```

Pour un usage GitHub Actions non interactif, laisser la passphrase vide pour **cette clé dédiée uniquement**. Ne jamais envoyer la clé privée dans un chat ni la commiter dans Git.

Afficher **la clé publique** :

```powershell
Get-Content "$HOME\.ssh\pythonanywhere_deploy.pub"
```

Sur PythonAnywhere, dans une console Bash :

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Ajouter la ligne `ssh-ed25519 ...` de la clé publique dans `authorized_keys`.

### 3. Vérifier la clé d'hôte SSH de PythonAnywhere

Sur votre ordinateur, récupérer les clés hôtes du serveur SSH PythonAnywhere utilisé :

```powershell
ssh-keyscan -t rsa,ecdsa,ed25519 ssh.pythonanywhere.com > "$HOME\.ssh\pythonanywhere_known_hosts"
ssh-keygen -lf "$HOME\.ssh\pythonanywhere_known_hosts"
```

**Comparer l'empreinte à celle de la documentation officielle** avant d'accepter les clés hôtes ; ne pas désactiver le contrôle SSH. Pour le site global, PythonAnywhere publie l'empreinte `SHA256:zy2jmqxNg/fs6tFZK55OjHTI3B2UofzOiUvTPtcX3/Y`. Si votre compte est hébergé dans l'UE, remplacer l'hôte par `ssh.eu.pythonanywhere.com` et vérifier son empreinte auprès de PythonAnywhere.

### 4. Définir les secrets et variables GitHub

Dans [GitHub → Settings → Secrets and variables → Actions](https://github.com/stephanefly/reservation/settings/secrets/actions), configurer :

| Type | Nom | Valeur |
|---|---|---|
| Variable optionnelle | `PA_SSH_HOST` | `ssh.pythonanywhere.com` (défaut) ou `ssh.eu.pythonanywhere.com` |
| Variable optionnelle | `PA_API_HOST` | `www.pythonanywhere.com` (défaut) ou `eu.pythonanywhere.com` |
| Secret | `PA_SSH_PRIVATE_KEY` | Contenu **complet** de `pythonanywhere_deploy`, sans l'extension `.pub` |
| Secret | `PA_SSH_KNOWN_HOSTS` | Contenu du fichier `pythonanywhere_known_hosts`, après vérification |
| Secret | `PA_API_TOKEN` | Jeton créé dans PythonAnywhere > Account > API Token |

Le compte `stephanefly`, le chemin `/home/stephanefly/reservation` et le nom de domaine `reservation.myselfiebooth-paris.fr` sont déjà configurés dans le workflow. Aucun paramètre GitHub n'est à saisir pour ces trois valeurs.

### 5. Activer

**En dernier**, ajouter la variable GitHub `PA_AUTODEPLOY_ENABLED` avec la valeur exacte `true`.

Tant qu'elle est absente ou différente de `true`, le workflow ne fait **aucun déploiement**.

## Fonctionnement et restrictions

- Déclenchement : réussite de `Test formulaire et devis` pour un événement **push sur main** seulement, jamais pour une PR.
- Pas de secrets dans les fichiers de code ou les logs du dépôt.
- Le travail en cours sur PythonAnywhere n'est jamais écrasé : les fichiers suivis modifiés bloquent le déploiement.
- Si `main` a changé pendant les tests, l'ancien commit n'est **pas** déployé.
- Le déploiement échoue en cas d'erreur SSH ou API, avec trace dans **Actions**.
- Les commandes métier de maintenance, les migrations et les dépendances requièrent une procédure spécifique.
- Le statut de l'API signifie qu'un rechargement a été demandé, pas une garantie qu'aucune erreur applicative n'est possible.

Documentation : [SSH PythonAnywhere](https://help.pythonanywhere.com/pages/SSHAccess), [API PythonAnywhere](https://help.pythonanywhere.com/pages/API).
