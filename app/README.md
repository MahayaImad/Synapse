# Synapse — app Android

Recherche hors connexion dans la nomenclature nationale, fiche produit et
équivalents, mise à jour automatique. Conception :
`docs/superpowers/specs/2026-11-01-app-recherche-design.md`.

## Installation

```bash
bash scripts/setup-flutter.sh        # Flutter stable + SDK Android (si dl.google.com est joignable)
export PATH="$HOME/flutter/bin:$PATH"
cd app && flutter pub get
```

## Tests

```bash
cd app
flutter analyze
flutter test                         # unitaires, widgets, captures (test/goldens)
flutter test --update-goldens        # seulement après avoir vérifié les écrans à l'œil
```

Le fichier `test/fixtures/` est généré par le backend (catalogue de test et
cas de parité de la recherche) :

```bash
cd backend && uv run python scripts/make_app_fixtures.py ../app/test/fixtures
```

## Nomenclature embarquée

Après chaque `synapse-admin publish`, copier la publication dans l'app
(SHA-256 vérifié) puis reconstruire :

```bash
bash scripts/sync-nomenclature.sh
```

## Construire l'APK

```bash
cd app
flutter build apk --release --dart-define=SYNAPSE_MANIFEST_URL=https://<hébergement>/manifest.json
```

Sans `SYNAPSE_MANIFEST_URL`, les mises à jour sont désactivées tant qu'une
adresse n'est pas saisie dans « À propos et mises à jour ». L'hébergement
sert `manifest.json` et le fichier `nomenclature-AAAA-MM.sqlite` qu'il nomme,
dans le même dossier (contenu de `nomenclature/publications/`).

Application : `dz.synapse.app`, nom affiché « Synapse ».
