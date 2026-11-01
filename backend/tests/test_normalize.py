from datetime import date

import pytest

from rows import raw
from synapse_admin.normalize import normalize_row


@pytest.mark.parametrize("v,exp", [("LISTE I", "I"), ("Liste I ", "I"), ("lISTE I", "I"), ("LISTE II", "II"),
                                   ("STUPEFIANT", "STUPEFIANT"), ("Stupéfiants", "STUPEFIANT"), ("", None), (" ", None), (None, None)])
def test_liste(v, exp):
    assert normalize_row(raw(liste=v))[0].liste == exp


@pytest.mark.parametrize("p1,p2,hop,off", [("HOP", "OFF", True, True), ("HOP*", "0FF", True, True), ("*HOP", None, True, False),
                                           ("HOP.", "OFF?", True, True), (None, "           ", False, False)])
def test_hop_off(p1, p2, hop, off):
    p = normalize_row(raw(p1=p1, p2=p2))[0]
    assert (p.hospital, p.pharmacy) == (hop, off)


@pytest.mark.parametrize("v,exp", [("F", "fabrique_localement"), ("I ", "importe"), ("i", "importe")])
def test_origin(v, exp):
    assert normalize_row(raw(statut=v))[0].origin == exp


def test_unknown_values_become_anomalies_not_guesses():
    p, an = normalize_row(raw(liste="LISTE III", statut="X", p2="MEDICAMENT SOUMIS A PRESCRIPTION RESTREINTE"))
    assert p.liste is None and p.origin is None
    assert {a.field for a in an} == {"liste", "statut", "p2"}


def test_text_collapsed_and_raw_kept():
    p, _ = normalize_row(raw(marque="VITAMINE C  BGL ", dosage=0.01))
    assert p.brand == "VITAMINE C BGL" and p.dosage == "0,01"
    assert p.raw["NOM DE MARQUE"] == "VITAMINE C  BGL "


def test_integer_cell_has_no_decimals():
    assert normalize_row(raw(dosage=500))[0].dosage == "500"


def test_unparseable_registration_is_anomaly_but_row_kept():
    p, an = normalize_row(raw(n_enregistrement="001/09 H 178 20", code="09 H 178"))
    assert p.registration is None and p.dci_code == "09 H 178"
    assert any(a.field == "n_enregistrement" for a in an)


def test_dates_and_type():
    p, an = normalize_row(raw(type=" RE", date_enregistrement_final="pas une date"))
    assert p.type == "RE" and p.initial_date == date(2017, 9, 10) and p.final_date is None
    assert [a.field for a in an] == ["date_enregistrement_final"]


def test_presentation_key_and_stem():
    p = normalize_row(raw())[0]
    assert p.presentation_key == ("CETIRIPEX", "10MG", "B/15")
    assert p.stem == ("035", "01 A 003", "17")
