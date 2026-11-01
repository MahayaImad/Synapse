"""Tests issus de la relecture finale (chaque test reproduit un défaut constaté)."""
import json

import openpyxl
import pytest
import yaml

from builders import ACTIF_ROWS_2026, build_2026
from rows import product
from synapse_admin import repository as repo
from synapse_admin.consolidate import consolidate
from synapse_admin.decisions import DecisionsInvalid, load_decisions, write_decisions_template
from synapse_admin.excel_reader import read_workbook
from synapse_admin.importer import run_import
from synapse_admin.normalize import normalize_row
from synapse_admin.publish import apply_and_publish, export_version, published_products

ZYT = ACTIF_ROWS_2026[1]  # ZYTREX 077/01 A 003/17/24, 10MG, B/10


def zyt(n, packaging, dosage="10MG"):
    r = list(ZYT); r[0] = n; r[7] = packaging; r[6] = dosage
    return r


def fill(path, choices, default_first=True):
    d = yaml.safe_load(path.read_text())
    for c in d["cas"]:
        c["choix"] = choices.get(c["id"], choices.get(c["type"], c["choix_possibles"][0] if default_first else None))
        c["par"], c["le"] = "imad", "2026-09-03"
    path.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False))
    return d


def review(conn, path, label):
    write_decisions_template(repo.load_draft(conn, label), path)
    return path


def publish_july(conn, tmp_path, rows):
    run_import(conn, build_2026(tmp_path, actif_rows=rows, month="JUILLET", name="juil.xlsx"), "2026-07")
    p = review(conn, tmp_path / "07.yaml", "2026-07"); fill(p, {})
    apply_and_publish(conn, "2026-07", p)


# C1 — un choix ne survit pas à un brouillon refait avec d'autres données
def test_remplacer_discards_stale_choices(conn, tmp_path):
    publish_july(conn, tmp_path, [zyt(1, "B/10"), zyt(2, "B/20")])
    run_import(conn, build_2026(tmp_path, actif_rows=[zyt(1, "B/30")]), "2026-08")
    p = review(conn, tmp_path / "08.yaml", "2026-08")
    fill(p, {"candidats_multiples": "meme_produit:c1", "disparu_sans_retrait": "disparu"})
    run_import(conn, build_2026(tmp_path, actif_rows=[zyt(1, "B/30", dosage="5MG")], name="autre.xlsx"), "2026-08", replace=True)
    review(conn, p, "2026-08")
    d = yaml.safe_load(p.read_text())
    assert all(c["choix"] is None for c in d["cas"] if c["type"] == "candidats_multiples")


def test_decisions_file_bound_to_draft(conn, tmp_path):
    publish_july(conn, tmp_path, [zyt(1, "B/10"), zyt(2, "B/20")])
    run_import(conn, build_2026(tmp_path, actif_rows=[zyt(1, "B/30")]), "2026-08")
    p = review(conn, tmp_path / "08.yaml", "2026-08")
    fill(p, {"candidats_multiples": "meme_produit:c1", "disparu_sans_retrait": "disparu"})
    saved = p.read_text()
    run_import(conn, build_2026(tmp_path, actif_rows=[zyt(1, "B/30", dosage="5MG")], name="autre.xlsx"), "2026-08", replace=True)
    p.write_text(saved)                                    # ancien fichier remis en place à la main
    with pytest.raises(DecisionsInvalid, match="brouillon"):
        load_decisions(p, repo.load_draft(conn, "2026-08"))


# I1 — un cas listé deux fois est refusé
def test_duplicate_case_entry_refused(conn, tmp_path):
    publish_july(conn, tmp_path, [zyt(1, "B/10"), zyt(2, "B/20")])
    run_import(conn, build_2026(tmp_path, actif_rows=[zyt(1, "B/30")]), "2026-08")
    p = review(conn, tmp_path / "08.yaml", "2026-08")
    d = fill(p, {"candidats_multiples": "meme_produit:c1"})
    dup = dict(next(c for c in d["cas"] if c["type"] == "candidats_multiples")); dup["choix"] = "nouveau"
    d["cas"].append(dup)
    p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False))
    with pytest.raises(DecisionsInvalid, match="double"):
        load_decisions(p, repo.load_draft(conn, "2026-08"))


# I2 — un ancien produit en vigueur proposé comme candidat mais non retenu exige une décision explicite
def test_unchosen_candidate_needs_explicit_disappearance(conn, tmp_path):
    publish_july(conn, tmp_path, [zyt(1, "B/10"), zyt(2, "B/20")])
    run_import(conn, build_2026(tmp_path, actif_rows=[zyt(1, "B/30")]), "2026-08")
    draft = repo.load_draft(conn, "2026-08")
    gone = [c for c in draft.cases if c.kind == "disparu_sans_retrait"]
    assert len(gone) == 2                                   # B/10 et B/20, tous deux candidats
    p = review(conn, tmp_path / "08.yaml", "2026-08")
    d = yaml.safe_load(p.read_text())
    multi = next(c for c in d["cas"] if c["type"] == "candidats_multiples")
    chosen = next(k["produit_id"] for k in multi["candidats"] if k["ref"] == "c1")
    ch = {multi["id"]: "meme_produit:c1"}
    for c in d["cas"]:
        if c["type"] == "disparu_sans_retrait":
            assert c["choix_possibles"] == ["disparu", "rattache"]
            ch[c["id"]] = "disparu"                         # faux pour celui qui est rattaché
    fill(p, ch)
    with pytest.raises(DecisionsInvalid, match="rattach"):
        load_decisions(p, draft)
    for c in d["cas"]:
        if c["type"] == "disparu_sans_retrait":
            ch[c["id"]] = "rattache" if c["sujet"]["produit_id"] == chosen else "disparu"
    fill(p, ch)
    apply_and_publish(conn, "2026-08", p)
    assert [x.packaging for _, x in published_products(conn, "2026-08") if x.brand == "ZYTREX"] == ["B/30"]


# I3 — fusion seulement des lignes vraiment identiques
def test_duplicate_with_different_form_is_a_case():
    kept, an, cases = consolidate([product(row_number=1, forme="COMPRIME"), product(row_number=2, forme="SIROP")])
    assert [c.kind for c in cases] == ["doublon_divergent"] and an == []


def test_duplicate_with_non_clinical_difference_merged_with_detail():
    kept, an, cases = consolidate([product(row_number=1), product(row_number=2, duree_stabilite="36 MOIS")])
    assert len(kept) == 1 and cases == []
    assert "stabilit" in an[0].message and "identique" not in an[0].message


# I4 — dosage au format pourcentage dans Excel
def test_percent_formatted_dosage_kept_as_percent(tmp_path):
    rows = [list(r) for r in ACTIF_ROWS_2026]
    rows[0][6] = 0.005
    f = build_2026(tmp_path, actif_rows=rows)
    wb = openpyxl.load_workbook(f)
    ws = wb.worksheets[0]
    ws.cell(row=17, column=7).number_format = "0.0%"
    wb.save(f)
    p, an = normalize_row(next(r for r in read_workbook(f).rows if r.values["marque"] == "CETIRIPEX"))
    assert p.dosage == "0,5%" and an == []


def test_numeric_dosage_without_unit_is_flagged():
    from rows import raw
    p, an = normalize_row(raw(dosage=0.03))
    assert p.dosage == "0,03" and [a.field for a in an] == ["dosage"]


# I5 — exporter une version remplacée ne touche pas au manifeste
def test_export_replaced_version_keeps_manifest(conn, tmp_path):
    publish_july(conn, tmp_path, [zyt(1, "B/10")])
    run_import(conn, build_2026(tmp_path, actif_rows=[zyt(1, "B/10")]), "2026-08")
    p = review(conn, tmp_path / "08.yaml", "2026-08"); fill(p, {})
    apply_and_publish(conn, "2026-08", p, tmp_path / "pub")
    export_version(conn, "2026-07", tmp_path / "pub")
    assert json.loads((tmp_path / "pub" / "manifest.json").read_text())["version"] == "2026-08"
    assert (tmp_path / "pub" / "nomenclature-2026-07.sqlite").exists()


# I6 — une ligne en double feuille participe au rapprochement (pas de faux palier 3)
def test_double_feuille_plus_other_presentation(conn, tmp_path):
    publish_july(conn, tmp_path, [zyt(1, "B/10")])
    july_id = {x.packaging: i for i, x in published_products(conn, "2026-07")}["B/10"]
    f = build_2026(tmp_path, actif_rows=[zyt(1, "B/10"), zyt(2, "B/20")])
    wb = openpyxl.load_workbook(f)
    ws = wb["Retraits"]
    r = ws.max_row + 1
    vals = [3, ZYT[1], ZYT[2], ZYT[3], ZYT[4], ZYT[5], "10MG", "B/10", "LISTE II", "HOP", "OFF", "LAM", "ALGERIE",
            None, "GE", "F", None, "RETRAIT"]
    for c, v in enumerate(vals, start=1):
        ws.cell(row=12 + 3, column=c, value=v)
    wb.save(f)
    run_import(conn, f, "2026-08")
    draft = repo.load_draft(conn, "2026-08")
    assert not any(g.category == "modifie" and g.new.packaging == "B/20" for g in draft.gaps)
    p = review(conn, tmp_path / "08.yaml", "2026-08"); fill(p, {"double_feuille": "garder:c2"})
    apply_and_publish(conn, "2026-08", p)
    ids = {(x.packaging, x.sheet): i for i, x in published_products(conn, "2026-08")}
    assert ids[("B/10", "retire")] == july_id and ids[("B/20", "en_vigueur")] != july_id


def test_sole_candidate_choice_states_disappearance(conn, tmp_path):
    from synapse_admin.decisions import possible_choices
    from synapse_admin.matching import PreviousProduct, match_versions
    from uuid import uuid4
    r = match_versions([PreviousProduct(uuid4(), product())], [product(dosage="20MG")])
    assert [c.kind for c in r.cases] == ["champ_clinique"]               # pas de cas disparu séparé
    assert possible_choices(r.cases[0], r.cases) == ["meme_produit:c1", "nouveau_et_disparu:c1"]
