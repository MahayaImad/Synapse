from rows import product
from synapse_admin.consolidate import consolidate, product_identity

VITC = dict(n_enregistrement="235/14 H 222/25", code="14 H 222", dci="ACIDE ASCORBIQUE", marque="VITAMINE C BGL",
            forme="COMPRIME EFFERVESCENT", dosage="1G", conditionnement="B/10", labo="BGL")
NOBAC = dict(n_enregistrement="263/10 G 054/23", code="10 G 054", dci="NIFUROXAZIDE", forme="SUSPENSION BUVABLE",
             dosage="50MG/26,7MG/ML", conditionnement="B/1 FLACON DE 200 ML", labo="NOBAC LAB")


def test_duplicate_after_normalization_merged_with_anomaly():
    kept, an, cases = consolidate([product(row_number=10, **VITC), product(row_number=11, **{**VITC, "marque": "VITAMINE C  BGL"})])
    assert len(kept) == 1 and kept[0].row_number == 10
    assert an[0].message.startswith("Doublon") and an[0].row_number == 11 and cases == []


def test_shared_decision_distinct_presentations_kept():
    kept, an, cases = consolidate([product(row_number=1, **NOBAC, marque="NOBAC FRAISE"),
                                   product(row_number=2, **NOBAC, marque="NOBAC ADULTE GOUT MENTHE")])
    assert len(kept) == 2 and an == [] and cases == []


def test_same_product_in_two_sheets_is_a_case():
    kept, _, cases = consolidate([product(sheet="en_vigueur", row_number=5), product(sheet="retire", row_number=7)])
    assert [c.kind for c in cases] == ["double_feuille"]
    assert [c.ref for c in cases[0].candidates] == ["c1", "c2"]
    assert cases[0].case_id == "double_feuille:en_vigueur:5"
    assert kept == []


def test_identity_uses_stem_so_renewal_is_same_identity():
    a = product(n_enregistrement="077/01 A 003/17"); b = product(n_enregistrement="077/01 A 003/17/24")
    assert product_identity(a) == product_identity(b)


def test_identity_falls_back_to_raw_number():
    assert product_identity(product(n_enregistrement="001/09 H 178 20"))[0] == "001/09 H 178 20"


def test_non_renewed_and_withdrawn_resolves_to_withdrawn():
    kept, an, cases = consolidate([product(sheet="non_renouvele", row_number=3), product(sheet="retire", row_number=9)])
    assert cases == [] and [p.sheet for p in kept] == ["retire"]
    assert an[0].sheet == "non_renouvele" and "retiré" in an[0].message
