from datetime import date
from uuid import UUID

from sqlalchemy import text

from rows import product
from synapse_admin import repository as repo
from synapse_admin.consolidate import consolidate
from synapse_admin.matching import match_versions


def _first_import(conn, label="2026-08"):
    kept, anomalies, cases = consolidate([
        product(row_number=1),
        product(row_number=2, n_enregistrement="077/01 A 003/17/24", marque="ZYTREX"),
        product(sheet="en_vigueur", row_number=3, n_enregistrement="099/27 A 001/13", marque="BUSILVEX"),
        product(sheet="retire", row_number=4, n_enregistrement="099/27 A 001/13", marque="BUSILVEX"),
    ])
    match = match_versions([], kept)
    vid = repo.save_draft(conn, label, date(2026, 8, 31), "aout.xlsx", "abc", kept, anomalies, match, cases)
    return vid


def test_migration_creates_extensions(conn):
    ext = set(conn.execute(text("select extname from pg_extension")).scalars())
    assert {"pg_trgm", "unaccent"} <= ext


def test_schema_matches_metadata(conn):
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from synapse_admin.db import metadata
    assert compare_metadata(MigrationContext.configure(conn), metadata) == []


def test_latest_published_none_when_empty(conn):
    assert repo.latest_published(conn) is None


def test_save_and_load_draft_roundtrip(conn):
    _first_import(conn)
    d = repo.load_draft(conn, "2026-08")
    assert d.version.state == "brouillon" and d.version.reference_date == date(2026, 8, 31)
    assert sorted(g.category for g in d.gaps) == ["nouveau", "nouveau"]
    assert {g.new.brand for g in d.gaps} == {"CETIRIPEX", "ZYTREX"}
    assert all(isinstance(g.product_id, UUID) for g in d.gaps)
    [case] = d.cases
    assert case.kind == "double_feuille" and [c.product.sheet for c in case.candidates] == ["en_vigueur", "retire"]
    assert d.gaps[0].new.registration is not None


def test_latest_published_returns_products_with_ids(conn):
    vid = _first_import(conn)
    conn.execute(text("update nomenclature_version set state='publiee' where id=:v"), {"v": vid})
    version, prev = repo.latest_published(conn)
    assert version.label == "2026-08" and len(prev) == 2
    assert all(p.pv_id for p in prev) and {p.product.brand for p in prev} == {"CETIRIPEX", "ZYTREX"}


def test_delete_draft(conn):
    _first_import(conn)
    repo.delete_draft(conn, "2026-08")
    assert repo.find_version(conn, "2026-08") is None


def test_second_draft_links_old_rows(conn):
    vid = _first_import(conn)
    conn.execute(text("update nomenclature_version set state='publiee' where id=:v"), {"v": vid})
    _, prev = repo.latest_published(conn)
    new = [product(row_number=1, duree_stabilite="36 MOIS")]
    match = match_versions(prev, new)
    repo.save_draft(conn, "2026-09", date(2026, 9, 30), "sept.xlsx", "def", new, [], match, [], prev)
    d = repo.load_draft(conn, "2026-09")
    by_cat = {g.category: g for g in d.gaps}
    assert by_cat["modifie"].old.stability == "24 MOIS" and by_cat["modifie"].new.stability == "36 MOIS"
    assert by_cat["modifie"].product_id == next(p.product_id for p in prev if p.product.brand == "CETIRIPEX")
    assert [c.kind for c in d.cases] == ["disparu_sans_retrait"]
