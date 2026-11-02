#!/usr/bin/env bash
# Copie la dernière nomenclature publiée (synapse-admin publish) dans les assets de l'app, SHA-256 vérifié.
# Usage : bash scripts/sync-nomenclature.sh [dossier_publications]
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
pub="${1:-$root/nomenclature/publications}"
dest="$root/app/assets/nomenclature"
manifest="$pub/manifest.json"
[ -f "$manifest" ] || { echo "Aucun manifeste dans $pub : lancer d'abord synapse-admin publish" >&2; exit 1; }
read -r file sha < <(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); print(m["file"], m["sha256"])' "$manifest")
echo "$sha  $pub/$file" | sha256sum -c - >/dev/null || { echo "SHA-256 différent pour $file" >&2; exit 1; }
mkdir -p "$dest"
cp "$pub/$file" "$dest/nomenclature.sqlite"
cp "$manifest" "$dest/manifest.json"
echo "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$manifest") copiée dans app/assets/nomenclature/ ($file, SHA-256 vérifié)"
