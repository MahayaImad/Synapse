import pytest

from synapse_admin.regnum import normalize_dci_code, parse_registration


def test_parse_renewed():
    r = parse_registration("352/01 A 003/06/22")
    assert (r.lab, r.dci_code, r.family, r.subfamily, r.molecule_num) == ("352", "01 A 003", "01", "A", "003")
    assert (r.initial_year, r.renewal_year) == ("06", "22")
    assert r.stem == ("352", "01 A 003", "06")


def test_parse_not_renewed_and_renewal_keeps_stem():
    a = parse_registration("077/01 A 003/17")
    b = parse_registration("077/01 A 003/17/24")
    assert a.renewal_year is None and a.stem == b.stem


def test_parse_tolerates_spaces():
    assert parse_registration(" 003 / 20 B 030 /97/09 ").stem == ("003", "20 B 030", "97")


@pytest.mark.parametrize("bad", ["001/09 H 178 20", "528/04 B 035/  ", "003/09/21 F 056/20", " nv/02 A 055/05/23", ""])
def test_unparseable_returns_none(bad):
    assert parse_registration(bad) is None


def test_normalize_dci_code():
    assert normalize_dci_code("01  A 003") == "01 A 003"
    assert normalize_dci_code(" 01A003 ") == "01 A 003"
