"""Lecture d'un classeur mensuel du ministère."""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

from .columns import FIELD_LABELS, REQUIRED_FIELDS, canonical_field, is_header_start, normalize_header
from .model import RawRow, SheetKind

MONTHS = {"JANVIER": 1, "FEVRIER": 2, "MARS": 3, "AVRIL": 4, "MAI": 5, "JUIN": 6, "JUILLET": 7, "AOUT": 8,
          "SEPTEMBRE": 9, "OCTOBRE": 10, "NOVEMBRE": 11, "DECEMBRE": 12}
_REF_DATE = re.compile(r"\bAU\s+(\d{1,2})\s+([A-Z]+)\s+(\d{4})")
_MONTH_YEAR = re.compile(r"\b([A-Z]+)\s+(\d{4})\b")
_DECLARED = re.compile(r"\(\s*(\d+)\s*DE\s*\)")


class WorkbookFormatError(Exception):
    pass


@dataclass
class WorkbookData:
    rows: list[RawRow]
    reference_date: date | None
    sheet_counts: dict[SheetKind, int]
    declared_counts: dict[SheetKind, int | None]


def sheet_kind(title: str) -> SheetKind | None:
    t = normalize_header(title)
    if t.startswith("NOMENCLATURE"):
        return "en_vigueur"
    if t.startswith("NON RENOUV"):
        return "non_renouvele"
    if t.startswith("RETRAIT"):
        return "retire"
    return None


def _json_safe(v: object) -> object:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def _cell_value(cell) -> object:
    """Valeur telle qu'affichée pour les nombres au format pourcentage (0.005 au format 0.0% -> « 0,5% »)."""
    v = cell.value
    fmt = getattr(cell, "number_format", "General") or "General"
    if isinstance(v, (int, float)) and not isinstance(v, bool) and "%" in fmt:
        pct = round(v * 100, 6)
        text = str(int(pct)) if float(pct).is_integer() else format(pct, "f").rstrip("0").rstrip(".")
        return text.replace(".", ",") + "%"
    return v


def _is_numbered(cell: object) -> bool:
    if isinstance(cell, bool):
        return False
    if isinstance(cell, (int, float)):
        return True
    return isinstance(cell, str) and cell.strip().isdigit()


def _parse_title(lines: list[str]) -> tuple[date | None, int | None]:
    ref, declared = None, None
    for line in lines:
        text = normalize_header(line)
        m = _REF_DATE.search(text)
        if m and ref is None and m.group(2) in MONTHS:
            try:
                ref = date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))
            except ValueError:
                pass
        if ref is None and not m:
            for mm in _MONTH_YEAR.finditer(text):
                if mm.group(1) in MONTHS:
                    y, mo = int(mm.group(2)), MONTHS[mm.group(1)]
                    ref = date(y, mo, calendar.monthrange(y, mo)[1])
                    break
        d = _DECLARED.search(text)
        if d and declared is None:
            declared = int(d.group(1))
    return ref, declared


def read_workbook(path: Path) -> WorkbookData:
    wb = load_workbook(path, read_only=True, data_only=True)
    rows: list[RawRow] = []
    counts: dict[SheetKind, int] = {}
    declared: dict[SheetKind, int | None] = {}
    references: dict[SheetKind, date | None] = {}
    try:
        for ws in wb.worksheets:
            kind = sheet_kind(ws.title)
            if kind is None:
                continue
            cells = list(ws.iter_rows())
            all_rows = [tuple(c.value for c in r) for r in cells]
            h = next((i for i, r in enumerate(all_rows) if r and is_header_start(r[0])), None)
            if h is None:
                raise WorkbookFormatError(f"Feuille '{ws.title.strip()}' : ligne d'en-tête (N°) introuvable")
            header = all_rows[h]
            fields = {i: canonical_field(c) for i, c in enumerate(header) if c is not None}
            missing = REQUIRED_FIELDS - {f for f in fields.values() if f}
            if missing:
                labels = ", ".join(sorted(FIELD_LABELS[f] for f in missing))
                raise WorkbookFormatError(f"Feuille '{ws.title.strip()}' : colonne(s) obligatoire(s) absente(s) : {labels}")
            title_lines = [str(c) for r in all_rows[:h] for c in r if isinstance(c, str)]
            references[kind], declared[kind] = _parse_title(title_lines)
            n = 0
            for idx, r in enumerate(all_rows[h + 1:], start=h + 2):
                if not r or not _is_numbered(r[0]):
                    continue
                values = {f: _cell_value(cells[idx - 1][i]) for i, f in fields.items() if f and i < len(r)}
                raw = {str(header[i]).strip(): _json_safe(r[i]) for i in fields if i < len(r)}
                rows.append(RawRow(kind, ws.title.strip(), idx, values, raw))
                n += 1
            counts[kind] = n
    finally:
        wb.close()
    if "en_vigueur" not in counts:
        raise WorkbookFormatError("Aucune feuille « Nomenclature … » : ce fichier n'est pas une nomenclature du ministère")
    reference = references.get("en_vigueur") or next((d for d in references.values() if d), None)
    return WorkbookData(rows, reference, counts, declared)
