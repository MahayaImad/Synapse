from datetime import date, datetime
from uuid import UUID

import pytest
import yaml

from rows import product
from synapse_admin.decisions import DecisionsInvalid, load_decisions, render_report, write_decisions_template
from synapse_admin.matching import Gap
from synapse_admin.model import Anomaly, Candidate, Case
from synapse_admin.repository import Draft, VersionRow

OLD = UUID("00000000-0000-0000-0000-00000000000a")
GONE = UUID("00000000-0000-0000-0000-00000000000b")


@pytest.fixture
def draft():
    v = VersionRow(1, "2026-08", date(2026, 8, 31), "aout.xlsx", "f00d", "brouillon", datetime(2026, 9, 2), None)
    gaps = [Gap("nouveau", None, UUID(int=5), None, product(marque="NOUVEAU"), []),
            Gap("nouveau", None, UUID(int=6), None, product(marque="AUTRE"), []),
            Gap("modifie", 3, UUID(int=7), product(conditionnement="B/15"), product(conditionnement="B/ 15"), ["packaging"])]
    cases = [Case("champ_clinique:en_vigueur:12", "champ_clinique", product(dosage="20MG", row_number=12), None,
                  [Candidate("c1", OLD, product())]),
             Case(f"disparu_sans_retrait:{GONE}", "disparu_sans_retrait", None, GONE, [])]
    anomalies = [Anomaly("en_vigueur", 40, "liste", "LISTE III", "Liste non reconnue")]
    return Draft(v, gaps, cases, anomalies)


def fill(path, choices, by="imad", when="2026-09-03"):
    d = yaml.safe_load(path.read_text())
    for c in d["cas"]:
        c["choix"] = choices[c["id"]]
        c["par"], c["le"] = by, when
    path.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False))
    return d


VALID = {"champ_clinique:en_vigueur:12": "meme_produit:c1", f"disparu_sans_retrait:{GONE}": "disparu"}


def test_report_totals_match_draft(draft):
    md = render_report(draft)
    assert "| nouveau | 2 |" in md and "| modifie | 1 |" in md and "| à trancher | 2 |" in md and "| anomalies | 1 |" in md
    assert "champ_clinique:en_vigueur:12" in md and "dosage : 10MG → 20MG" in md
    assert "f00d" in md


def test_template_lists_possible_choices(draft, tmp_path):
    p = tmp_path / "d.yaml"
    write_decisions_template(draft, p)
    d = yaml.safe_load(p.read_text())
    assert d["version"] == "2026-08"
    by_id = {c["id"]: c for c in d["cas"]}
    assert by_id["champ_clinique:en_vigueur:12"]["choix_possibles"] == ["meme_produit:c1", "nouveau_et_disparu:c1"]
    assert by_id[f"disparu_sans_retrait:{GONE}"]["choix_possibles"] == ["disparu"]
    assert all(c["choix"] is None for c in d["cas"])


def test_template_preserves_existing_choices(draft, tmp_path):
    p = tmp_path / "d.yaml"
    write_decisions_template(draft, p)
    fill(p, VALID)
    write_decisions_template(draft, p)
    d = yaml.safe_load(p.read_text())
    assert {c["id"]: c["choix"] for c in d["cas"]} == VALID and d["cas"][0]["par"] == "imad"


def test_valid_decisions_loaded(draft, tmp_path):
    p = tmp_path / "d.yaml"
    write_decisions_template(draft, p)
    fill(p, VALID)
    decisions = load_decisions(p, draft)
    assert {(x.case_id, x.choice, x.decided_by, x.decided_at) for x in decisions} == {
        (k, v, "imad", date(2026, 9, 3)) for k, v in VALID.items()}


@pytest.mark.parametrize("mutate,msg", [
    (lambda d: d["cas"][0].update(choix=None), "sans choix"),
    (lambda d: d["cas"][0].update(choix="meme_produit:c9"), "c9"),
    (lambda d: d["cas"][0].update(choix="peut-etre"), "invalide"),
    (lambda d: d["cas"][0].update(id="inconnu:1"), "inconnu"),
    (lambda d: d["cas"].pop(), "manquant"),
    (lambda d: d["cas"][0].update(par=None), "par"),
    (lambda d: d["cas"][0].update(le="hier"), "date"),
    (lambda d: d.update(version="2026-07"), "2026-07"),
])
def test_invalid_decisions_listed(mutate, msg, draft, tmp_path):
    p = tmp_path / "d.yaml"
    write_decisions_template(draft, p)
    d = fill(p, VALID)
    mutate(d)
    p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False))
    with pytest.raises(DecisionsInvalid) as e:
        load_decisions(p, draft)
    assert any(msg in problem for problem in e.value.problems), e.value.problems


def test_same_old_product_claimed_twice_is_invalid(draft, tmp_path):
    draft.cases.append(Case("changement_titulaire:en_vigueur:13", "changement_titulaire", product(row_number=13), None,
                            [Candidate("c1", OLD, product())]))
    p = tmp_path / "d.yaml"
    write_decisions_template(draft, p)
    fill(p, {**VALID, "changement_titulaire:en_vigueur:13": "meme_produit:c1"})
    with pytest.raises(DecisionsInvalid, match="plusieurs"):
        load_decisions(p, draft)
