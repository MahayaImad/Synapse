"""Fabrique de classeurs openpyxl reproduisant les fichiers du ministère."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

HEADER_2026_ACTIF = ["N°", "N°ENREGISTREMENT", "CODE", "DENOMINATION COMMUNE INTERNATIONALE", "NOM DE MARQUE", "FORME",
                     "DOSAGE", "CONDITIONNEMENT", "LISTE", "P1", "P2", "OBS",
                     "LABORATOIRES DETENTEUR DE LA DECISION D'ENREGISTREMENT",
                     "PAYS DU LABORATOIRE DETENTEUR DE LA DECISION D'ENREGISTREMENT",
                     "DATE D'ENREGISTREMENT INITIAL ", "DATE D'ENREGISTREMENT  FINAL ", "TYPE", "STATUT", "DUREE DE STABILITE"]
HEADER_2026_NON_RENOUV = HEADER_2026_ACTIF[:-1]
HEADER_2026_RETRAITS = ["N°", "N°ENREGISTREMENT", "CODE", "DENOMINATION COMMUNE INTERNATIONALE", "NOM DE MARQUE", "FORME",
                        "DOSAGE", "CONDITIONNEMENT", "LISTE", "P1", "P2",
                        "LABORATOIRES DETENTEUR DE LA DECISION D'ENREGISTREMENT",
                        "PAYS DU LABORATOIRE DETENTEUR DE LA DECISION D'ENREGISTREMENT",
                        "DATE D'ENREGISTREMENT INITIAL ", "TYPE", "STATUT", "DATE DE RETRAIT", "MOTIF DE RETRAIT"]
HEADER_2024_ACTIF = ["N"] + HEADER_2026_ACTIF[1:7] + ["CONDITIONNEMENT"] + HEADER_2026_ACTIF[8:]
HEADER_2024_RETRAITS = HEADER_2026_RETRAITS[:7] + ["COND"] + HEADER_2026_RETRAITS[8:]

D = datetime


@dataclass
class SheetSpec:
    title: str
    header: list[str]
    rows: list[list]
    title_line: str
    header_row: int
    first_header_cell: str = "N°"
    extra_lines: list[str] = field(default_factory=lambda: [
        "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE",
        "                     MINISTERE DE L'INDUSTRIE PHARMACEUTIQUE ",
        "DIRECTION DE LA PHARMACO-ECONOMIE, DES ACTIVITES PHARMACEUTIQUES ET DE LA REGULATION",
    ])


def build_workbook(path: Path, sheets: list[SheetSpec]) -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    for spec in sheets:
        ws = wb.create_sheet(spec.title)
        for i, line in enumerate(spec.extra_lines):
            ws.cell(row=6 + i, column=1, value=line)
        ws.cell(row=spec.header_row - 2, column=1, value=spec.title_line)
        header = [spec.first_header_cell] + spec.header[1:]
        for c, h in enumerate(header, start=1):
            ws.cell(row=spec.header_row, column=c, value=h)
        for r, values in enumerate(spec.rows, start=spec.header_row + 1):
            for c, v in enumerate(values, start=1):
                ws.cell(row=r, column=c, value=v)
        ws.cell(row=spec.header_row + len(spec.rows) + 2, column=2, value="Arrêtée au 31/08/2026")
    wb.save(path)
    return path


ACTIF_ROWS_2026 = [
    [1, "035/01 A 003/17/23", "01 A 003", "CETIRIZINE DICHLORHYDRATE", "CETIRIPEX", "COMPRIME PELLICULE SECABLE", "10MG",
     "B/15", "LISTE II", "HOP", "OFF", None, "PHARMALLIANCE", "ALGERIE", D(2017, 9, 10), D(2023, 12, 4), "GE", "F", "24 MOIS"],
    [2, "077/01 A 003/17/24", "01 A 003", "CETIRIZINE DICHLORHYDRATE", "ZYTREX", "COMPRIME PELLICULE", "10MG",
     "B/10", "LISTE II", "HOP", "OFF", None, "LAM", "ALGERIE", D(2017, 1, 17), D(2024, 11, 26), "GE", "F", "24 MOIS"],
    [3, "003/12 J 118/24", "12 J 118", "EPTACOG ALFA", "COAGIL-VII", "POUDRE ET SOLVANT POUR SOLUTION INJECTABLE", "4,8MG",
     "B/1 FL DE LYOPHILISAT", "LISTE I", "HOP", None, None, "GROUPE SAIDAL", "ALGERIE", D(2024, 5, 2), D(2024, 5, 2), "BIO", "F", "24 MOIS"],
]
NON_RENOUV_ROWS_2026 = [
    [1, "003/20 B 030/97/09", "20 B 030", "TERPINE/EUCALYPTOL/BENZOATE DE SODIUM", "ENCOFLUIDE ADULTE", "SOL.BUV.",
     "0,25G/0,01G/2G/100ML", "FL/180 ML", "LISTE II", "HOP", "OFF", None, "GROUPE SAIDAL", "ALGERIE", D(1997, 7, 12), D(2009, 7, 19), "GE", "F"],
]
RETRAITS_ROWS_2026 = [
    [1, "356/20 B 030/09", "20 B 030", "TERPINE / EUCALYPTOL", "PULMOFLUIDE SIMPLE", "SIROP", "0,25G/100ML", "FL./150ML",
     "Liste II", "HOP", "OFF", "COOPER MAROC", "MAROC", D(2009, 2, 28), "GE", "F", "ABROGATION",
     "PRODUIT NON COMMERCIALISE ET DECISION NON RENOUVELEE"],
    [2, "099/27 A 001/13", "27 A 001", "BUSULFAN", "BUSILVEX", "SOL. A DILUER P. PERF. IV", "6MG/ML (60MG/10ML)",
     "B/08FL. DE 10ML", "LISTE I", "HOP", None, "PIERRE FABRE MEDICAMENT", "FRANCE", D(2013, 2, 18), "RE", "I",
     D(2024, 3, 31), "RETRAIT PAR LE DETENTEUR POUR MOTIF COMMERCIAL"],
]


def _drop(header: list[str], rows: list[list], column: str | None):
    if column is None or column not in header:
        return header, rows
    i = header.index(column)
    return header[:i] + header[i + 1:], [r[:i] + r[i + 1:] for r in rows]


def build_2026(tmp_path: Path, drop_column: str | None = None, actif_rows=None, month="AOUT", day=31,
               name="aout-2026.xlsx") -> Path:
    h, rows = _drop(HEADER_2026_ACTIF, actif_rows if actif_rows is not None else ACTIF_ROWS_2026, drop_column)
    return build_workbook(tmp_path / name, [
        SheetSpec(f"Nomenclature {month.capitalize()} 2026", h, rows,
                  f"NOMENCLATURE NATIONALE DES PRODUITS PHARMACEUTIQUES A USAGE DE LA MEDECINE HUMAINE AU {day} {month} 2026  ( 5425 DE )", 16),
        SheetSpec("Non Renouvelés ", HEADER_2026_NON_RENOUV, NON_RENOUV_ROWS_2026,
                  f"LISTE DES PRODUITS ... QUI N'ONT PAS FAIT L'OBJET DE RENOUVELLEMENT AU {day} {month} 2026 ( 1491 DE ) ", 12),
        SheetSpec("Retraits", HEADER_2026_RETRAITS, RETRAITS_ROWS_2026,
                  f"LISTE DES PRODUITS ... FAISANT L'OBJET DE RETRAIT AU {day} {month} 2026  ( 2679 DE )", 11),
    ])


def build_2024(tmp_path: Path) -> Path:
    rows = [["1"] + r[1:] for r in ACTIF_ROWS_2026[:2]]
    return build_workbook(tmp_path / "aout-2024.xlsx", [
        SheetSpec(" Nomenclature AOUT 2024", HEADER_2024_ACTIF, rows,
                  "NOMENCLATURE NATIONALE ... AU 31 AOUT 2024 ( 4898 DE )", 17, first_header_cell="N"),
        SheetSpec("Retraits", HEADER_2024_RETRAITS, RETRAITS_ROWS_2026[:1],
                  "LISTE DES PRODUITS ... RETRAIT AU 31 AOUT 2024 ( 2532 DE )", 11),
    ])
