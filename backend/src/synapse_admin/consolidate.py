"""Consolidation à l'intérieur d'une version : doublons et produits présents dans plusieurs feuilles."""
from __future__ import annotations

from collections import defaultdict

from .model import Anomaly, Candidate, Case, Product


def product_identity(p: Product) -> tuple:
    return (p.stem or p.reg_raw, p.presentation_key)


def consolidate(products: list[Product]) -> tuple[list[Product], list[Anomaly], list[Case]]:
    groups: dict[tuple, list[Product]] = defaultdict(list)
    for p in products:
        groups[product_identity(p)].append(p)
    kept: list[Product] = []
    anomalies: list[Anomaly] = []
    cases: list[Case] = []
    for group in groups.values():
        first_by_sheet: dict[str, Product] = {}
        for p in group:
            if p.sheet in first_by_sheet:
                f = first_by_sheet[p.sheet]
                anomalies.append(Anomaly(p.sheet, p.row_number, "ligne", p.reg_raw,
                                         f"Doublon de la ligne {f.row_number} (identique après normalisation) : fusionné"))
            else:
                first_by_sheet[p.sheet] = p
        distinct = list(first_by_sheet.values())
        if len(distinct) == 1:
            kept.append(distinct[0])
        else:
            s = distinct[0]
            cases.append(Case(
                case_id=f"double_feuille:{s.sheet}:{s.row_number}",
                kind="double_feuille",
                subject=s,
                subject_product_id=None,
                candidates=[Candidate(f"c{i}", None, p) for i, p in enumerate(distinct, start=1)],
            ))
    kept.sort(key=lambda p: (p.sheet, p.row_number))
    return kept, anomalies, cases
