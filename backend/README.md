# synapse-admin

Outil en ligne de commande d'administration de la nomenclature nationale des
produits pharmaceutiques (Synapse, phase 1). Conception :
`docs/superpowers/specs/2026-11-01-nomenclature-import-design.md`.

## Installation

```bash
cd backend
uv sync
docker compose up -d                 # PostgreSQL 16 (bases synapse et synapse_test)
uv run alembic upgrade head          # schéma
```

Sans Docker, n'importe quel PostgreSQL ≥ 14 convient : définir
`DATABASE_URL` (défaut `postgresql+psycopg://synapse:synapse@localhost:5432/synapse`)
et `TEST_DATABASE_URL` pour les tests (défaut `…/synapse_test`).

## Cycle mensuel

Toutes les commandes s'exécutent depuis la racine du dépôt (`--workdir`
vaut `./nomenclature` par défaut) avec `uv run --project backend synapse-admin …`.

1. Télécharger le fichier Excel du mois sur miph.gov.dz.
2. `synapse-admin import NOMENCLATURE.xlsx --version 2026-08`
   — lit les 3 feuilles, compare à la version publiée, enregistre un brouillon.
   Refusé si le mois ne correspond pas au titre du fichier, si la version
   n'est pas postérieure à la dernière publiée, ou si un autre brouillon existe.
   `--remplacer` refait un brouillon.
3. `synapse-admin review 2026-08`
   — écrit `nomenclature/reports/2026-08.md` (totaux, cas, modifications,
   anomalies) et `nomenclature/decisions/2026-08.yaml`.
4. Éditer le fichier de décisions : pour chaque cas, `choix` (une valeur de
   `choix_possibles`), `par`, `le`. Relancer `review` conserve les choix déjà saisis.
5. `synapse-admin publish 2026-08`
   — refuse tant qu'un cas est sans choix valide ; sinon publie, enregistre les
   décisions (audit) et génère `nomenclature/publications/nomenclature-2026-08.sqlite`
   et `manifest.json` (version, taille, SHA-256) pour l'app.
6. Versionner `nomenclature/decisions/` et `nomenclature/reports/` dans git.

Autres commandes : `status` (versions), `search "texte"` (recherche dans le
fichier publié, comme l'app hors connexion), `export VERSION` (régénère le
fichier SQLite d'une version publiée).

### Cas à trancher

| Type | Signification | Choix |
| --- | --- | --- |
| `champ_clinique` | Même numéro, mais marque, dosage ou forme changés | `meme_produit:c1`, `nouveau` |
| `changement_titulaire` | Même code DCI et dosage, marque proche, autre labo | `meme_produit:cN`, `nouveau` |
| `candidats_multiples` | Plusieurs présentations possibles sous la même décision | `meme_produit:cN`, `nouveau` |
| `disparu_sans_retrait` | Produit en vigueur absent du fichier, ni retiré ni non renouvelé | `disparu` |
| `double_feuille` | Produit à la fois en vigueur et non renouvelé/retiré | `garder:cN` |

Différences de mise en forme seule (espaces ; tirets, points et apostrophes
dans la marque et la forme) : « modifié », jamais un cas. Les espaces sont les
seuls ignorés dans le dosage.

## Tests

```bash
cd backend
uv run pytest
SYNAPSE_REAL_FILES=/chemin/vers/fichiers uv run pytest tests/test_real_files.py -s   # AAAA-MM.xlsx
```

### Résultats sur les fichiers réels (import successif, décisions automatiques de test)

| Version | Nouveaux | Modifiés | Statut | Disparus | À trancher | Anomalies |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-08 | 9 034 | — | — | — | 1 | 223 |
| 2024-12 | 137 | 927 | 14 | 6 | 456 | 51 |
| 2026-04 | 383 | 3 644 | 171 | 8 | 456 | 49 |
| 2026-06 | 44 | 37 | 0 | 0 | 25 | 49 |
| 2026-08 | 42 | 164 | 2 | 0 | 28 | 50 |

Entre deux mois consécutifs, il reste 25 à 30 cas ; les écarts de 4 à 16 mois
en produisent davantage (le ministère réécrit des formes et des dosages).
Recherche : 10 ms au pire sur 50 marques, fichier publié ≈ 3,6 Mo.

Seuil de ressemblance des marques pour les changements de titulaire :
`BRAND_SIMILARITY_THRESHOLD = 85` (rapidfuzz `ratio`) — les 26 propositions
de 2024-12 sont toutes de vrais transferts (ex. Sanofi Aventis → Propharmal).
