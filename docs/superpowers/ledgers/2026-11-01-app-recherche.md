# SDD ledger — plan: docs/superpowers/plans/2026-11-01-app-recherche.md
Spec: docs/superpowers/specs/2026-11-01-app-recherche-design.md
BASE: 5913390
Pre-flight: T4/T5/T6/T7/T9-11 share Product/NomenclatureDb/NomenclatureStore as declared in T3/T6 — consistent. T9 tests need T8 strings — order OK.
Task 1: complete (commit ab19745, tests: flutter test → 1 passed; flutter analyze clean)
Task 1: Ruling: dl.google.com blocked by env network policy (403) → no Android SDK; setup script installs it when reachable; flutter test unaffected; APK build (T12 step 3) deferred to an environment that allows dl.google.com — cost: no APK from this session
Task 1: Ruling: sqlite3 3.x bundles SQLite 3.54.1 via build hooks (FTS5+trigram verified on host); sqlite3_flutter_libs is 'eol' → removed — none
Task 1: Ruling: smoke test targets SynapseShellPreview (replaced in T8) — none
Task 2: complete (commit 6e6143d, tests: backend pytest test_app_fixtures → 2 passed; 40 products, 69 search cases, 40 equivalents cases)
Task 2: Ruling: other_dosages serialized as an ordered list [{dosage, ids}] (sorted by dosage key) instead of a dict — preserves order across JSON — none
Task 2: Ruling: equivalents_cases also carries 'statut' and 'active_same_dosage' — used by T5/T10 tests — none
Task 2: Ruling: published_at forced to a fixed value → reproducible fixture — none
Task 3: complete (commit 7702641, tests: flutter test test/data/nomenclature_db_test.dart → 7 passed; analyze clean)
Task 3: Ruling: open() also requires produit_fts and marque_trgm tables (search needs them) — none
Task 3: complete (commit 0c68985, tests: flutter test test/data → 7 passed; analyze clean)
Task 3: Ruling: open() also requires produit_fts and marque_trgm tables (search needs them) — none
Task 4: complete (commit 8cce8fe, tests: flutter test test/data → 13 passed; parity 69/69 cases; perf <300 ms on 9 500 rows)
Task 4: Ruling: stripAccents uses an explicit Latin accent table (Dart has no NFKD) — parity verified on fixtures incl. É — cost if wrong: a rare non-Latin-1 accent differs from backend
Task 4: Ruling: fuzzy sort made explicitly stable (bm25 index tiebreak) to mirror Python's stable sort — none
Task 5: complete (commit 750dcf7, tests: flutter test test/data → 17 passed; parity 40/40)
Task 5: Ruling: otherDosages is an ordered List<DosageGroup(dosage, products)> instead of Map — order is explicit, matches T2 JSON — none
Task 6: complete (commit c26b1dd, tests: flutter test test/data → 23 passed)
Task 6: Ruling: init compares versions via embedded assets/nomenclature/manifest.json (no copy needed to read it); a corrupt installed file is replaced from the APK — none
Task 6: Ruling: install validates the file before renaming over the current one — guarantees old DB survives a bad file — none
Task 7: complete (commit 53ff243, tests: flutter test test/data → 38 passed; 10 failure modes covered)
Task 7: Ruling: download goes to store.dir (same filesystem as installed DB → atomic rename) instead of a separate tmpDir param — none
Task 7: Ruling: manifest 'file' must be a bare *.sqlite name (no '/' or '..'); version must be AAAA-MM; sha256 64 hex — rejects path tricks — none
Task 7: Ruling: 'due' counts only checks that reached the server (disabled/waitingForWifi retried next time) — none
Task 7: Ruling: whole file read in memory (≈3.6 MB) via client.get — simpler than streaming — cost: memory spike ≈4 MB
Task 8: complete (commit 00cb39d, tests: flutter test → 44 passed; analyze clean)
Task 8: Ruling: Flutter 3.47 ships two ColorScheme types (framework vs package material_ui used by dynamic_color 2.1) → DynamicColorBuilder unusable; dynamic colour kept by reading DynamicColorPlugin.getCorePalette() in main and seeding ColorScheme.fromSeed with primary tone 40; warning harmonized with Blend.harmonize — cost if wrong: scheme close to but not identical to the system's Material You scheme
Task 8: Ruling: Services InheritedWidget carries store/updates/settings to screens; HomeScreen placeholder until T9 — none
Task 8: Ruling: embedded asset temporarily = test fixture + manifest {version 2026-08}; replaced by real publication in T12 — none
Task 8: Ruling: Settings stores '' explicitly to disable updates even when a build URL exists; only https accepted — none
Task 9: complete (commit 0004786, tests: flutter test → all pass; goldens search_light/dark/font130 reviewed by eye)
Task 9: Ruling: androidTapTargetGuideline replaced by explicit ≥48 dp checks on SearchBar/IconButton/menu/ProductTile — the guideline measures the 24 dp text field inside SearchBar (whole 56 dp bar is the target) — cost if wrong: a small target elsewhere would be missed (only listed widget types checked)
Task 9: Ruling: SearchBar elevation 0 on surfaceContainerHigh (Google apps style); default 6 dp rendered as a hard black ring in goldens — none
Task 9: Ruling: status warning container uses tonalSpot (light container like errorContainer) instead of fidelity (dark, saturated) — found on golden review; test added and seen failing on old value
Task 9: Ruling: U+2060 after '/' so 'B/10', '5MG/ML' never break across lines — none
Task 9: Ruling: tests run with FocusHighlightStrategy.alwaysTouch (phone) — none
Task 9: Note: theme fix written before its test (TDD slip) — test then verified RED on old value, GREEN on new
Task 10: complete (commit d8ae1c7, tests: flutter test → all pass; goldens product_active_light / retired_light / retired_dark reviewed)
Task 10: Ruling: sheet is a SingleChildScrollView+Column (bounded content: one DCI code's products) instead of a lazy ListView — every section built, simpler tests — cost if wrong: slower build for a DCI code with hundreds of products (none seen)
Task 10: Ruling: for a non-active product, same-dosage active equivalents shown on top are not repeated in 'Même dosage' — none
Task 11: complete (commit edcdbca, tests: flutter test → 74 passed)
Task 11: Ruling: background check runs every hour and acts only when 'due' (24 h since last server contact) — so a check missed for lack of Wi-Fi retries within the hour — none
Task 11: Ruling: manual check also shows its result in a snackbar (any outcome); automatic check notifies only 'updated' — none
Task 12: complete except APK (commit d9c8463, tests: embedded_asset_test → 2 passed; flutter build apk → 'No Android SDK found' (dl.google.com blocked))
Task 12: Ruling: 4 double_feuille decisions made provisionally by Claude to publish the embedded file (SETREME, IMUZOLE, LATENDRA → en vigueur; ABILIFY MAINTENA → retiré, cautious) — marked 'claude (provisoire)' in decisions/2026-08.yaml — cost if wrong: one product shown with the wrong status until the admin re-decides
Task 12: Ruling: namespace kept dz.synapse.synapse (Kotlin package); only applicationId set to dz.synapse.app; minSdk = Flutter default — none
Task 13: in progress — finish review (Impeccable, fresh subagent, degraded instructions): disposition fix; code review (fresh subagent): With fixes (0 Critical, 5 Important, 8 Minor)
Final: Ruling: code-review minor #8 (clear during debounce shows stale results) re-graded Important — misleading at the counter, cheap fix
Final: Ruling: finish-review fix #2 (remove manifest URL field from About) declined — the field is in the user-approved spec (pilot) — cost: an admin setting visible to pharmacists
Final: Ruling: finish-review fix #6 (DynamicColorBuilder) not applicable — type conflict in Flutter 3.47; theme being redone from the user's El Hana reference
Final: fixed code #1 update with unreadable row — update_service_test 'statut inconnu' + 'date illisible' RED→GREEN, suite 96/96
Final: fixed code #2 empty dosage as same dosage — backend test_unknown_dosage_never_same_dosage (RED on old script) + equivalents parity/'dosage non précisé' RED→GREEN
Final: fixed code #3 total download deadline — 'connexion lente mais continue' RED→GREEN; 'connexion bloquée' guards regression
Final: fixed code #4 concurrent checks — 'deux vérifications simultanées' RED→GREEN
Final: fixed code #5 startup failure — store 'copie de l'APK impossible' + startup_test RED→GREEN
Final: fixed code #8 stale results after clear — 'pas de résultats fantômes' RED→GREEN
Final: fixed finish #1 seed ref, #3 status column, #4 explicit status on sheet, #5 medium app bar, #7 no-results copy, #8 captures — widget tests RED→GREEN, goldens reviewed
Final: minor (deferred): accent table vs NFKD (ﬁ, fullwidth, ß, ², ½, Ł…) and ASCII \b — fewer results, never wrong ones
Final: minor (deferred): SQL tie order not fixed by rowid (both sides)
Final: minor (deferred): brand titles 1 line (near-identical long names at ×2)
Final: minor (deferred): build-time manifest URL / redirects not forced to https
Final: minor (deferred): no quick_check of the installed DB at startup
Final: minor (deferred): Android cmdline-tools zip not SHA-checked in setup script
Final: pending: Impeccable verdict pass + DESIGN.md postponed until the El Hana-based theme is settled (user request)
Theme: El Hana-inspired theme committed (2003499), 101 tests pass
Theme: Ruling: card shadow replaced by a 1 px light border (elevation 0) — the test renderer draws elevation as a hard black ring, so captures would misrepresent the device — cost: flatter than El Hana's soft shadow
Theme: Ruling: textContrastGuideline (pixel sampling) dropped — it measured Nunito anti-aliasing in the search field (1.84) while token contrast is ~14:1; replaced by explicit token-pair contrast checks — cost: a hard-coded text colour bypassing tokens would not be caught
Theme: Ruling: orange accent from El Hana not used — reserved for 'non renouvelé' status — none
Theme finish review #2: disposition fix (5 material fixes) — all applied (e633a76): soft shadow restored (capture helper now marks every render object for repaint with shadows enabled — the hard ring was a stale paint, not the renderer), titleLarge onSurface section headings, dividers in sheet lists, outlineVariant/divider #E3E8EF, brand w700; tests RED→GREEN, 105 pass
Theme: Ruling (superseded): the earlier '1 px border instead of shadow' ruling is withdrawn
Final: fixed deferred minor #12 quick_check — store 'même version mais abîmée' RED→GREEN
Final: fixed deferred minor #11 build URL https — theme_test validBuildUrl RED→GREEN
Final: fixed deferred minor #7 rowid tiebreak (both sides) — no reproducible RED (depends on SQLite version); parity 69/69 re-verified on regenerated fixtures
Final: Impeccable verdict pass on 5 fixes: ship (scope: the five fixes only)
Follow-up: fixed 'produit absent' state (icon + title like other empty states) — product_screen test RED→GREEN
Follow-up: Nunito 500 instance bundled (Material 500 roles no longer fall back) — theme_test RED→GREEN
Follow-up: brand titles on 2 lines in result rows (near-identical long names) — search test RED→GREEN
Follow-up: rare characters — accent table generated from Python NFKD (backend/scripts/make_accent_table.py → app/lib/data/accents.g.dart, 1153 entries), ß→SS, Unicode-aware elision boundary; 11 new parity cases (80 total) RED→GREEN
Follow-up: setup script verifies Android cmdline-tools zip against the SHA-1 in Google's repository index (selection logic checked on a sample index; real index blocked here)
