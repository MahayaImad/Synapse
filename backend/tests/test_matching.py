from uuid import UUID, uuid4

import pytest

from rows import product
from synapse_admin.matching import PreviousProduct, match_versions

PREV_ID = UUID("00000000-0000-0000-0000-000000000001")

ZYTREX = dict(n_enregistrement="077/01 A 003/17", marque="ZYTREX", conditionnement="B/10", labo="LAM")
GOAGIL = dict(n_enregistrement="640/12 J 118/24", code="12 J 118", dci="EPTACOG ALFA", marque="GOAGIL-VII",
              forme="POUDRE ET SOLVANT", dosage="4,8MG", conditionnement="B/1 FLC DE LYOPHILISAT", labo="LAB 640")
COAGIL = {**GOAGIL, "n_enregistrement": "003/12 J 118/24", "marque": "COAGIL-VII", "labo": "GROUPE SAIDAL"}
KINADYN = dict(n_enregistrement="263/14 G 175/22", code="14 G 175", dci="CALCIUM/VITAMINE D3", marque="KINADYN-OS",
               dosage="500MG/400UI", conditionnement="B/30")


def prev(p, pid=PREV_ID):
    return PreviousProduct(pid, p)


def gap(old, new):
    r = match_versions([old], [new])
    assert r.cases == [] and len(r.gaps) == 1
    return r.gaps[0]


def test_first_import_everything_new():
    r = match_versions([], [product()])
    assert [g.category for g in r.gaps] == ["nouveau"] and r.cases == []


def test_tier1_exact():
    g = gap(prev(product()), product())
    assert (g.category, g.tier, g.product_id) == ("inchange", 1, PREV_ID)


def test_tier1_non_clinical_change_is_modified():
    g = gap(prev(product()), product(duree_stabilite="36 MOIS"))
    assert (g.category, g.tier, g.changed_fields) == ("modifie", 1, ["stability"])


def test_tier2_renewal_same_stem():
    g = gap(prev(product(**ZYTREX)), product(**{**ZYTREX, "n_enregistrement": "077/01 A 003/17/24"}))
    assert (g.category, g.tier, g.changed_fields) == ("modifie", 2, ["reg_raw"])


def test_tier3_packaging_fix_is_safe():
    g = gap(prev(product(conditionnement="B/15")), product(conditionnement="B/ 15 COMPRIMES"))
    assert (g.category, g.tier, g.changed_fields) == ("modifie", 3, ["packaging"])


@pytest.mark.parametrize("field,value", [("marque", "CETIRIPEX GE"), ("dosage", "20MG"), ("forme", "SIROP")])
def test_clinical_change_is_a_case(field, value):
    r = match_versions([prev(product())], [product(**{field: value})])
    assert [c.kind for c in r.cases] == ["champ_clinique"] and r.gaps == []
    assert r.cases[0].candidates[0].product_id == PREV_ID and r.cases[0].candidates[0].ref == "c1"


def test_holder_change_is_a_case():
    r = match_versions([prev(product(**GOAGIL))], [product(**COAGIL)])
    assert [c.kind for c in r.cases] == ["changement_titulaire"]
    assert r.cases[0].candidates[0].product_id == PREV_ID
    assert r.gaps == []


def test_unrelated_brand_is_new_not_holder_change():
    r = match_versions([prev(product(**GOAGIL))], [product(**{**COAGIL, "marque": "NOVOSEVEN"})])
    assert sorted(c.kind for c in r.cases) == ["disparu_sans_retrait"]
    assert [g.category for g in r.gaps] == ["nouveau"]


def test_status_change_same_product():
    g = gap(prev(product(sheet="en_vigueur")), product(sheet="retire", date_retrait="31/03/2026"))
    assert g.category == "statut" and "withdrawal_date" in g.changed_fields


def test_disappeared_without_withdrawal_is_a_case():
    r = match_versions([prev(product(**KINADYN))], [])
    assert [c.kind for c in r.cases] == ["disparu_sans_retrait"]
    assert r.cases[0].subject_product_id == PREV_ID and r.cases[0].case_id == f"disparu_sans_retrait:{PREV_ID}"


def test_disappeared_already_withdrawn_is_plain_gap():
    r = match_versions([prev(product(sheet="retire", **KINADYN))], [])
    assert [g.category for g in r.gaps] == ["disparu"] and r.cases == []


def test_multiple_candidates_same_stem():
    olds = [prev(product(conditionnement="B/10"), uuid4()), prev(product(conditionnement="B/20"), uuid4())]
    news = [product(conditionnement="B/ 10", row_number=1), product(conditionnement="B/ 20", row_number=2)]
    r = match_versions(olds, news)
    assert [c.kind for c in r.cases] == ["candidats_multiples"] * 2 + ["disparu_sans_retrait"] * 2
    assert all(len(c.candidates) == 2 for c in r.cases if c.kind == "candidats_multiples")


def test_conservation():
    olds = [prev(product(**ZYTREX), uuid4()), prev(product(**GOAGIL), uuid4()), prev(product(**KINADYN), uuid4()),
            prev(product(), uuid4())]
    news = [product(**{**ZYTREX, "n_enregistrement": "077/01 A 003/17/24"}), product(**COAGIL), product(),
            product(n_enregistrement="999/01 A 001/26", marque="NOUVEAU")]
    r = match_versions(olds, news)
    new_seen = [id(g.new) for g in r.gaps if g.new] + [id(c.subject) for c in r.cases if c.subject]
    assert sorted(new_seen) == sorted(id(n) for n in news)
    old_in_gaps = [g.product_id for g in r.gaps if g.old]
    old_in_cases = {c.subject_product_id for c in r.cases} | {k.product_id for c in r.cases for k in c.candidates}
    assert len(old_in_gaps) == len(set(old_in_gaps)) and not set(old_in_gaps) & old_in_cases
    assert set(old_in_gaps) | (old_in_cases - {None}) == {o.product_id for o in olds}


@pytest.mark.parametrize("field,old,new", [("dosage", "10 MG", "10MG"), ("marque", "ANTALFEN-GYN", "ANTALFEN GYN"),
                                           ("marque", "DOLI RHUME", "DOLIRHUME"), ("forme", "SOL.INJ", "SOL INJ")])
def test_formatting_only_clinical_change_is_safe_modification(field, old, new):
    g = gap(prev(product(**{field: old})), product(**{field: new}))
    assert g.category == "modifie" and g.changed_fields


@pytest.mark.parametrize("field,old,new", [("dosage", "0.5MG", "05MG"), ("dosage", "0,5MG", "0.5MG"),
                                           ("dosage", "10MG", "100MG"), ("marque", "XUDOL 400", "XYDOL 400")])
def test_meaningful_clinical_change_stays_a_case(field, old, new):
    r = match_versions([prev(product(**{field: old}))], [product(**{field: new})])
    assert [c.kind for c in r.cases] == ["champ_clinique"]
