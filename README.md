2.2 Update : Les Données qui restent
## Données

**Test avec volume** (`-v colis-donnees:/donnees`) :
- Colis MS-0001 créé (HTTP 201)
- Conteneur supprimé (`docker rm -f colis`) puis recréé sur le même volume
- Le colis MS-0001 est toujours lisible

**Test sans volume** :
- Colis MS-0002 créé, puis conteneur supprimé et recréé
- Le colis a disparu (HTTP 404)

**Explication** : sans volume, `/donnees` vit dans la couche inscriptible du
conteneur, détruite avec lui. Avec un volume nommé, les données vivent hors
du conteneur et survivent à sa suppression.

**Propriétaire** : `colis.db` appartient à l'uid 10001 (vérifié avec
`ls -ln`), car `/donnees` est créé et attribué à 10001 dans le Dockerfile.
# Mistral-Tramontane-S2

2.

2.3 update :
## Réseau

Le portail et la base communiquent par le réseau dédié `mistral-net` : le DNS
intégré de Docker résout `base` en adresse privée, ce qui n'existe pas sur le
`bridge` par défaut. La base ne publie aucun port (`docker port base` est vide) :
elle n'est joignable que depuis le réseau, jamais depuis l'hôte.


3.1 : 
## Rapport de sécurité : avant / après

+----------------+----------------+----------------+----------------+-----------------+
|                | HERITAGE       | 1.0            | 1.1            | Gain heritage   |
|                | (Malik)        |                |                | -> 1.1          |
+----------------+----------------+----------------+----------------+-----------------+
| Base           |Debian/Linux 13 |Debian 13.7 slim| Alpine 3.24.4  |
| Taille         | 1118 Mo        | 150 Mo         | 72 Mo          | -94 %           |
| Utilisateur    | root           | 10001          | 10001          | non root        |
| CRITICAL       | 235            | 0              | 0              | 235 -> 0        |
| HIGH           | 2539           | 49             | 0              | 2539 -> 0       |
+----------------+----------------+----------------+----------------+-----------------+

Fichiers : `securite/trivy-heritage.json`, `securite/trivy-1.1.json`,
`securite/sbom-1.1.cdx.json`.

4.1 : 
# Mistral Colis : suivi de colis conteneurisé

API de suivi de colis (Python, port 8080), livrée en image Docker
durcie et déployable avec Docker Compose ou Kubernetes (k3s).

## Prérequis

- Docker et Docker Compose
- k3s (via `python3 ../lab.py k3s ...`)
- curl, openssl

## Installation

1. Récupérer le code et construire l'image :

   ```bash
   git clone https://github.com/Azaelias/Mistral-Tramontane-S2
   cd Mistral-Tramontane-S2/depot
   docker build -t mistral/colis:1.1 app/
   ```

2. Créer les fichiers de configuration locaux.

   Le mot de passe de la base n'est **jamais** versionné (`secrets/` et
   `.env` sont dans `.gitignore`). Après un `git clone`, la stack ne démarre
   donc pas tant que ces deux fichiers n'existent pas.

   Variables non sensibles :

   ```bash
   cp .env.exemple .env
   ```

   Secret de la base (généré aléatoirement, sans retour à la ligne) :

   ```bash
   mkdir -p secrets
   openssl rand -hex 16 | tr -d '\n' > secrets/db_mdp.txt
   chmod 644 secrets/db_mdp.txt
   ```

3. Vérifier que rien ne partira sur GitHub :

   ```bash
   git check-ignore .env secrets/db_mdp.txt
   git ls-files | grep -E '(^|/)\.env$|secrets/' || echo propre
   ```

   Attendu : les deux fichiers sont listés par `check-ignore`, puis `propre`.

### Changer le mot de passe plus tard

Postgres ne lit le secret qu'à la **première** initialisation du volume.
Si vous régénérez `secrets/db_mdp.txt` sur une base existante, la connexion
échoue (`password authentication failed`).

- Environnement de test : `docker compose down -v` puis `docker compose up -d`
  (**efface les données**).
- Production : changer le mot de passe dans Postgres
  (`ALTER USER colis WITH PASSWORD '...'`), puis mettre à jour le fichier.

## Lancement avec Docker Compose

```bash
docker compose up -d
docker compose ps
curl -s http://127.0.0.1:8080/sante
```

Attendu : `web` et `base` en `(healthy)`, et `"base":"postgres"` dans la
réponse de `/sante` (comptez ~15 secondes au premier démarrage).

Arrêt : `docker compose down`
Arrêt avec suppression des données : `docker compose down -v`

## Lancement avec k3s

Importer l'image dans k3s (elle n'est pas tirée d'un registre,
`imagePullPolicy: Never`), puis déployer :

```bash
python3 ../lab.py k3s kubectl apply -f k8s/colis.yaml
python3 ../lab.py k3s kubectl rollout status deployment colis
python3 ../lab.py k3s kubectl get pods,svc
curl -s http://127.0.0.1:30080/sante
```

Après reconstruction de l'image : la réimporter dans k3s, puis

```bash
python3 ../lab.py k3s kubectl rollout restart deployment colis
```

Suppression : `python3 ../lab.py k3s kubectl delete -f k8s/colis.yaml`

## Vérifier l'installation

### Vérification manuelle (Compose)

1. Les conteneurs sont sains :

   ```bash
   docker compose ps
   ```
   Attendu : `web` et `base` en `Up ... (healthy)`.

2. Le portail voit la base :

   ```bash
   curl -s http://127.0.0.1:8080/sante
   ```
   Attendu : `"base":"postgres"`.

3. Seul `web` est publié (la base est isolée) :

   ```bash
   docker compose ps --format '{{.Service}} {{.Ports}}'
   ```
   Attendu : un port publié pour `web`, aucun pour `base`.

4. Le mot de passe n'est pas en clair :

   ```bash
   docker inspect -f '{{.Config.Env}}' $(docker compose ps -q base) | grep -c 'POSTGRES_PASSWORD='
   ```
   Attendu : `0` (seul `POSTGRES_PASSWORD_FILE` apparaît).

5. Durcissement de `web` :

   ```bash
   docker inspect -f '{{.HostConfig.ReadonlyRootfs}} {{.HostConfig.CapDrop}} {{.HostConfig.Memory}}' $(docker compose ps -q web)
   ```
   Attendu : `true [ALL] 268435456`.

### Vérification (k3s)

```bash
python3 ../lab.py k3s kubectl get pods
```
Attendu : tous les pods en `Running` et `READY 1/1`.

Auto-réparation : un pod supprimé est recréé par le Deployment.

```bash
python3 ../lab.py k3s kubectl delete pod -l app=colis --wait=false
python3 ../lab.py k3s kubectl get pods
```
Attendu : un nouveau pod apparaît aussitôt et repasse `Running`
(adaptez le sélecteur `app=colis` à celui de votre manifeste).

## Sécurité

- Image multi-stage, versions de base épinglées, sans compilateur
- Exécution non root (UID 10001), `runAsNonRoot: true`
- Système de fichiers en lecture seule (`readOnlyRootFilesystem`)
- Toutes les capabilities Linux retirées (`drop: ALL`),
  élévation de privilèges interdite
- Écriture limitée à `/tmp` et `/donnees` (volumes `emptyDir`)
- Ressources bornées (requests/limits CPU et mémoire)
- Sondes readiness et liveness sur `/sante`
- Mot de passe de la base fourni par secret (`POSTGRES_PASSWORD_FILE`),
  jamais en variable d'environnement ni dans Git
- Base de données isolée sur un réseau interne, non publiée sur l'hôte

## Limites

- Les secrets ne sont pas dans le dépôt : chaque machine doit les créer
  (voir Installation), un `git clone` seul ne suffit pas
- Compose : les données de Postgres sont dans un volume nommé, supprimé
  par `docker compose down -v`
- k3s : les données sont dans un `emptyDir`, perdues à la suppression
  du pod
- k3s : chaque réplica a sa propre base SQLite, les colis enregistrés
  via un pod ne sont pas visibles depuis les autres
- Service NodePort : adapté au TP, pas à la production (prévoir un
  Ingress et TLS)
- Image locale (`imagePullPolicy: Never`) : pas de registre
