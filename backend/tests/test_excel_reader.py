from datetime import date

import pytest

from builders import build_2024, build_2026
from synapse_admin.excel_reader import WorkbookFormatError, read_workbook


def test_reads_three_sheets_by_title(tmp_path):
    wb = read_workbook(build_2026(tmp_path))
    assert wb.sheet_counts == {"en_vigueur": 3, "non_renouvele": 1, "retire": 2}
    assert wb.reference_date == date(2026, 8, 31)
    assert wb.declared_counts["en_vigueur"] == 5425


def test_2024_header_variants(tmp_path):
    wb = read_workbook(build_2024(tmp_path))
    rows = wb.rows
    assert rows[0].values["conditionnement"] == "B/15" and rows[0].row_number > 16
    assert wb.reference_date == date(2024, 8, 31)
    retrait = [r for r in rows if r.sheet == "retire"][0]
    assert retrait.values["conditionnement"] == "FL./150ML"          # en-tête "COND"


def test_retraits_columns_by_name_not_position(tmp_path):
    r = [x for x in read_workbook(build_2026(tmp_path)).rows if x.sheet == "retire"][1]
    assert r.values["motif_retrait"] == "RETRAIT PAR LE DETENTEUR POUR MOTIF COMMERCIAL"
    assert "obs" not in r.values


def test_missing_required_column_refused(tmp_path):
    with pytest.raises(WorkbookFormatError, match="DOSAGE"):
        read_workbook(build_2026(tmp_path, drop_column="DOSAGE"))


def test_non_numbered_rows_ignored(tmp_path):
    rows = read_workbook(build_2026(tmp_path)).rows
    assert len(rows) == 6
    assert all(str(r.raw["N°"]).strip().isdigit() for r in rows)


def test_raw_is_json_serializable(tmp_path):
    import json
    for r in read_workbook(build_2026(tmp_path)).rows:
        json.dumps(r.raw)


def test_not_a_nomenclature_refused(tmp_path):
    from openpyxl import Workbook
    p = tmp_path / "x.xlsx"; wb = Workbook(); wb.active.title = "Feuil1"; wb.save(p)
    with pytest.raises(WorkbookFormatError, match="nomenclature"):
        read_workbook(p)


def test_title_without_day_uses_end_of_month(tmp_path):
    from builders import HEADER_2026_ACTIF, ACTIF_ROWS_2026, SheetSpec, build_workbook
    p = build_workbook(tmp_path / "x.xlsx", [SheetSpec(
        "Nomenclature AOUT 2024", HEADER_2026_ACTIF, ACTIF_ROWS_2026,
        "NOMENCLATURE NATIONALE DES PRODUITS PHARMACEUTIQUES A USAGE DE LA MEDECINE HUMAINE -AOUT 2024  ( 4898 DE)", 16)])
    wb = read_workbook(p)
    assert wb.reference_date == date(2024, 8, 31) and wb.declared_counts["en_vigueur"] == 4898
