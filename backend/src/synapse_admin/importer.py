"""Orchestration de l'import d'un fichier mensuel."""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Connection

from . import repository
from .consolidate import consolidate
from .excel_reader import MONTHS, read_workbook
from .matching import match_versions
from .model import Anomaly
from .normalize import normalize_row

_LABEL = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
MONTH_NAMES = {v: k for k, v in MONTHS.items()}


class ImportRefused(Exception):
    pass


@dataclass
class ImportSummary:
    label: str
    rows_read: int
    counts_by_category: dict[str, int]
    cases: int
    anomalies: int


@contextmanager
def atomic(conn: Connection):
    """Transaction (ou point de sauvegarde si une transaction est déjà ouverte)."""
    tx = conn.begin_nested() if conn.in_transaction() else conn.begin()
    with tx:
        yield


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _check_label(label: str, reference_date) -> None:
    m = _LABEL.match(label)
    if not m:
        raise ImportRefused(f"Version « {label} » invalide : format attendu AAAA-MM (ex. 2026-08)")
    if reference_date is None:
        raise ImportRefused("Date de référence introuvable dans le titre de la feuille Nomenclature")
    if (int(m.group(1)), int(m.group(2))) != (reference_date.year, reference_date.month):
        raise ImportRefused(
            f"Le fichier est arrêté au {reference_date.day} {MONTH_NAMES[reference_date.month]} {reference_date.year}, "
            f"pas en {label} : vérifier --version")


def run_import(conn: Connection, path: Path, label: str, replace: bool = False) -> ImportSummary:
    path = Path(path)
    wb = read_workbook(path)
    _check_label(label, wb.reference_date)
    with atomic(conn):
        existing = repository.find_version(conn, label)
        if existing is not None:
            if existing.state != "brouillon":
                raise ImportRefused(f"La version {label} est déjà publiée ({existing.state}) : elle ne peut pas être remplacée")
            if not replace:
                raise ImportRefused(f"Un brouillon {label} existe déjà : relancer avec --remplacer pour le refaire")
            repository.delete_draft(conn, label)
        others = [v.label for v in repository.list_versions(conn) if v.state == "brouillon"]
        if others:
            raise ImportRefused(f"Le brouillon {others[0]} doit d'abord être publié ou supprimé")
        published = repository.latest_published(conn)
        previous = []
        if published is not None:
            version, previous = published
            if wb.reference_date <= version.reference_date:
                raise ImportRefused(
                    f"Ordre chronologique : {label} ({wb.reference_date}) n'est pas postérieure à la version publiée "
                    f"{version.label} ({version.reference_date})")

        products, anomalies = [], []
        for row in wb.rows:
            p, a = normalize_row(row)
            products.append(p)
            anomalies.extend(a)
        for sheet, n in wb.sheet_counts.items():
            declared = wb.declared_counts.get(sheet)
            if declared is not None and declared != n:
                anomalies.append(Anomaly(sheet, 0, "effectif", str(declared),
                                         f"Le titre annonce {declared} produits, {n} lignes numérotées lues"))
        kept, cons_anomalies, cons_cases = consolidate(products)
        anomalies.extend(cons_anomalies)
        match = match_versions(previous, kept)
        repository.save_draft(conn, label, wb.reference_date, path.name, sha256_file(path), kept, anomalies, match,
                              cons_cases, previous)
    return ImportSummary(
        label=label,
        rows_read=len(wb.rows),
        counts_by_category=dict(Counter(g.category for g in match.gaps)),
        cases=len(match.cases) + len(cons_cases),
        anomalies=len(anomalies),
    )
