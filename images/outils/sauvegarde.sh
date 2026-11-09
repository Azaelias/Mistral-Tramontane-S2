#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

JOURNAL="${JOURNAL:-/var/log/mistral/sauvegarde.log}"
GARDER=7

usage() {
  echo "usage : $0 [-k N] SOURCE [DESTINATION]" >&2
  exit 1
}

log() {
  printf '[%s] %s\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$*" | tee -a "$JOURNAL"
}

nettoyer() {
  [[ -n "${TMP:-}" && -e "$TMP" ]] && rm -f "$TMP"
  return 0
}
trap nettoyer EXIT

while getopts ":k:h" opt; do
  case "$opt" in
    k) GARDER="$OPTARG" ;;
    h) usage ;;
    *) usage ;;
  esac
done
shift $((OPTIND - 1))

[[ $# -ge 1 ]] || usage
SOURCE="${1%/}"
DEST="${2:-/srv/sauvegardes}"
[[ "$GARDER" =~ ^[0-9]+$ && "$GARDER" -ge 1 ]] || { echo "erreur : -k attend un entier positif" >&2; exit 1; }
[[ -d "$SOURCE" ]] || { echo "erreur : $SOURCE n'est pas un dossier" >&2; exit 2; }

mkdir -p "$DEST" "$(dirname "$JOURNAL")"
NOM="$(basename "$SOURCE")"
ARCHIVE="$DEST/$NOM-$(date +%Y%m%d-%H%M%S).tar.gz"
TMP="$ARCHIVE.part"

log "debut sauvegarde de $SOURCE"
tar -czf "$TMP" -C "$(dirname "$SOURCE")" "$NOM"
mv "$TMP" "$ARCHIVE"
log "archive creee : $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"

mapfile -t ANCIENNES < <(find "$DEST" -maxdepth 1 -name "$NOM-*.tar.gz" -printf '%f\n' | sort -r | tail -n +"$((GARDER + 1))")
for a in "${ANCIENNES[@]}"; do
  rm -f -- "$DEST/$a"
  log "rotation : $a supprimee"
done
log "fin sauvegarde, $GARDER archives conservees au plus"
