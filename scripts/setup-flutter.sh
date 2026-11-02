#!/usr/bin/env bash
# Installe Flutter stable (vérifié par SHA-256) et, si dl.google.com est joignable, le SDK Android.
# Idempotent. Usage : bash scripts/setup-flutter.sh
set -euo pipefail
FLUTTER_HOME="${FLUTTER_HOME:-$HOME/flutter}"
ANDROID_HOME="${ANDROID_HOME:-$HOME/android-sdk}"
BASE=https://storage.googleapis.com/flutter_infra_release/releases

if [ ! -x "$FLUTTER_HOME/bin/flutter" ]; then
  meta=$(curl -fsSL "$BASE/releases_linux.json")
  read -r archive sha < <(python3 -c '
import json,sys
d=json.loads(sys.stdin.read()); h=d["current_release"]["stable"]
r=next(x for x in d["releases"] if x["hash"]==h); print(r["archive"], r["sha256"])' <<<"$meta")
  tmp=$(mktemp -d)
  curl -fsSL "$BASE/$archive" -o "$tmp/flutter.tar.xz"
  echo "$sha  $tmp/flutter.tar.xz" | sha256sum -c -
  mkdir -p "$(dirname "$FLUTTER_HOME")"
  tar -xJf "$tmp/flutter.tar.xz" -C "$(dirname "$FLUTTER_HOME")"
  [ "$(dirname "$FLUTTER_HOME")/flutter" = "$FLUTTER_HOME" ] || mv "$(dirname "$FLUTTER_HOME")/flutter" "$FLUTTER_HOME"
  rm -rf "$tmp"
fi
git config --global --add safe.directory "$FLUTTER_HOME" || true
export PATH="$FLUTTER_HOME/bin:$PATH"
flutter --disable-analytics >/dev/null 2>&1 || true
flutter --version

REPO=https://dl.google.com/android/repository
if curl -fsS -o /dev/null "$REPO/repository2-3.xml"; then
  if [ ! -x "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" ]; then
    tmp=$(mktemp -d)
    curl -fsSL "$REPO/repository2-3.xml" -o "$tmp/repo.xml"
    # Archive Linux des cmdline-tools la plus récente, avec l'empreinte SHA-1 publiée dans l'index de Google.
    read -r zip sha1 < <(python3 - "$tmp/repo.xml" <<'PY'
import re, sys, xml.etree.ElementTree as ET
best = None
for pkg in ET.parse(sys.argv[1]).getroot().iter():
    if not pkg.tag.endswith("remotePackage") or not pkg.get("path", "").startswith("cmdline-tools;"):
        continue
    for a in pkg.iter():
        if a.tag.endswith("archive"):
            url = next((u.text for u in a.iter() if u.tag.endswith("url")), "") or ""
            sha = next((c.text for c in a.iter() if c.tag.endswith("checksum")), "") or ""
            if re.fullmatch(r"commandlinetools-linux-\d+_latest\.zip", url) and re.fullmatch(r"[0-9a-f]{40}", sha):
                n = int(re.search(r"\d+", url).group())
                if best is None or n > best[0]:
                    best = (n, url, sha)
if best is None:
    sys.exit("archive cmdline-tools Linux introuvable dans repository2-3.xml")
print(best[1], best[2])
PY
)
    curl -fsSL "$REPO/$zip" -o "$tmp/c.zip"
    echo "$sha1  $tmp/c.zip" | sha1sum -c - >/dev/null || { echo "Empreinte SHA-1 différente pour $zip" >&2; exit 1; }
    mkdir -p "$ANDROID_HOME/cmdline-tools" && unzip -q "$tmp/c.zip" -d "$tmp" && mv "$tmp/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"
    rm -rf "$tmp"
  fi
  yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses >/dev/null || true
  "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" "platform-tools" "platforms;android-35" "build-tools;35.0.0"
  flutter config --android-sdk "$ANDROID_HOME"
else
  echo "AVERTISSEMENT : dl.google.com injoignable — SDK Android non installé (flutter test fonctionne, flutter build apk non)." >&2
fi
