# App Synapse : recherche et fiche — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** App Android Flutter qui cherche hors connexion dans la nomenclature publiée par `synapse-admin`, affiche la fiche produit et ses équivalents, et se met à jour seule depuis un `manifest.json`.

**Architecture:** Couche données pure Dart (`lib/data/`) sur le fichier SQLite publié, ouverte en lecture seule via `sqlite3` + `sqlite3_flutter_libs` ; la recherche est un portage de `backend/src/synapse_admin/search.py` vérifié par des cas générés par le backend. Un `NomenclatureStore` (`ChangeNotifier`) détient la base courante et la remplace atomiquement à la mise à jour. UI Material 3 standard (`lib/ui/`), chaînes en ARB.

**Tech Stack:** Flutter stable (Dart 3), `sqlite3`, `sqlite3_flutter_libs`, `path_provider`, `http`, `crypto`, `connectivity_plus`, `shared_preferences`, `dynamic_color`, `flutter_localizations`/`intl`, `flutter_test` (goldens).

**Spec:** `docs/superpowers/specs/2026-11-01-app-recherche-design.md` (+ brief `.impeccable/surfaces/app-lib-main-dart.md`, `PRODUCT.md`)

## Global Constraints

- Recherche < 300 ms ; toujours disponible hors connexion ; base ouverte en lecture seule.
- Résultats de recherche identiques à `synapse-admin search` (mêmes ids, même ordre) sur le jeu de cas du backend.
- Statut toujours visible : « Retiré » (rôle erreur), « Non renouvelé » (couleur d'avertissement harmonisée) sur chaque ligne et en tête de fiche.
- Produit retiré / non renouvelé : équivalents **en vigueur, même dosage** juste sous le statut.
- Équivalents : même `code_dci` ; même dosage = dosages égaux espaces retirés ; « Même dosage » puis « Autres dosages » groupés.
- Mise à jour : Wi-Fi seulement, au lancement puis toutes les 24 h ; version strictement postérieure ; taille + SHA-256 + `meta.version` + `PRAGMA integrity_check` vérifiés avant remplacement atomique ; échec = base inchangée ; URL vide = mise à jour désactivée.
- Material 3 standard, couleurs dynamiques avec repli statique, thème sombre complet ; cibles ≥ 48 dp ; tailles en sp via l'échelle Material ; geste Retour système respecté ; mise en page directionnelle (`EdgeInsetsDirectional`, `start`/`end`).
- Toutes les chaînes dans `lib/l10n/app_fr.arb` ; français seulement.
- Aucune donnée personnelle, aucune télémétrie. Application `dz.synapse.app`, nom affiché « Synapse ».
- Aucun texte du direction contract dans le code source livré.

## Review Focus

1. **Police système ×2,0** → aucun débordement (`RenderFlex overflowed`) ni texte coupé sur les lignes de résultat et la fiche. Test : Tasks 9 et 10.
2. **Libellés réels très longs** (conditionnement de 200 caractères, DCI composées) → ellipse sur 1–2 lignes dans la liste, texte complet dans la fiche. Test : Tasks 9 et 10.
3. **Mise à jour pendant une recherche ou une fiche ouverte** → aucune exception ; la fiche d'un produit absent de la nouvelle version affiche « Ce produit ne figure plus dans la nomenclature … ». Test : Tasks 6 et 10.
4. **Manifeste invalide** (JSON cassé, champ manquant, HTTP 404, délai dépassé, fichier tronqué) → `UpdateOutcome.failed` avec message, base inchangée. Test : Task 7.
5. **Requêtes spéciales** (`"`, `*`, `-`, `L'ALCOOL`, `é`, vide, 300 caractères) → pas d'exception, mêmes résultats que le backend. Test : Task 4.

---

## Structure des fichiers

```
scripts/setup-flutter.sh          # installe Flutter + Android SDK (environnement neuf)
scripts/sync-nomenclature.sh      # copie la dernière publication dans app/assets/
backend/scripts/make_app_fixtures.py
app/
  pubspec.yaml, l10n.yaml, analysis_options.yaml
  android/                        # applicationId dz.synapse.app, minSdk 23
  assets/nomenclature/            # nomenclature-AAAA-MM.sqlite + manifest.json
  lib/
    main.dart, app.dart
    data/product.dart             # Product, ProductStatus, NomenclatureMeta
    data/nomenclature_db.dart     # NomenclatureDb
    data/text.dart                # stripAccents, tokens, trigrams, dosageKey
    data/search.dart
    data/equivalents.dart
    data/store.dart               # NomenclatureStore
    data/manifest.dart
    data/update_service.dart
    data/settings.dart
    ui/theme.dart                 # thème M3, StatusColors (ThemeExtension)
    ui/widgets/status_chip.dart, ui/widgets/product_tile.dart
    ui/search/search_screen.dart
    ui/product/product_screen.dart
    ui/about/about_screen.dart
    l10n/app_fr.arb
  test/
    fixtures/                     # générés par le backend
    fonts/                        # Roboto pour les goldens
    goldens/
    *_test.dart
```

---

### Task 1: Outillage et squelette Flutter

**Files:**
- Create: `scripts/setup-flutter.sh`, `app/` (via `flutter create`), `app/analysis_options.yaml`, `app/test/smoke_test.dart`
- Modify: `.gitignore` (`app/build/`, `app/.dart_tool/`, `app/android/.gradle/` déjà couverts ; vérifier), `CLAUDE.md` (commande de setup)

**Interfaces:**
- Produces: projet `app/` compilable ; `flutter test` exécutable ; `bash scripts/setup-flutter.sh` idempotent qui installe Flutter stable dans `$HOME/flutter` et le SDK Android (cmdline-tools, `platforms;android-35`, `build-tools;35.0.0`, `platform-tools`) dans `$HOME/android-sdk`, licences acceptées.

- [ ] **Step 1:** Écrire `scripts/setup-flutter.sh` (téléchargement de l'archive stable listée par `releases_linux.json`, `flutter config --android-sdk`, `sdkmanager --install …`, `yes | sdkmanager --licenses`), l'exécuter. Expected : `flutter doctor` → Flutter ✓, Android toolchain ✓.
- [ ] **Step 2:** `flutter create --org dz.synapse --project-name synapse --platforms android app`, ajouter les dépendances de la stack, `flutter pub get`.
- [ ] **Step 3: Failing test** `test/smoke_test.dart` : `testWidgets('app démarre', …)` qui pompe `SynapseApp` et trouve le titre « Synapse » → FAIL (classe absente).
- [ ] **Step 4:** `lib/app.dart` : `SynapseApp` minimal (`MaterialApp(title: 'Synapse', home: Scaffold(appBar: AppBar(title: Text('Synapse'))))`) → `flutter test` PASS ; `flutter analyze` sans problème.
- [ ] **Step 5:** Vérifier que `sqlite3` fonctionne sous `flutter test` sur l'hôte (FTS5 + `trigram`) par un test jetable ; si la bibliothèque système manque ou est trop ancienne, consigner la solution retenue (ruling).
- [ ] **Step 6:** Commit `feat(app): flutter skeleton and setup script`

---

### Task 2: Fichier de test et cas de parité (backend)

**Files:**
- Create: `backend/scripts/make_app_fixtures.py`, `backend/tests/test_app_fixtures.py`
- Output: `app/test/fixtures/nomenclature-test.sqlite`, `app/test/fixtures/search_cases.json`, `app/test/fixtures/equivalents_cases.json`

**Interfaces:**
- Consumes: `synapse_admin.export.export_sqlite`, `synapse_admin.search.search`, `tests/rows.product`
- Produces:
  - Catalogue synthétique déterministe (ids `uuid5` fixes) d'environ 40 produits couvrant : même code DCI à plusieurs dosages et formes, dosages qui ne diffèrent que par des espaces, un produit retiré avec équivalents en vigueur, un non renouvelé, un stupéfiant, accents dans la DCI, `ALCOOL CHIRURGICAL 90°`, un conditionnement de 200 caractères, une marque qui ne se trouve que par faute de frappe.
  - `search_cases.json` : `[{"query": str, "limit": int, "ids": [str]}]` — au moins 40 requêtes dont celles du Review Focus 5.
  - `equivalents_cases.json` : `[{"id": str, "same_dosage": [id], "other_dosages": {dosage: [id]}}]` calculés par une fonction Python de référence `equivalents(db, id)` écrite dans le script (même code DCI ; dosage clé = sans espaces ; tri : statut puis marque).
  - `uv run python scripts/make_app_fixtures.py ../app/test/fixtures` régénère les trois fichiers.

- [ ] **Step 1: Failing test** `test_fixtures_are_deterministic` (deux générations dans deux dossiers → même `search_cases.json`, mêmes lignes produit) et `test_cases_cover_review_focus` (les 8 requêtes spéciales présentes).
- [ ] **Step 2–4:** FAIL → implémenter → PASS ; générer les fichiers dans `app/test/fixtures/`.
- [ ] **Step 5:** Commit `test(app): backend-generated fixtures and parity cases`

---

### Task 3: Modèle produit et accès à la base

**Files:**
- Create: `app/lib/data/product.dart`, `app/lib/data/nomenclature_db.dart`, `app/test/data/nomenclature_db_test.dart`

**Interfaces:**
- Produces:
  - `enum ProductStatus { enVigueur, nonRenouvele, retire }` + `static ProductStatus fromDb(String)` (`en_vigueur`, `non_renouvele`, `retire`) + `int get rank`.
  - `class Product` (immutable) : `id, marque, dci, codeDci, forme, dosage, conditionnement, String? liste, ProductStatus statut, String? origine, DateTime? dateRetrait, String? typeRetrait, String? motifRetrait, labo, pays, String? type, bool hopital, bool officine, nEnregistrement` ; `factory Product.fromRow(Row r)`.
  - `class NomenclatureMeta { String version; DateTime referenceDate; int products; DateTime publishedAt; }`
  - `class NomenclatureDb { static NomenclatureDb open(String path); NomenclatureMeta get meta; Product? productById(String id); Database get raw; void close(); }` — ouverture `OpenMode.readOnly` ; lève `NomenclatureFormatError` si la table `meta` ou `produit` manque.

- [ ] **Step 1: Failing tests** : ouverture du fichier de test → `meta.version == '2026-08'`, `products` = nombre du catalogue ; `productById` d'un id connu → marque attendue, statut, date de retrait ; id inconnu → `null` ; fichier non SQLite → `NomenclatureFormatError` ; écriture refusée (lecture seule).
- [ ] **Step 2–4:** FAIL → implémenter → PASS
- [ ] **Step 5:** Commit `feat(app): product model and read-only database`

---

### Task 4: Recherche (portage et parité)

**Files:**
- Create: `app/lib/data/text.dart`, `app/lib/data/search.dart`, `app/test/data/search_test.dart`

**Interfaces:**
- Consumes: `NomenclatureDb.raw`, `Product.fromRow`
- Produces:
  - `String stripAccents(String)`, `List<String> searchTokens(String query)` (élisions `L' D' J' C' M' N' S' T'`, max 8 jetons), `Set<String> trigrams(String)`, `String dosageKey(String)` (espaces retirés).
  - `List<Product> search(NomenclatureDb db, String query, {int limit = 20})` — même algorithme et mêmes constantes que `search.py` (`TRIGRAM_CANDIDATES = 400`, Dice ≥ 0,5, longueur compacte ≥ 4 pour le repli, tri par rang de statut puis bm25 / similarité).

- [ ] **Step 1: Failing test** `parité avec le backend` : pour chaque cas de `search_cases.json`, `search(db, q, limit: l).map((p) => p.id)` égale exactement `ids`.
- [ ] **Step 2:** Tests unitaires de `stripAccents('PARACÉTAMOL') == 'PARACETAMOL'`, `searchTokens("l'alcool 90°") == ['ALCOOL', '90']`, `searchTokens('') == []`.
- [ ] **Step 3–4:** FAIL → implémenter → PASS
- [ ] **Step 5:** Test de performance : 50 requêtes sur le fichier de test agrandi à 9 500 lignes (copie synthétique en mémoire) → maximum < 300 ms sur l'hôte.
- [ ] **Step 6:** Commit `feat(app): offline search ported from backend`

---

### Task 5: Équivalents

**Files:**
- Create: `app/lib/data/equivalents.dart`, `app/test/data/equivalents_test.dart`

**Interfaces:**
- Consumes: `NomenclatureDb`, `Product`, `dosageKey`
- Produces:
  - `class Equivalents { final List<Product> sameDosage; final Map<String, List<Product>> otherDosages; List<Product> get activeSameDosage; bool get isEmpty; }` — le produit lui-même exclu ; listes triées par rang de statut puis marque ; `otherDosages` dans l'ordre des dosages tel que `equivalents_cases.json`.
  - `Equivalents equivalentsOf(NomenclatureDb db, Product p)`.

- [ ] **Step 1: Failing test** : parité avec chaque cas de `equivalents_cases.json` ; produit retiré du catalogue → `activeSameDosage` non vide et uniquement `enVigueur` ; dosages `10 MG` / `10MG` dans le même groupe.
- [ ] **Step 2–4:** FAIL → implémenter → PASS
- [ ] **Step 5:** Commit `feat(app): equivalents by DCI code and dosage`

---

### Task 6: Stockage et remplacement de la base

**Files:**
- Create: `app/lib/data/store.dart`, `app/test/data/store_test.dart`

**Interfaces:**
- Consumes: `NomenclatureDb`
- Produces:
  - `typedef AssetBytes = Future<ByteData> Function(String key);`
  - `class NomenclatureStore extends ChangeNotifier { NomenclatureStore({required Directory dir, required AssetBytes loadAsset, String embeddedKey = 'assets/nomenclature/nomenclature.sqlite'}); Future<void> init(); NomenclatureDb get db; NomenclatureMeta get meta; Future<void> install(File verified); }`
  - `init()` : installe l'asset dans `dir/nomenclature.sqlite` s'il n'existe pas, ou si la version embarquée est postérieure à l'installée (mise à jour de l'APK) ; sinon ouvre l'existant.
  - `install(file)` : renomme `file` en `dir/nomenclature.sqlite` (même système de fichiers), ouvre la nouvelle base, remplace la référence, **puis** ferme l'ancienne, `notifyListeners()`.

- [ ] **Step 1: Failing tests** : premier lancement → base copiée, `meta.version` ; second `init` → pas de recopie (mtime inchangé) ; asset plus récent → recopie ; `install` → version nouvelle, écouteur notifié ; une recherche lancée sur l'ancienne référence juste avant `install` se termine sans exception (Review Focus 3) ; `install` d'un fichier invalide → exception et ancienne base toujours ouverte.
- [ ] **Step 2–4:** FAIL → implémenter → PASS
- [ ] **Step 5:** Commit `feat(app): nomenclature store with atomic replacement`

---

### Task 7: Manifeste et service de mise à jour

**Files:**
- Create: `app/lib/data/manifest.dart`, `app/lib/data/update_service.dart`, `app/test/data/update_service_test.dart`

**Interfaces:**
- Consumes: `NomenclatureStore.install`, `NomenclatureDb.open`
- Produces:
  - `class Manifest { version, referenceDate, file, int size, sha256, publishedAt; static Manifest parse(String json); }` — lève `FormatException` (champ manquant ou de mauvais type).
  - `enum UpdateOutcome { upToDate, updated, disabled, waitingForWifi, failed }`
  - `class UpdateResult { UpdateOutcome outcome; String? newVersion; String? error; DateTime checkedAt; }`
  - `class UpdateService { UpdateService({required http.Client client, required NomenclatureStore store, required Future<String> Function() manifestUrl, required Future<bool> Function() onUnmeteredNetwork, required Directory tmpDir, DateTime Function()? now, Duration timeout = const Duration(seconds: 30)}); Future<UpdateResult> check({bool userInitiated = false}); UpdateResult? get last; bool get due; }` — `due` vrai si aucune vérification ou dernière > 24 h ; `userInitiated` ignore la contrainte Wi-Fi mais jamais les vérifications ; l'URL du fichier = `Uri.parse(manifestUrl).resolve(manifest.file)`.

- [ ] **Step 1: Failing tests** (`MockClient` de `package:http/testing.dart`, fichier de test re-étiqueté `2026-09` par copie + `UPDATE meta` sur une copie inscriptible) :
  `url vide → disabled` ; `réseau facturé → waitingForWifi` ; `même version → upToDate` ; `version plus ancienne → upToDate, aucun téléchargement` ; `version plus récente → updated, store.meta.version == '2026-09'` ; puis Review Focus 4 : JSON cassé, champ manquant, HTTP 404 sur le manifeste, HTTP 500 sur le fichier, SHA faux, taille fausse, fichier tronqué, `meta.version` ≠ manifeste, délai dépassé → `failed`, `store.meta.version` inchangé, aucun fichier temporaire restant.
- [ ] **Step 2–4:** FAIL → implémenter → PASS
- [ ] **Step 5:** Commit `feat(app): verified nomenclature updates`

---

### Task 8: Thème, chaînes et coquille de l'app

**Files:**
- Create: `app/lib/ui/theme.dart`, `app/lib/l10n/app_fr.arb`, `app/l10n.yaml`, `app/lib/data/settings.dart`, `app/test/ui/theme_test.dart`
- Modify: `app/lib/app.dart`, `app/lib/main.dart`, `app/pubspec.yaml` (`generate: true`, assets)

**Interfaces:**
- Produces:
  - `class StatusColors extends ThemeExtension<StatusColors> { Color warning, onWarning, warningContainer, onWarningContainer; }` dérivée par harmonisation (`MaterialDynamicColors`/`Color.harmonizeWith` de `dynamic_color`) d'un ambre de base.
  - `ThemeData buildTheme(ColorScheme scheme)` ; `ColorScheme fallbackScheme(Brightness b)` = `ColorScheme.fromSeed(seedColor: Color(0xFF2E5D7A), brightness: b)`.
  - `class Settings { static Future<Settings> load(); String get manifestUrl; Future<void> setManifestUrl(String); }` — défaut `const String.fromEnvironment('SYNAPSE_MANIFEST_URL')`.
  - `SynapseApp({required NomenclatureStore store, required UpdateService updates, required Settings settings})` : `DynamicColorBuilder`, `localizationsDelegates`, `supportedLocales: [Locale('fr')]`, `home: SearchScreen`.
  - `main()` : `WidgetsFlutterBinding`, store `init` (écran de préparation pendant la copie), service, vérification au lancement si `due`, minuterie 24 h.
  - Chaînes (clés ARB) : `appTitle`, `searchHint`, `searchEmptyHelp`, `noResults`, `nomenclatureVersion`, `statusRetire`, `statusNonRenouvele`, `listeI`, `listeII`, `stupefiant`, `sameDosage`, `otherDosages`, `activeEquivalents`, `noActiveEquivalent`, `sourceFooter`, `about`, `checkNow`, `updateDone`, `updateFailed`, `updateDisabled`, `waitingForWifi`, `upToDate`, `manifestUrl`, `disclaimer`, `productGone`, et les libellés de champs de la fiche.

- [ ] **Step 1: Failing tests** : les deux schémas de repli ont un contraste texte/fond ≥ 4,5 (`onSurface`/`surface`, `onErrorContainer`/`errorContainer`, `onWarningContainer`/`warningContainer`) ; `StatusColors` présent en clair et sombre ; `Settings` sans valeur enregistrée → URL de build ; après `setManifestUrl` → nouvelle valeur.
- [ ] **Step 2–4:** FAIL → implémenter → PASS
- [ ] **Step 5:** Commit `feat(app): material 3 theme, strings and app shell`

---

### Task 9: Écran de recherche

**Files:**
- Create: `app/lib/ui/widgets/status_chip.dart`, `app/lib/ui/widgets/product_tile.dart`, `app/lib/ui/search/search_screen.dart`, `app/test/ui/search_screen_test.dart`, `app/test/fonts/` (Roboto copiée depuis le cache Flutter), `app/test/flutter_test_config.dart` (chargement des polices)

**Interfaces:**
- Consumes: `search`, `NomenclatureStore`, `StatusColors`, chaînes ARB
- Produces:
  - `StatusChip(ProductStatus)` — rien pour `enVigueur` ; `Retiré` (errorContainer) ; `Non renouvelé` (warningContainer) ; sémantique lisible par TalkBack.
  - `ProductTile(Product, {VoidCallback? onTap})` — `ListTile` : titre marque (1 ligne, ellipse), sous-titre `dosage · forme · conditionnement` (2 lignes max, ellipse, chiffres tabulaires), `trailing` : `StatusChip` ou libellé de liste ; hauteur ≥ 48 dp.
  - `SearchScreen` — `SearchBar` M3 en haut avec focus initial, sous-titre de version, résultats `ListView`, délai 120 ms, états vide / aucun résultat / préparation ; menu → `AboutScreen` ; tap → `ProductScreen`.

- [ ] **Step 1: Failing tests** : saisie « cetiri » → première ligne CETIRIPEX ; produit retiré affiche « Retiré » ; « zzzz » → message aucun résultat contenant la version ; champ vide → aide ; tap → fiche poussée ; Review Focus 1 : `textScaler: TextScaler.linear(2.0)` → aucune exception d'overflow ; Review Focus 2 : conditionnement de 200 caractères → sous-titre sur 2 lignes maximum.
- [ ] **Step 2:** Goldens `search_light.png`, `search_dark.png`, `search_font130.png` (390×844 dp, résultats « cetirizine »).
- [ ] **Step 3–4:** FAIL → implémenter → PASS (`flutter test --update-goldens` une fois, images relues à l'œil, puis `flutter test`).
- [ ] **Step 5:** Commit `feat(app): search screen`

---

### Task 10: Fiche produit

**Files:**
- Create: `app/lib/ui/product/product_screen.dart`, `app/test/ui/product_screen_test.dart`

**Interfaces:**
- Consumes: `NomenclatureStore`, `equivalentsOf`, `ProductTile`, `StatusChip`
- Produces: `ProductScreen({required String productId})` — relit le produit dans `store.db` à chaque notification du store ; produit absent → message `productGone` avec la version courante (Review Focus 3) ; ordre : en-tête (marque, dosage, forme) → bandeau de statut (date + motif + type de retrait) si non en vigueur → « Équivalents en vigueur — même dosage » (ou `noActiveEquivalent`) si non en vigueur → informations (paires libellé/valeur ; valeurs absentes omises) → « Même dosage » → « Autres dosages » (sous-titres par dosage) → pied `sourceFooter`.

- [ ] **Step 1: Failing tests** : produit en vigueur → pas de bandeau, sections d'équivalents conformes à `equivalents_cases.json` ; produit retiré → bandeau avec date formatée `31/03/2024` et motif, puis équivalents en vigueur avant les informations ; origine « Fabriqué localement » / « Importé » ; texte ×2,0 sans overflow ; conditionnement de 200 caractères affiché en entier ; `store.install` d'une version sans ce produit pendant que la fiche est ouverte → message `productGone`, sans exception.
- [ ] **Step 2:** Goldens `product_active_light.png`, `product_retired_light.png`, `product_retired_dark.png`.
- [ ] **Step 3–4:** FAIL → implémenter → PASS
- [ ] **Step 5:** Commit `feat(app): product sheet with equivalents`

---

### Task 11: À propos, réglage d'URL et notifications de mise à jour

**Files:**
- Create: `app/lib/ui/about/about_screen.dart`, `app/test/ui/about_screen_test.dart`
- Modify: `app/lib/app.dart` (snackbar après `updated`), `app/lib/main.dart`

**Interfaces:**
- Consumes: `UpdateService`, `Settings`, `NomenclatureStore`
- Produces: `AboutScreen` — version, date de référence, nombre de produits, date de publication, dernière vérification + résultat (chaîne selon `UpdateOutcome`), bouton « Vérifier maintenant » (`check(userInitiated: true)`, indicateur pendant l'appel), champ URL (validation `https://`, enregistrement), mention `disclaimer`.

- [ ] **Step 1: Failing tests** : URL vide → texte `updateDisabled` ; « Vérifier maintenant » avec un faux service renvoyant `updated` → snackbar « Nomenclature mise à jour : … » et version affichée changée ; `failed` → message d'erreur affiché, version inchangée ; URL `http://…` refusée, `https://…` enregistrée.
- [ ] **Step 2–4:** FAIL → implémenter → PASS
- [ ] **Step 5:** Commit `feat(app): about screen and update notifications`

---

### Task 12: Données embarquées, Android et APK

**Files:**
- Create: `scripts/sync-nomenclature.sh`, `app/README.md`
- Modify: `app/android/app/build.gradle(.kts)` (applicationId `dz.synapse.app`, `minSdk 23`), `app/android/app/src/main/AndroidManifest.xml` (libellé « Synapse », permission `INTERNET`, `ACCESS_NETWORK_STATE`, `enableOnBackInvokedCallback="true"`), `app/pubspec.yaml` (assets)

**Interfaces:**
- Produces: `scripts/sync-nomenclature.sh [publications_dir]` copie `manifest.json` et le fichier qu'il nomme vers `app/assets/nomenclature/` (`nomenclature.sqlite` + `manifest.json`), vérifie le SHA-256 ; échoue si aucun manifeste.

- [ ] **Step 1:** Publier la nomenclature 2026-08 réelle avec `synapse-admin` (fichiers réels, décisions de test) si absente, puis `bash scripts/sync-nomenclature.sh` → Expected : SHA vérifié, fichiers copiés.
- [ ] **Step 2:** Test d'intégration hôte `test/embedded_asset_test.dart` : l'asset réel s'ouvre, `search('doliprane')` renvoie un résultat en < 300 ms.
- [ ] **Step 3:** `flutter build apk --debug --dart-define=SYNAPSE_MANIFEST_URL=` → Expected : `build/app/outputs/flutter-apk/app-debug.apk` produit ; noter sa taille.
- [ ] **Step 4:** README (installation, régénération des fixtures, synchronisation, build, URL du manifeste).
- [ ] **Step 5:** Commit `build(app): embedded nomenclature and android config`

---

### Task 13: Finition Impeccable

**Files:**
- Create: `DESIGN.md` (racine), `app/test/goldens/*` mis à jour
- Modify: écrans selon les constats

**Interfaces:**
- Consumes: brief `.impeccable/surfaces/app-lib-main-dart.md`, goldens

- [ ] **Step 1:** Lire `reference/craft-floor.md` et `reference/audit.native.md` d'Impeccable ; auditer les goldens (clair, sombre, ×1,3) et le code contre Material 3 / Android (cibles, insets edge-to-edge, Retour, contraste, sémantique TalkBack).
- [ ] **Step 2:** Corriger chaque constat par un test qui échoue d'abord (widget ou golden), puis `flutter test` vert.
- [ ] **Step 3:** Rédiger `DESIGN.md` à partir du résultat construit (procédure de documentation d'Impeccable : couleurs, type, composants, états), en citant les goldens comme preuves.
- [ ] **Step 4:** `flutter analyze` et `flutter test` → tout vert.
- [ ] **Step 5:** Commit `docs(app): impeccable finish review and DESIGN.md`
