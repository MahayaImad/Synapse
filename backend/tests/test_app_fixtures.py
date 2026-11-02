import json
import sqlite3
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "make_app_fixtures.py"
SPECIAL = ['"', "*", "-", "L'ALCOOL", "é", "", "AND OR NOT", "a" * 300]


def generate(out: Path) -> Path:
    subprocess.run([sys.executable, str(SCRIPT), str(out)], check=True, capture_output=True)
    return out


def test_fixtures_are_deterministic(tmp_path):
    a, b = generate(tmp_path / "a"), generate(tmp_path / "b")
    for name in ("search_cases.json", "equivalents_cases.json"):
        assert (a / name).read_text() == (b / name).read_text()
    rows = lambda p: sqlite3.connect(p / "nomenclature-test.sqlite").execute("select * from produit order by id").fetchall()
    assert rows(a) == rows(b)


def test_cases_cover_review_focus(tmp_path):
    out = generate(tmp_path)
    queries = {c["query"] for c in json.loads((out / "search_cases.json").read_text())}
    assert set(SPECIAL) <= queries and len(queries) >= 40
    eq = json.loads((out / "equivalents_cases.json").read_text())
    retired = [c for c in eq if c["statut"] == "retire"]
    assert any(c["active_same_dosage"] for c in retired) and any(not c["active_same_dosage"] for c in retired)
    with sqlite3.connect(out / "nomenclature-test.sqlite") as c:
        assert c.execute("select max(length(conditionnement)) from produit").fetchone()[0] >= 200
        assert dict(c.execute("select cle, valeur from meta"))["version"] == "2026-08"


def test_unknown_dosage_never_same_dosage(tmp_path):
    out = generate(tmp_path)
    eq = json.loads((out / "equivalents_cases.json").read_text())
    with sqlite3.connect(out / "nomenclature-test.sqlite") as c:
        ids = dict(c.execute("select marque, id from produit where code_dci = '14 H 097'"))
    polivit = next(x for x in eq if x["id"] == ids["POLIVIT"])
    assert polivit["same_dosage"] == [] and polivit["active_same_dosage"] == []
    assert [g["dosage"] for g in polivit["other_dosages"]] == ["", "500MG"]
