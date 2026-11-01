import pytest
import yaml
from sqlalchemy import text

from builders import ACTIF_ROWS_2026, RETRAITS_ROWS_2026, build_2026
from synapse_admin import repository as repo
from synapse_admin.decisions import DecisionsInvalid, write_decisions_template
from synapse_admin.importer import run_import
from synapse_admin.publish import PublishRefused, apply_and_publish, published_products

GOAGIL_ROW = [3, "640/12 J 118/24", "12 J 118", "EPTACOG ALFA", "GOAGIL-VII", "POUDRE ET SOLVANT POUR SOLUTION INJECTABLE",
              "4,8MG", "B/1 FL DE LYOPHILISAT", "LISTE I", "HOP", None, None, "LAB 640", "ALGERIE", None, None, "BIO", "I", "24 MOIS"]


def decide(conn, tmp_path, label, choices=None, by="imad"):
    p = tmp_path / f"{label}.yaml"
    draft = repo.load_draft(conn, label)
    write_decisions_template(draft, p)
    d = yaml.safe_load(p.read_text())
    for c in d["cas"]:
        c["choix"] = (choices or {}).get(c["type"], c["choix_possibles"][0])
        c["par"], c["le"] = by, "2026-09-03"
    p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False))
    return p


def two_versions(conn, tmp_path, choices=None):
    first = [r for r in ACTIF_ROWS_2026[:2]] + [GOAGIL_ROW]
    run_import(conn, build_2026(tmp_path, actif_rows=first, month="JUILLET", name="juil.xlsx"), "2026-07")
    apply_and_publish(conn, "2026-07", decide(conn, tmp_path, "2026-07"))
    run_import(conn, build_2026(tmp_path), "2026-08")
    return decide(conn, tmp_path, "2026-08", choices)


def ids_by_brand(conn, label):
    return {p.brand: pid for pid, p in published_products(conn, label)}


def test_first_publish_without_cases(conn, tmp_path):
    run_import(conn, build_2026(tmp_path), "2026-08")
    s = apply_and_publish(conn, "2026-08", decide(conn, tmp_path, "2026-08"))
    assert s.products == 6 and s.decisions == 0
    assert repo.find_version(conn, "2026-08").state == "publiee"
    assert conn.execute(text("select count(*) from produit")).scalar() == 6


def test_publish_refuses_pending_case_and_writes_nothing(conn, tmp_path):
    p = two_versions(conn, tmp_path)
    d = yaml.safe_load(p.read_text()); d["cas"][0]["choix"] = None
    p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False))
    with pytest.raises(DecisionsInvalid, match="sans choix"):
        apply_and_publish(conn, "2026-08", p)
    assert repo.find_version(conn, "2026-08").state == "brouillon"
    assert conn.execute(text("select count(*) from decision")).scalar() == 0


def test_same_product_keeps_id(conn, tmp_path):
    p = two_versions(conn, tmp_path, {"changement_titulaire": "meme_produit:c1"})
    before = ids_by_brand(conn, "2026-07")
    apply_and_publish(conn, "2026-08", p)
    after = ids_by_brand(conn, "2026-08")
    assert after["COAGIL-VII"] == before["GOAGIL-VII"]
    assert after["CETIRIPEX"] == before["CETIRIPEX"]


def test_new_choice_creates_new_id(conn, tmp_path):
    p = two_versions(conn, tmp_path, {"changement_titulaire": "nouveau"})
    before = ids_by_brand(conn, "2026-07")
    apply_and_publish(conn, "2026-08", p)
    after = ids_by_brand(conn, "2026-08")
    assert after["COAGIL-VII"] not in before.values()
    assert conn.execute(text("select count(*) from produit where id=:i"), {"i": after["COAGIL-VII"]}).scalar() == 1


def test_previous_version_becomes_replaced(conn, tmp_path):
    apply_and_publish(conn, "2026-08", two_versions(conn, tmp_path))
    assert {v.label: v.state for v in repo.list_versions(conn)} == {"2026-07": "remplacee", "2026-08": "publiee"}


def test_decisions_recorded_with_author(conn, tmp_path):
    apply_and_publish(conn, "2026-08", two_versions(conn, tmp_path, {"changement_titulaire": "meme_produit:c1"}))
    rows = conn.execute(text("select case_id, choice, decided_by from decision")).all()
    assert [(r.choice, r.decided_by) for r in rows] == [("meme_produit:c1", "imad")]


def test_garder_keeps_only_chosen_row(conn, tmp_path):
    actif = ACTIF_ROWS_2026 + [[4] + RETRAITS_ROWS_2026[1][1:11] + [None] + RETRAITS_ROWS_2026[1][11:13] + [None, None, "RE", "I", None]]
    run_import(conn, build_2026(tmp_path, actif_rows=actif), "2026-08")
    p = decide(conn, tmp_path, "2026-08", {"double_feuille": "garder:c2"})
    apply_and_publish(conn, "2026-08", p)
    busilvex = [x for _, x in published_products(conn, "2026-08") if x.brand == "BUSILVEX"]
    assert [x.sheet for x in busilvex] == ["retire"]


def test_published_version_cannot_be_republished(conn, tmp_path):
    run_import(conn, build_2026(tmp_path), "2026-08")
    p = decide(conn, tmp_path, "2026-08")
    apply_and_publish(conn, "2026-08", p)
    with pytest.raises(PublishRefused, match="publiee"):
        apply_and_publish(conn, "2026-08", p)
