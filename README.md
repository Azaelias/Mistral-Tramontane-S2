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
Mistral Colis : suivi de colis conteneurisé

API de suivi de colis (Python, port 8080), livrée en image Docker
durcie et déployable avec Docker Compose ou Kubernetes (k3s).

## Prérequis

- Docker et Docker Compose
- k3s (via `python3 ../lab.py k3s ...`)
- curl

## Installation

    git clone https://github.com/Azaelias/Mistral-Tramontane-S2
    cd depot
    docker build -t mistral/colis:1.1 app/

## Lancement avec Docker Compose

    docker compose up -d
    docker compose ps
    curl -s http://127.0.0.1:8080/sante

Arrêt : `docker compose down`

## Lancement avec k3s

Importer l'image dans k3s (elle n'est pas tirée d'un registre,
`imagePullPolicy: Never`), puis déployer :

    python3 ../lab.py k3s kubectl apply -f k8s/colis.yaml
    python3 ../lab.py k3s kubectl rollout status deployment colis
    python3 ../lab.py k3s kubectl get pods,svc
    curl -s http://127.0.0.1:30080/sante

Après reconstruction de l'image : la réimporter dans k3s, puis

    python3 ../lab.py k3s kubectl rollout restart deployment colis

Suppression : `python3 ../lab.py k3s kubectl delete -f k8s/colis.yaml`

## Sécurité

- Image multi-stage, versions de base épinglées, sans compilateur
- Exécution non root (UID 10001), `runAsNonRoot: true`
- Système de fichiers en lecture seule (`readOnlyRootFilesystem`)
- Toutes les capabilities Linux retirées (`drop: ALL`),
  élévation de privilèges interdite
- Écriture limitée à `/tmp` et `/donnees` (volumes `emptyDir`)
- Ressources bornées (requests/limits CPU et mémoire)
- Sondes readiness et liveness sur `/sante`

## Limites

- Les données sont dans un `emptyDir` : perdues à la suppression
  du pod
- Chaque réplica a sa propre base SQLite : les colis enregistrés
  via un pod ne sont pas visibles depuis les autres
- Service NodePort : adapté au TP, pas à la production (prévoir un
  Ingress et TLS)
- Image locale (`imagePullPolicy: Never`) : pas de registre
