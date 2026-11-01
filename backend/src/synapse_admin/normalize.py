"""Normalisation d'une ligne brute en Product ; tout inconnu devient une Anomaly."""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

from .model import Anomaly, Product, RawRow
from .regnum import normalize_dci_code, parse_registration


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def normalize_text(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v).upper()
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        return repr(v).replace(".", ",")
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return " ".join(str(v).split()).upper()


def _letters(v: object) -> str:
    """Valeur réduite à ses lettres/chiffres, sans accents (HOP*, 0FF., ...)."""
    return re.sub(r"[^A-Z0-9]", "", strip_accents(normalize_text(v)))


class _Ctx:
    def __init__(self, row: RawRow):
        self.row = row
        self.anomalies: list[Anomaly] = []

    def flag(self, field: str, value: object, message: str) -> None:
        self.anomalies.append(Anomaly(self.row.sheet, self.row.row_number, field, normalize_text(value), message))


def _liste(ctx: _Ctx, v: object):
    s = _letters(v)
    if not s:
        return None
    if s.startswith("STUPEFIANT"):
        return "STUPEFIANT"
    if s == "LISTEI":
        return "I"
    if s == "LISTEII":
        return "II"
    ctx.flag("liste", v, "Liste non reconnue")
    return None


def _flag_value(ctx: _Ctx, field: str, v: object, expected: str) -> bool:
    s = _letters(v).replace("0FF", "OFF")
    if not s:
        return False
    if s == expected:
        return True
    ctx.flag(field, v, f"Valeur {field.upper()} non reconnue (attendu {expected})")
    return False


def _type(ctx: _Ctx, v: object):
    s = _letters(v)
    if not s:
        return None
    if s in ("GE", "RE", "BIO"):
        return s
    ctx.flag("type", v, "Type non reconnu")
    return None


def _origin(ctx: _Ctx, v: object):
    s = _letters(v)
    if not s:
        return None
    if s == "F":
        return "fabrique_localement"
    if s == "I":
        return "importe"
    ctx.flag("statut", v, "Statut non reconnu (attendu F ou I)")
    return None


def _date(ctx: _Ctx, field: str, v: object) -> date | None:
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(v.strip(), fmt).date()
            except ValueError:
                pass
    ctx.flag(field, v, "Date non reconnue")
    return None


def normalize_row(row: RawRow) -> tuple[Product, list[Anomaly]]:
    ctx = _Ctx(row)
    val = row.values.get
    reg_raw = normalize_text(val("n_enregistrement"))
    registration = parse_registration(reg_raw)
    if registration is None:
        ctx.flag("n_enregistrement", reg_raw, "Numéro d'enregistrement absent" if not reg_raw else "Numéro d'enregistrement non décomposable")
    dci_code = normalize_dci_code(normalize_text(val("code")))
    if not dci_code and registration:
        dci_code = registration.dci_code
    product = Product(
        sheet=row.sheet,
        row_number=row.row_number,
        reg_raw=reg_raw,
        registration=registration,
        dci_code=dci_code,
        dci=normalize_text(val("dci")),
        brand=normalize_text(val("marque")),
        form=normalize_text(val("forme")),
        dosage=normalize_text(val("dosage")),
        packaging=normalize_text(val("conditionnement")),
        liste=_liste(ctx, val("liste")),
        hospital=_flag_value(ctx, "p1", val("p1"), "HOP"),
        pharmacy=_flag_value(ctx, "p2", val("p2"), "OFF"),
        type=_type(ctx, val("type")),
        origin=_origin(ctx, val("statut")),
        lab=normalize_text(val("labo")),
        country=normalize_text(val("pays")),
        initial_date=_date(ctx, "date_enregistrement_initial", val("date_enregistrement_initial")),
        final_date=_date(ctx, "date_enregistrement_final", val("date_enregistrement_final")),
        stability=normalize_text(val("duree_stabilite")),
        obs=normalize_text(val("obs")),
        withdrawal_date=_date(ctx, "date_retrait", val("date_retrait")),
        withdrawal_reason=normalize_text(val("motif_retrait")),
        raw=row.raw,
    )
    return product, ctx.anomalies
