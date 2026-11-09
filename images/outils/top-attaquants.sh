#!/usr/bin/env bash
set -euo pipefail

N=5
usage() {
  echo "usage : $0 [-n N] [FICHIER]" >&2
  exit 1
}

while getopts ":n:h" opt; do
  case "$opt" in
    n) N="$OPTARG" ;;
    *) usage ;;
  esac
done
shift $((OPTIND - 1))

[[ "$N" =~ ^[0-9]+$ ]] || usage
FICHIER="${1:-/var/log/mistral/auth.log}"
[[ -r "$FICHIER" ]] || { echo "erreur : $FICHIER illisible" >&2; exit 2; }

grep 'Failed password' "$FICHIER" \
  | awk '{ for (i = 1; i <= NF; i++) if ($i == "from") print $(i + 1) }' \
  | sort | uniq -c | sort -k1,1nr -k2,2 | head -n "$N" | awk '{ print $1, $2 }'
