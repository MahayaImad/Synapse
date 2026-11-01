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

if curl -fsS -o /dev/null https://dl.google.com/android/repository/repository2-3.xml; then
  if [ ! -x "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" ]; then
    tmp=$(mktemp -d)
    curl -fsSL https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip -o "$tmp/c.zip"
    mkdir -p "$ANDROID_HOME/cmdline-tools" && unzip -q "$tmp/c.zip" -d "$tmp" && mv "$tmp/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"
    rm -rf "$tmp"
  fi
  yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses >/dev/null || true
  "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" "platform-tools" "platforms;android-35" "build-tools;35.0.0"
  flutter config --android-sdk "$ANDROID_HOME"
else
  echo "AVERTISSEMENT : dl.google.com injoignable — SDK Android non installé (flutter test fonctionne, flutter build apk non)." >&2
fi
