import pytest
from sqlalchemy import text
from typer.testing import CliRunner

from builders import ACTIF_ROWS_2026, build_2026
from conftest import TEST_URL
from synapse_admin import importer, repository as repo
from synapse_admin.importer import ImportRefused, run_import


def publish_raw(conn, label):
    conn.execute(text("update nomenclature_version set state='publiee' where label=:l"), {"l": label})


def test_first_import_all_new(conn, tmp_path):
    s = run_import(conn, build_2026(tmp_path), "2026-08")
    assert s.counts_by_category == {"nouveau": 6} and s.cases == 0
    assert s.rows_read == 6


def test_declared_count_mismatch_is_reported(conn, tmp_path):
    run_import(conn, build_2026(tmp_path), "2026-08")
    msgs = [a.message for a in repo.load_draft(conn, "2026-08").anomalies if a.field == "effectif"]
    assert any("5425" in m and "3" in m for m in msgs)


def test_label_must_match_reference_month(conn, tmp_path):
    with pytest.raises(ImportRefused, match="AOUT 2026"):
        run_import(conn, build_2026(tmp_path), "2026-07")


@pytest.mark.parametrize("label", ["2026-8", "aout", "2026-13"])
def test_label_format(conn, tmp_path, label):
    with pytest.raises(ImportRefused, match="AAAA-MM"):
        run_import(conn, build_2026(tmp_path), label)


def test_older_than_published_refused(conn, tmp_path):
    run_import(conn, build_2026(tmp_path), "2026-08")
    publish_raw(conn, "2026-08")
    old = build_2026(tmp_path, month="JUIN", day=30, name="juin.xlsx")
    with pytest.raises(ImportRefused, match="chronologique"):
        run_import(conn, old, "2026-06")


def test_other_draft_must_be_published_first(conn, tmp_path):
    run_import(conn, build_2026(tmp_path, month="JUIN", day=30, name="juin.xlsx"), "2026-06")
    with pytest.raises(ImportRefused, match="2026-06"):
        run_import(conn, build_2026(tmp_path), "2026-08")


def test_rerun_needs_replace(conn, tmp_path):
    f = build_2026(tmp_path)
    run_import(conn, f, "2026-08")
    with pytest.raises(ImportRefused, match="--remplacer"):
        run_import(conn, f, "2026-08")
    run_import(conn, f, "2026-08", replace=True)
    assert [v.label for v in repo.list_versions(conn)] == ["2026-08"]


def test_published_version_cannot_be_replaced(conn, tmp_path):
    f = build_2026(tmp_path)
    run_import(conn, f, "2026-08"); publish_raw(conn, "2026-08")
    with pytest.raises(ImportRefused, match="publiée"):
        run_import(conn, f, "2026-08", replace=True)


def test_failure_leaves_nothing(conn, tmp_path, monkeypatch):
    original = repo.save_draft

    def boom(*a, **k):
        original(*a, **k)
        raise RuntimeError("panne simulée")

    monkeypatch.setattr(importer.repository, "save_draft", boom)
    with pytest.raises(RuntimeError):
        run_import(conn, build_2026(tmp_path), "2026-08")
    assert repo.list_versions(conn) == []
    assert conn.execute(text("select count(*) from produit_version")).scalar() == 0


def test_second_import_detects_changes(conn, tmp_path):
    run_import(conn, build_2026(tmp_path), "2026-08"); publish_raw(conn, "2026-08")
    rows = [list(r) for r in ACTIF_ROWS_2026]
    rows[1][1] = "077/01 A 003/17/26"                     # ZYTREX renouvelé
    s = run_import(conn, build_2026(tmp_path, actif_rows=rows, month="SEPTEMBRE", day=30, name="sept.xlsx"), "2026-09")
    assert s.counts_by_category == {"inchange": 5, "modifie": 1}


@pytest.fixture
def clean_db(engine):
    yield
    with engine.begin() as c:
        c.execute(text("truncate anomalie, decision, ecart, produit_version, produit, nomenclature_version cascade"))


def test_cli_import_and_status(clean_db, tmp_path, monkeypatch):
    from synapse_admin.cli import app
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    runner = CliRunner()
    r = runner.invoke(app, ["--workdir", str(tmp_path), "import", str(build_2026(tmp_path)), "--version", "2026-08"])
    assert r.exit_code == 0, r.output
    assert "nouveau" in r.output
    r = runner.invoke(app, ["--workdir", str(tmp_path), "status"])
    assert r.exit_code == 0 and "2026-08" in r.output and "brouillon" in r.output
    r = runner.invoke(app, ["--workdir", str(tmp_path), "import", str(build_2026(tmp_path)), "--version", "2026-07"])
    assert r.exit_code == 1 and "AOUT 2026" in r.output


def test_cli_review_writes_files(clean_db, tmp_path, monkeypatch):
    from synapse_admin.cli import app
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    runner = CliRunner()
    assert runner.invoke(app, ["--workdir", str(tmp_path), "import", str(build_2026(tmp_path)), "--version", "2026-08"]).exit_code == 0
    r = runner.invoke(app, ["--workdir", str(tmp_path), "review", "2026-08"])
    assert r.exit_code == 0, r.output
    assert (tmp_path / "reports" / "2026-08.md").read_text().startswith("# Revue de la nomenclature 2026-08")
    assert "cas: []" in (tmp_path / "decisions" / "2026-08.yaml").read_text()
    assert runner.invoke(app, ["--workdir", str(tmp_path), "review", "2099-01"]).exit_code == 1
