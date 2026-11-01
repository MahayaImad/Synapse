# Import de la nomenclature — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Outil CLI `synapse-admin` qui importe le fichier Excel mensuel de la nomenclature, le compare à la version publiée, fait trancher les cas douteux par fichier de décisions, publie un SQLite FTS5 pour l'app et permet d'y chercher.

**Architecture:** Un noyau pur (lecture Excel → normalisation → consolidation → rapprochement) sans base de données, entièrement testable sur des classeurs construits en mémoire. Une couche PostgreSQL (SQLAlchemy Core + Alembic) stocke versions, produits, écarts, décisions et anomalies. La CLI Typer orchestre ; la publication produit un SQLite autonome + `manifest.json`.

**Tech Stack:** Python 3.12+, uv, Typer, openpyxl, PyYAML, rapidfuzz, SQLAlchemy 2 Core, psycopg 3, Alembic, PostgreSQL 16 (pg_trgm, unaccent), SQLite FTS5, pytest.

**Spec:** `docs/superpowers/specs/2026-11-01-nomenclature-import-design.md`

## Global Constraints

- Lecture des colonnes **par nom normalisé**, jamais par position ; colonne obligatoire absente → import refusé.
- Aucune correction silencieuse : toute valeur non reconnue devient une `Anomaly` listée dans le rapport ; la ligne brute est toujours conservée.
- Changement de **marque, dosage ou forme** à numéro/racine égale → toujours à trancher, jamais automatique.
- Import strictement chronologique ; premier import = tout « nouveau », aucune décision.
- `publish` refuse s'il reste un cas sans choix valide.
- Statuts publiés : `en_vigueur`, `non_renouvele`, `retire` ; classement de recherche dans cet ordre.
- `STATUT` : `F` → `fabrique_localement`, `I` → `importe`.
- `search` < 300 ms par requête sur le fichier complet.
- Fichiers Excel sources hors git (empreinte SHA-256 en base). Décisions YAML versionnées dans git.
- Tables PostgreSQL : `nomenclature_version`, `produit`, `produit_version`, `ecart`, `decision`, `anomalie`.
- Aucun LLM.

## Review Focus

1. **N° en texte ou cellules numériques** (fichiers 2024 : `N°` = `'1'`, en-tête `N` ; dosage saisi comme nombre `0.01`) → lignes lues, dosage rendu sans artefact flottant (`0,01`). Test : Task 3.
2. **Import interrompu ou relancé** pour la même version → transaction unique ; relance refusée sauf `--remplacer` qui supprime le brouillon. Test : Task 7.
3. **Fichier de décisions mal rempli** (id inconnu, choix invalide, référence hors candidats, cas manquant) → `publish` refuse en listant chaque problème, rien n'est écrit. Test : Task 8.
4. **Requête de recherche avec caractères spéciaux** (`"`, `*`, `-`, `L'ALCOOL`, `é`, chaîne vide) → pas d'exception, résultats sensés. Test : Task 10.
5. **Version au mauvais mois** (`--version 2026-07` sur un fichier « AU 31 AOUT 2026 ») → refus explicite. Test : Task 7.

---

## Structure des fichiers

```
backend/
  pyproject.toml            # paquet synapse-admin, script `synapse-admin`
  docker-compose.yml        # postgres:16
  alembic.ini
  migrations/               # env.py + versions/0001_initial.py
  src/synapse_admin/
    model.py                # dataclasses partagées
    regnum.py               # numéro d'enregistrement
    normalize.py            # RawRow -> Product
    columns.py              # alias d'en-têtes, détection de l'en-tête
    excel_reader.py         # classeur -> WorkbookData
    consolidate.py          # doublons, produit dans deux feuilles
    matching.py             # rapprochement par paliers
    db.py                   # tables SQLAlchemy Core, engine
    repository.py           # lecture/écriture versions
    decisions.py            # rapport Markdown + YAML de décisions
    publish.py              # application des décisions, export SQLite
    search.py               # recherche FTS5
    cli.py                  # Typer
  tests/
    builders.py             # fabrique de classeurs openpyxl en mémoire
    conftest.py             # base de test PostgreSQL
    test_*.py
nomenclature/               # répertoire de travail par défaut de la CLI
  decisions/                # versionné
  reports/                  # versionné
  publications/             # .sqlite + manifest.json, ignoré par git
```

---

### Task 1: Squelette du paquet et numéro d'enregistrement

**Files:**
- Create: `backend/pyproject.toml`, `backend/src/synapse_admin/__init__.py`, `backend/src/synapse_admin/regnum.py`, `backend/tests/test_regnum.py`, `backend/README.md`
- Modify: `.gitignore` (ajouter `nomenclature/publications/`, `backend/.venv/`)

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) RegistrationNumber(raw: str, lab: str, dci_code: str, family: str, subfamily: str, molecule_num: str, initial_year: str, renewal_year: str | None)` avec propriété `stem -> tuple[str, str, str]` = `(lab, dci_code, initial_year)`.
  - `parse_registration(raw: str) -> RegistrationNumber | None`
  - `normalize_dci_code(raw: str) -> str` (`"01  A 003"` → `"01 A 003"`).

- [ ] **Step 1: Write the failing tests**

```python
def test_parse_renewed():
    r = parse_registration("352/01 A 003/06/22")
    assert (r.lab, r.dci_code, r.family, r.subfamily, r.molecule_num) == ("352", "01 A 003", "01", "A", "003")
    assert (r.initial_year, r.renewal_year) == ("06", "22")
    assert r.stem == ("352", "01 A 003", "06")

def test_parse_not_renewed_and_renewal_keeps_stem():
    a = parse_registration("077/01 A 003/17"); b = parse_registration("077/01 A 003/17/24")
    assert a.renewal_year is None and a.stem == b.stem

def test_parse_tolerates_spaces():
    assert parse_registration(" 003 / 20 B 030 /97/09 ").stem == ("003", "20 B 030", "97")

@pytest.mark.parametrize("bad", ["001/09 H 178 20", "528/04 B 035/  ", "003/09/21 F 056/20", " nv/02 A 055/05/23", ""])
def test_unparseable_returns_none(bad):
    assert parse_registration(bad) is None
```

- [ ] **Step 2:** `cd backend && uv run pytest tests/test_regnum.py -v` → FAIL (module absent)
- [ ] **Step 3:** Créer `pyproject.toml` (dépendances de la stack ci-dessus, `[project.scripts] synapse-admin = "synapse_admin.cli:app"`, `src` layout) ; implémenter `regnum.py` par une regex `^\s*(\d{3})\s*/\s*(\d{2})\s*([A-Z])\s*(\d{3})\s*/\s*(\d{2})(?:\s*/\s*(\d{2}))?\s*$`.
- [ ] **Step 4:** `uv run pytest tests/test_regnum.py -v` → PASS
- [ ] **Step 5:** Commit `feat(admin): package skeleton and registration number parser`

---

### Task 2: Normalisation d'une ligne

**Files:**
- Create: `backend/src/synapse_admin/model.py`, `backend/src/synapse_admin/normalize.py`, `backend/tests/test_normalize.py`

**Interfaces:**
- Consumes: `parse_registration`, `normalize_dci_code` (Task 1)
- Produces (dans `model.py`):
  - `SheetKind = Literal["en_vigueur", "non_renouvele", "retire"]`
  - `@dataclass RawRow(sheet: SheetKind, sheet_title: str, row_number: int, values: dict[str, object], raw: dict[str, object])` — `values` indexé par champ canonique (voir Task 3), `raw` = en-tête d'origine → valeur JSON-sérialisable.
  - `@dataclass Anomaly(sheet: SheetKind, row_number: int, field: str, value: str, message: str)`
  - `@dataclass Product(sheet: SheetKind, row_number: int, reg_raw: str, registration: RegistrationNumber | None, dci_code: str, dci: str, brand: str, form: str, dosage: str, packaging: str, liste: Literal["I","II","STUPEFIANT"] | None, hospital: bool, pharmacy: bool, type: Literal["GE","RE","BIO"] | None, origin: Literal["fabrique_localement","importe"] | None, lab: str, country: str, initial_date: date | None, final_date: date | None, stability: str, obs: str, withdrawal_date: date | None, withdrawal_reason: str, raw: dict[str, object])` avec propriétés `presentation_key -> tuple[str, str, str]` = (marque, dosage, conditionnement) et `stem -> tuple | None`.
  - `CLINICAL_FIELDS = ("brand", "dosage", "form")`
- Produces (dans `normalize.py`): `normalize_text(v: object) -> str`, `normalize_row(row: RawRow) -> tuple[Product, list[Anomaly]]`

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize("v,exp", [("LISTE I", "I"), ("Liste I ", "I"), ("lISTE I", "I"), ("LISTE II", "II"),
                                   ("STUPEFIANT", "STUPEFIANT"), ("Stupéfiants", "STUPEFIANT"), ("", None), (" ", None), (None, None)])
def test_liste(v, exp): assert normalize_row(raw(liste=v))[0].liste == exp

@pytest.mark.parametrize("p1,p2,hop,off", [("HOP", "OFF", True, True), ("HOP*", "0FF", True, True), ("*HOP", None, True, False),
                                           ("HOP.", "OFF?", True, True), (None, "           ", False, False)])
def test_hop_off(p1, p2, hop, off):
    p = normalize_row(raw(p1=p1, p2=p2))[0]; assert (p.hospital, p.pharmacy) == (hop, off)

@pytest.mark.parametrize("v,exp", [("F", "fabrique_localement"), ("I ", "importe"), ("i", "importe")])
def test_origin(v, exp): assert normalize_row(raw(statut=v))[0].origin == exp

def test_unknown_values_become_anomalies_not_guesses():
    p, an = normalize_row(raw(liste="LISTE III", statut="X", p2="MEDICAMENT SOUMIS A PRESCRIPTION RESTREINTE"))
    assert p.liste is None and p.origin is None
    assert {a.field for a in an} == {"liste", "statut", "p2"}

def test_text_collapsed_and_raw_kept():
    p, _ = normalize_row(raw(marque="VITAMINE C  BGL ", dosage=0.01))
    assert p.brand == "VITAMINE C BGL" and p.dosage == "0,01"
    assert p.raw["NOM DE MARQUE"] == "VITAMINE C  BGL "

def test_unparseable_registration_is_anomaly_but_row_kept():
    p, an = normalize_row(raw(n_enregistrement="001/09 H 178 20", code="09 H 178"))
    assert p.registration is None and p.dci_code == "09 H 178"
    assert any(a.field == "n_enregistrement" for a in an)
```

(`raw(**overrides)` : helper local qui construit un `RawRow` CETIRIPEX valide — `035/01 A 003/17/23`, `01 A 003`, `CETIRIZINE DICHLORHYDRATE`, `COMPRIME PELLICULE SECABLE`, `10MG`, `B/15`, `LISTE II`, `HOP`, `OFF`, `PHARMALLIANCE`, `ALGERIE`, `GE`, `F`.)

- [ ] **Step 2:** `uv run pytest tests/test_normalize.py -v` → FAIL
- [ ] **Step 3:** Implémenter. Textes : `str`, trim, espaces multiples → un, majuscules. Nombre non entier → `str` avec virgule décimale ; entier → sans décimales. Dates : `datetime`/`date` → `date` ; texte non vide non convertible → anomalie. `dci_code` pris de la colonne CODE normalisée, à défaut du numéro décomposé.
- [ ] **Step 4:** → PASS
- [ ] **Step 5:** Commit `feat(admin): row normalization with anomalies`

---

### Task 3: Lecture du classeur

**Files:**
- Create: `backend/src/synapse_admin/columns.py`, `backend/src/synapse_admin/excel_reader.py`, `backend/tests/builders.py`, `backend/tests/test_excel_reader.py`

**Interfaces:**
- Consumes: `RawRow`, `SheetKind` (Task 2)
- Produces:
  - `CANONICAL_FIELDS` : `n_enregistrement, code, dci, marque, forme, dosage, conditionnement, liste, p1, p2, obs, labo, pays, date_enregistrement_initial, date_enregistrement_final, type, statut, duree_stabilite, date_retrait, motif_retrait`
  - `REQUIRED_FIELDS = {"n_enregistrement", "code", "dci", "marque", "forme", "dosage", "conditionnement"}`
  - `class WorkbookFormatError(Exception)`
  - `@dataclass WorkbookData(rows: list[RawRow], reference_date: date | None, sheet_counts: dict[SheetKind, int], declared_counts: dict[SheetKind, int | None])`
  - `read_workbook(path: Path) -> WorkbookData`
  - `tests/builders.py` : `build_workbook(path: Path, sheets: list[SheetSpec]) -> Path`, `SheetSpec(title: str, header: list[str], rows: list[list], title_line: str, header_row: int, first_header_cell: str = "N°")`, plus les en-têtes réels `HEADER_2026_ACTIF`, `HEADER_2026_RETRAITS`, `HEADER_2024_ACTIF` (copiés des fichiers réels, dont « N » et « COND »).

- [ ] **Step 1: Write the failing tests**

```python
def test_reads_three_sheets_by_title(tmp_path):
    wb = read_workbook(build_2026(tmp_path))          # titres "Nomenclature Aout 2026", "Non Renouvelés ", "Retraits"
    assert wb.sheet_counts == {"en_vigueur": 3, "non_renouvele": 1, "retire": 2}
    assert wb.reference_date == date(2026, 8, 31)     # depuis "… AU 31 AOUT 2026 ( 5425 DE )"
    assert wb.declared_counts["en_vigueur"] == 5425

def test_2024_header_variants(tmp_path):            # première cellule "N", "COND", N° en texte '1', titre de feuille " Nomenclature AOUT 2024"
    rows = read_workbook(build_2024(tmp_path)).rows
    assert rows[0].values["conditionnement"] == "B/15" and rows[0].row_number > 16

def test_retraits_columns_by_name_not_position(tmp_path):
    r = [x for x in read_workbook(build_2026(tmp_path)).rows if x.sheet == "retire"][0]
    assert r.values["motif_retrait"] == "RETRAIT PAR LE DETENTEUR POUR MOTIF COMMERCIAL"
    assert "obs" not in r.values

def test_missing_required_column_refused(tmp_path):
    with pytest.raises(WorkbookFormatError, match="DOSAGE"):
        read_workbook(build_2026(tmp_path, drop_column="DOSAGE"))

def test_non_numbered_rows_ignored(tmp_path):        # lignes vides, titres, pied de page
    assert all(str(r.raw["N°"]).strip().isdigit() for r in read_workbook(build_2026(tmp_path)).rows)
```

- [ ] **Step 2:** → FAIL
- [ ] **Step 3:** `openpyxl.load_workbook(read_only=True, data_only=True)`. Feuille : titre normalisé (`strip`, minuscules, sans accents) commençant par `nomenclature` / `non renouv` / `retrait` ; autre feuille ignorée. En-tête : première ligne dont la 1re cellule normalisée vaut `N°` ou `N`. Alias : normaliser l'en-tête (sans accents, majuscules, espaces réduits) puis table `{"N°ENREGISTREMENT": "n_enregistrement", "CODE": "code", "DENOMINATION COMMUNE INTERNATIONALE": "dci", "NOM DE MARQUE": "marque", "FORME": "forme", "DOSAGE": "dosage", "CONDITIONNEMENT": "conditionnement", "COND": "conditionnement", "LISTE": "liste", "P1": "p1", "P2": "p2", "OBS": "obs", "LABORATOIRES DETENTEUR DE LA DECISION D'ENREGISTREMENT": "labo", "PAYS DU LABORATOIRE DETENTEUR DE LA DECISION D'ENREGISTREMENT": "pays", "DATE D'ENREGISTREMENT INITIAL": "date_enregistrement_initial", "DATE D'ENREGISTREMENT FINAL": "date_enregistrement_final", "TYPE": "type", "STATUT": "statut", "DUREE DE STABILITE": "duree_stabilite", "DATE DE RETRAIT": "date_retrait", "MOTIF DE RETRAIT": "motif_retrait"}`. Date de référence et effectif déclaré : regex `AU (\d{1,2}) (\w+) (\d{4})` et `\(\s*(\d+)\s*DE\s*\)` sur les lignes au-dessus de l'en-tête (mois français sans accents).
- [ ] **Step 4:** → PASS
- [ ] **Step 5:** Commit `feat(admin): workbook reader with header aliases`

---

### Task 4: Consolidation d'une version

**Files:**
- Create: `backend/src/synapse_admin/consolidate.py`, `backend/tests/test_consolidate.py`
- Modify: `backend/src/synapse_admin/model.py` (ajout `Case`, `CaseKind`, `Candidate`)

**Interfaces:**
- Consumes: `Product`, `Anomaly` (Task 2)
- Produces:
  - `CaseKind = Literal["changement_titulaire", "candidats_multiples", "champ_clinique", "disparu_sans_retrait", "double_feuille"]`
  - `@dataclass Candidate(ref: str, product_id: UUID | None, product: Product)` — `ref` court et stable (`"c1"`, `"c2"`…) utilisé dans le YAML.
  - `@dataclass Case(case_id: str, kind: CaseKind, subject: Product | None, subject_product_id: UUID | None, candidates: list[Candidate])` — `case_id` déterministe : `f"{kind}:{sheet}:{row_number}"` (sujet = nouvelle ligne) ou `f"{kind}:{product_id}"` (sujet = ancien produit).
  - `consolidate(products: list[Product]) -> tuple[list[Product], list[Anomaly], list[Case]]`
  - `product_identity(p: Product) -> tuple` = `(stem or reg_raw, presentation_key)`

- [ ] **Step 1: Write the failing tests**

```python
def test_duplicate_after_normalization_merged_with_anomaly():   # "VITAMINE C BGL" ×2, même numéro 235/14 H 222/25
    kept, an, cases = consolidate([vitc(row=10), vitc(row=11)])
    assert len(kept) == 1 and an[0].message.startswith("Doublon") and cases == []

def test_shared_decision_distinct_presentations_kept():          # NOBAC fraise / menthe, même 263/10 G 054/23
    kept, _, _ = consolidate([nobac("NOBAC FRAISE"), nobac("NOBAC ADULTE GOUT MENTHE")])
    assert len(kept) == 2

def test_same_product_in_two_sheets_is_a_case():
    kept, _, cases = consolidate([cetiripex(sheet="en_vigueur"), cetiripex(sheet="retire")])
    assert [c.kind for c in cases] == ["double_feuille"] and len(cases[0].candidates) == 2
    assert kept == []                                             # retenu seulement après décision
```

- [ ] **Step 2:** → FAIL
- [ ] **Step 3:** Grouper par `product_identity`. Même feuille → garder la première, anomalie pour les suivantes. Feuilles différentes → `Case("double_feuille")` dont les candidats sont les lignes, refs `c1…`.
- [ ] **Step 4:** → PASS
- [ ] **Step 5:** Commit `feat(admin): in-version consolidation`

---

### Task 5: Rapprochement entre versions

**Files:**
- Create: `backend/src/synapse_admin/matching.py`, `backend/tests/test_matching.py`

**Interfaces:**
- Consumes: `Product`, `Case`, `Candidate`, `CLINICAL_FIELDS`, `product_identity`
- Produces:
  - `@dataclass PreviousProduct(product_id: UUID, product: Product)`
  - `GapCategory = Literal["nouveau", "disparu", "statut", "modifie", "inchange"]`
  - `@dataclass Gap(category: GapCategory, tier: int | None, product_id: UUID | None, old: Product | None, new: Product | None, changed_fields: list[str])` — un `Gap` peut porter `statut` **et** des champs modifiés : `category="statut"` prime, `changed_fields` les liste.
  - `@dataclass MatchResult(gaps: list[Gap], cases: list[Case])`
  - `match_versions(previous: list[PreviousProduct], new: list[Product]) -> MatchResult`
  - `BRAND_SIMILARITY_THRESHOLD = 85` (rapidfuzz `fuzz.ratio`, à recalibrer en Task 11)

- [ ] **Step 1: Write the failing tests**

```python
def test_first_import_everything_new():
    r = match_versions([], [cetiripex()]); assert [g.category for g in r.gaps] == ["nouveau"] and r.cases == []

def test_tier1_exact():               assert gap(prev(cetiripex()), cetiripex()).category == "inchange"
def test_tier2_renewal_same_stem():   # 077/01 A 003/17 -> 077/01 A 003/17/24
    g = gap(prev(zytrex("077/01 A 003/17")), zytrex("077/01 A 003/17/24"))
    assert (g.category, g.tier, g.changed_fields) == ("modifie", 2, ["reg_raw"])
def test_tier3_packaging_fix_is_safe():
    g = gap(prev(cetiripex(packaging="B/15")), cetiripex(packaging="B/ 15 COMPRIMES"))
    assert (g.category, g.tier, g.changed_fields) == ("modifie", 3, ["packaging"])

@pytest.mark.parametrize("field,value", [("brand", "CETIRIPEX GE"), ("dosage", "20MG"), ("form", "SIROP")])
def test_tier3_clinical_change_is_a_case(field, value):
    r = match_versions([prev(cetiripex())], [cetiripex(**{field: value})])
    assert [c.kind for c in r.cases] == ["champ_clinique"]

def test_holder_change_is_a_case():   # GOAGIL-VII 640/12 J 118/24 -> COAGIL-VII 003/12 J 118/24
    r = match_versions([prev(goagil())], [coagil()])
    assert [c.kind for c in r.cases] == ["changement_titulaire"]
    assert r.cases[0].candidates[0].product_id == PREV_ID

def test_status_change_same_product():
    g = gap(prev(cetiripex(sheet="en_vigueur")), cetiripex(sheet="retire"))
    assert g.category == "statut"

def test_disappeared_without_withdrawal_is_a_case():
    r = match_versions([prev(kinadyn())], [])
    assert [c.kind for c in r.cases] == ["disparu_sans_retrait"]

def test_conservation():               # chaque nouvelle ligne et chaque ancien produit apparaît exactement une fois
    r = match_versions(PREVS, NEWS)
    assert count_new(r) == len(NEWS) and count_old(r) == len(PREVS)
```

- [ ] **Step 3: Algorithme** (une ligne rapprochée sort du jeu à chaque palier)

```
1. index ancien par (reg_raw, presentation_key)        -> égalité: inchange (ou statut si feuille diffère)
2. index ancien par (stem, presentation_key)           -> modifie tier 2 (ou statut)
3. par stem : exactement 1 ancien et 1 nouveau restants
      champs cliniques différents -> Case champ_clinique (candidat = l'ancien)
      sinon                        -> modifie tier 3
   par stem avec >1 de chaque côté -> Case candidats_multiples pour chaque nouvelle ligne
4. nouvelles restantes : anciens restants de même dci_code et même dosage, labo différent,
   fuzz.ratio(brand) >= seuil -> Case changement_titulaire (tous ces candidats)
5. nouvelles restantes -> nouveau ; anciens restants -> disparu si l'ancien était déjà
   retire/non_renouvele, sinon Case disparu_sans_retrait
```
`changed_fields` = noms d'attributs `Product` différents hors `sheet`, `row_number`, `raw`.

- [ ] **Step 2/4:** FAIL puis PASS
- [ ] **Step 5:** Commit `feat(admin): tiered version matching`

---

### Task 6: Schéma PostgreSQL et dépôt

**Files:**
- Create: `backend/docker-compose.yml`, `backend/alembic.ini`, `backend/migrations/env.py`, `backend/migrations/versions/0001_initial.py`, `backend/src/synapse_admin/db.py`, `backend/src/synapse_admin/repository.py`, `backend/tests/conftest.py`, `backend/tests/test_repository.py`

**Interfaces:**
- Consumes: `Product`, `Anomaly`, `Gap`, `Case`, `PreviousProduct`
- Produces:
  - `db.py` : `metadata`, tables, `get_engine(url: str | None = None) -> Engine` (défaut env `DATABASE_URL`, sinon `postgresql+psycopg://synapse:synapse@localhost:5442/synapse`).
  - Tables (colonnes clés) :
    - `nomenclature_version(id serial, label text unique, reference_date date, source_filename, source_sha256, state text check in ('brouillon','publiee','remplacee'), imported_at, published_at)`
    - `produit(id uuid pk, created_at, created_in_version int)`
    - `produit_version(id serial, version_id, produit_id uuid null, sheet, row_number, …tous les champs de Product…, raw jsonb)` ; index `gin_trgm_ops` sur `brand`, `dci`.
    - `ecart(id serial, version_id, category text, tier int, produit_id uuid null, old_pv_id int null, new_pv_id int null, changed_fields text[], case_id text null, case_kind text null, candidates jsonb null)` — `category='a_trancher'` pour un cas.
    - `decision(id serial, version_id, case_id, choice text, decided_by, decided_at, recorded_at)`
    - `anomalie(id serial, version_id, sheet, row_number, field, value, message)`
  - `repository.py` :
    - `latest_published(conn) -> tuple[VersionRow, list[PreviousProduct]] | None`
    - `save_draft(conn, label, reference_date, filename, sha256, products, anomalies, match: MatchResult, consolidation_cases: list[Case]) -> int` — attribue un `uuid4` provisoire aux « nouveau », reprend l'id des produits rapprochés, `produit_id = NULL` pour les sujets de cas.
    - `load_draft(conn, label) -> Draft` (`Draft(version: VersionRow, gaps, cases, anomalies)`)
    - `delete_draft(conn, label) -> None`
  - `tests/conftest.py` : fixture `conn` sur `TEST_DATABASE_URL` (défaut `…/synapse_test`), `alembic upgrade head` une fois par session, transaction annulée après chaque test ; `pytest.skip` si la base est injoignable, avec le message de démarrage `docker compose up -d`.

- [ ] **Step 1: Failing tests** — `test_migration_creates_extensions` (`pg_trgm`, `unaccent` dans `pg_extension`) ; `test_save_and_load_draft_roundtrip` (2 nouveaux + 1 cas → `load_draft` rend les mêmes catégories et le cas avec ses candidats) ; `test_latest_published_none_when_empty`.
- [ ] **Step 2:** FAIL
- [ ] **Step 3:** Implémenter (SQLAlchemy Core, pas d'ORM). Migration écrite à la main avec `CREATE EXTENSION IF NOT EXISTS`.
- [ ] **Step 4:** `docker compose -f backend/docker-compose.yml up -d && uv run pytest tests/test_repository.py -v` → PASS
- [ ] **Step 5:** Commit `feat(admin): postgres schema and repository`

---

### Task 7: Commandes `import` et `status`

**Files:**
- Create: `backend/src/synapse_admin/cli.py`, `backend/src/synapse_admin/importer.py`, `backend/tests/test_import_cmd.py`

**Interfaces:**
- Consumes: `read_workbook`, `normalize_row`, `consolidate`, `match_versions`, repository
- Produces:
  - `run_import(conn, path: Path, label: str, replace: bool = False) -> ImportSummary` (`ImportSummary(label, rows_read, counts_by_category: dict[str, int], cases: int, anomalies: int)`), le tout dans **une** transaction.
  - `class ImportRefused(Exception)`
  - CLI : `synapse-admin import FICHIER --version YYYY-MM [--remplacer]`, `synapse-admin status`. Option globale `--workdir` (défaut `./nomenclature`).

- [ ] **Step 1: Failing tests**

```python
def test_first_import_all_new(conn, tmp_path):
    s = run_import(conn, build_2026(tmp_path), "2026-08")
    assert s.counts_by_category == {"nouveau": 6} and s.cases == 0

def test_label_must_match_reference_month(conn, tmp_path):
    with pytest.raises(ImportRefused, match="AOUT 2026"): run_import(conn, build_2026(tmp_path), "2026-07")

def test_older_than_published_refused(conn, tmp_path): ...      # publier 2026-08 puis importer 2026-06 -> ImportRefused "chronologique"
def test_rerun_needs_replace(conn, tmp_path):
    run_import(conn, f, "2026-08")
    with pytest.raises(ImportRefused, match="--remplacer"): run_import(conn, f, "2026-08")
    run_import(conn, f, "2026-08", replace=True)                  # OK, un seul brouillon
def test_failure_leaves_nothing(conn, tmp_path, monkeypatch):     # exception injectée dans save_draft -> aucune ligne en base
def test_status_lists_versions(cli_runner, conn, tmp_path): ...   # sortie contient "2026-08  brouillon"
```

- [ ] **Step 2–4:** FAIL → implémenter (SHA-256 du fichier, contrôle mois/étiquette, contrôle chronologique, `save_draft`) → PASS
- [ ] **Step 5:** Commit `feat(admin): import and status commands`

---

### Task 8: `review` — rapport et fichier de décisions

**Files:**
- Create: `backend/src/synapse_admin/decisions.py`, `backend/tests/test_decisions.py`
- Modify: `backend/src/synapse_admin/cli.py`

**Interfaces:**
- Consumes: `load_draft`
- Produces:
  - `render_report(draft: Draft) -> str` (Markdown : en-tête version/fichier/SHA, tableau des totaux par catégorie + anomalies, puis sections détaillées ; chaque cas cite son `case_id`).
  - `write_decisions_template(draft: Draft, path: Path) -> None` — ne remplace **jamais** les `choix` déjà remplis d'un fichier existant (fusion par `case_id`).
  - `load_decisions(path: Path, draft: Draft) -> list[Decision]` ; lève `DecisionsInvalid(problems: list[str])`.
  - `@dataclass Decision(case_id: str, choice: str, decided_by: str, decided_at: date)`
  - Choix valides : `meme_produit:<ref>` (ref parmi les candidats), `nouveau` (sujet = nouvelle ligne), `disparu` (sujet = ancien produit), `garder:<ref>` (`double_feuille`).
  - CLI : `synapse-admin review YYYY-MM` écrit `reports/YYYY-MM.md` et `decisions/YYYY-MM.yaml`.

Format YAML :

```yaml
version: 2026-08
cas:
  - id: "changement_titulaire:en_vigueur:812"
    type: changement_titulaire
    sujet: {n_enregistrement: "003/12 J 118/24", marque: COAGIL-VII, dosage: 4,8MG, conditionnement: "...", feuille: en_vigueur, ligne: 812}
    candidats:
      - {ref: c1, produit_id: "…", n_enregistrement: "640/12 J 118/24", marque: GOAGIL-VII, ...}
    choix_possibles: ["meme_produit:c1", "nouveau"]
    choix:
    par:
    le:
```

- [ ] **Step 1: Failing tests** — `test_report_totals_match_draft` ; `test_template_preserves_existing_choices` ; puis la validation (Review Focus 3) :

```python
@pytest.mark.parametrize("mutate,msg", [
    (lambda d: d["cas"][0].update(choix=None), "sans choix"),
    (lambda d: d["cas"][0].update(choix="meme_produit:c9"), "c9"),
    (lambda d: d["cas"][0].update(choix="peut-etre"), "invalide"),
    (lambda d: d["cas"][0].update(id="inconnu:1"), "inconnu"),
    (lambda d: d["cas"].pop(), "manquant"),
    (lambda d: d["cas"][0].update(par=None), "par"),
])
def test_invalid_decisions_listed(mutate, msg, draft_with_two_cases, tmp_path): ...
    # DecisionsInvalid, un problème par cas fautif, message contenant `msg`
```

- [ ] **Step 2–4:** FAIL → implémenter (PyYAML `safe_load`/`safe_dump`, `allow_unicode=True`, `sort_keys=False`) → PASS
- [ ] **Step 5:** Commit `feat(admin): review report and decisions file`

---

### Task 9: `publish` — application des décisions

**Files:**
- Create: `backend/src/synapse_admin/publish.py`, `backend/tests/test_publish.py`
- Modify: `backend/src/synapse_admin/repository.py`, `backend/src/synapse_admin/cli.py`

**Interfaces:**
- Consumes: `load_draft`, `load_decisions`, `export_sqlite` (Task 10 — appelé à la fin ; jusqu'à Task 10, `publish` s'arrête à la base)
- Produces:
  - `apply_and_publish(conn, label: str, decisions_path: Path) -> PublishSummary` dans une transaction : valider les décisions (refus = rien d'écrit), résoudre chaque cas (`meme_produit` → `produit_id` du candidat ; `nouveau` → nouvel uuid ; `disparu` → aucun `produit_version` ; `garder` → seule la ligne choisie est conservée), créer les lignes `produit` manquantes, insérer `decision`, passer la version en `publiee` et la précédente en `remplacee`.
  - `published_products(conn, label) -> list[tuple[UUID, Product]]`
  - CLI : `synapse-admin publish YYYY-MM`.

- [ ] **Step 1: Failing tests** — `test_publish_refuses_pending_case_and_writes_nothing` ; `test_same_product_keeps_id` (GOAGIL → COAGIL avec `meme_produit:c1` : `produit_id` identique dans les deux versions) ; `test_new_choice_creates_new_id` ; `test_previous_version_becomes_replaced` ; `test_decisions_recorded_with_author`.
- [ ] **Step 2–4:** FAIL → implémenter → PASS
- [ ] **Step 5:** Commit `feat(admin): publish applies decisions`

---

### Task 10: Export SQLite, manifeste et `search`

**Files:**
- Create: `backend/src/synapse_admin/search.py`, `backend/tests/test_export_search.py`
- Modify: `backend/src/synapse_admin/publish.py`, `backend/src/synapse_admin/cli.py`

**Interfaces:**
- Consumes: `published_products`
- Produces:
  - `export_sqlite(products: list[tuple[UUID, Product]], meta: dict[str, str], out_dir: Path) -> Path` → `publications/nomenclature-YYYY-MM.sqlite` + `publications/manifest.json` (`{"version", "reference_date", "file", "size", "sha256", "source_sha256", "published_at"}`).
  - Schéma SQLite : `produit(rowid, id TEXT UNIQUE, marque, dci, code_dci, forme, dosage, conditionnement, liste, statut, origine, date_retrait, motif_retrait, labo, pays, type, hopital INT, officine INT, n_enregistrement)`, `meta(cle PRIMARY KEY, valeur)`, `produit_fts USING fts5(marque, dci, code_dci, labo, content='produit', content_rowid='rowid', tokenize="unicode61 remove_diacritics 2")`, `marque_trgm USING fts5(marque, content='produit', content_rowid='rowid', tokenize='trigram')`. Fichier finalisé par `VACUUM`.
  - `@dataclass SearchHit(product_id: str, marque: str, dci: str, forme: str, dosage: str, conditionnement: str, statut: str)`
  - `search(db_path: Path, query: str, limit: int = 20) -> list[SearchHit]` : tokens alphanumériques (sans accents) → `"tok"*` en ET sur `produit_fts` ; si moins de `limit` résultats et requête ≥ 3 caractères → compléter par `marque_trgm MATCH '"<requête>"'` ; dédoublonner ; trier par rang de statut (`en_vigueur` < `non_renouvele` < `retire`) puis `bm25`.
  - CLI : `synapse-admin search "texte" [--fichier PATH]` (défaut : fichier du manifeste) — affiche marque, DCI, dosage, forme, statut.

- [ ] **Step 1: Failing tests**

```python
def test_prefix_and_accents(published):        assert top(published, "cetiri")[0].marque == "CETIRIPEX"
def test_dci_search(published):                 assert {h.marque for h in search(published, "cetirizine")} >= {"CETIRIPEX", "ZYTREX"}
def test_typo_via_trigram(published):           assert "CETIRIPEX" in names(search(published, "cetripex"))
def test_withdrawn_listed_after_active(published):
    st = [h.statut for h in search(published, "cetirizine")]; assert st == sorted(st, key=STATUS_RANK.get)
@pytest.mark.parametrize("q", ['"', "*", "-", "L'ALCOOL", "é", "", "   ", "AND OR NOT"])
def test_special_queries_never_raise(published, q): search(published, q)
def test_manifest_sha_matches_file(published_dir): ...
def test_search_under_300ms(big_published):      # 6 000 produits synthétiques, 50 requêtes, max < 0,3 s
```

- [ ] **Step 2–4:** FAIL → implémenter, brancher `export_sqlite` à la fin de `apply_and_publish` (hors transaction PostgreSQL, après commit) → PASS
- [ ] **Step 5:** Commit `feat(admin): sqlite export, manifest and search`

---

### Task 11: Bout en bout sur les vrais fichiers et calibrage

**Files:**
- Create: `backend/tests/test_real_files.py`
- Modify: `backend/README.md`, `backend/src/synapse_admin/matching.py` (seuil si besoin)

**Interfaces:**
- Consumes: toute la CLI.

- [ ] **Step 1: Test** (ignoré si `SYNAPSE_REAL_FILES` n'est pas défini ; ce répertoire contient les 5 fichiers, nommés `AAAA-MM.xlsx`) : importer et publier dans l'ordre 2024-08, 2024-12, 2026-04, 2026-06, 2026-08 en tranchant automatiquement chaque cas par son premier `choix_possibles` (aide de test uniquement) ; vérifier à chaque version : lignes lues = somme des catégories + lignes fusionnées en doublon + lignes sujets de cas ; effectif lu par feuille = effectif déclaré dans le titre ; 2026-06 → 2026-08 : le cas GOAGIL-VII/COAGIL-VII apparaît en `changement_titulaire` ; `search` < 300 ms sur 50 marques tirées du fichier.
- [ ] **Step 2:** `SYNAPSE_REAL_FILES=/chemin uv run pytest tests/test_real_files.py -v` ; noter dans le README les totaux par catégorie obtenus et ajuster `BRAND_SIMILARITY_THRESHOLD` si des changements de titulaire évidents sont manqués (consigner la valeur et la raison).
- [ ] **Step 3:** README : installation (`uv sync`, `docker compose up -d`, `uv run alembic upgrade head`), cycle mensuel `import → review → (éditer decisions) → publish`, `search`.
- [ ] **Step 4:** `uv run pytest -v` → tout PASS
- [ ] **Step 5:** Commit `test(admin): end-to-end on real nomenclature files`
