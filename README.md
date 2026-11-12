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

2.3 update : 
## Réseau

Le portail et la base communiquent par le réseau dédié `mistral-net` : le DNS
intégré de Docker résout `base` en adresse privée, ce qui n'existe pas sur le
`bridge` par défaut. La base ne publie aucun port (`docker port base` est vide) :
elle n'est joignable que depuis le réseau, jamais depuis l'hôte.
