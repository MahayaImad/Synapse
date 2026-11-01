"""Consolidation à l'intérieur d'une version : doublons et produits présents dans plusieurs feuilles."""
from __future__ import annotations

from collections import defaultdict

from .matching import changed_fields, clinical_changes
from .model import Anomaly, Candidate, Case, Product

FIELD_NAMES = {"stability": "stabilité", "lab": "labo", "dci": "DCI", "initial_date": "date initiale",
               "final_date": "date finale", "withdrawal_date": "date de retrait", "withdrawal_reason": "motif de retrait",
               "withdrawal_kind": "type de retrait", "obs": "OBS", "country": "pays", "liste": "liste",
               "hospital": "hôpital", "pharmacy": "officine", "origin": "origine", "type": "type", "reg_raw": "n° enregistrement"}


def product_identity(p: Product) -> tuple:
    return (p.stem or p.reg_raw, p.presentation_key)


def _merge_same_sheet(rows: list[Product], anomalies: list[Anomaly]) -> list[Product]:
    """Fusionne les lignes d'une même feuille ; garde distinctes celles dont un champ clinique diffère."""
    distinct: list[Product] = []
    for p in rows:
        twin = next((d for d in distinct if not clinical_changes(d, p)), None)
        if twin is None:
            distinct.append(p)
            continue
        diff = changed_fields(twin, p)
        if diff:
            names = ", ".join(FIELD_NAMES.get(f, f) for f in diff)
            msg = f"Doublon de la ligne {twin.row_number} avec différences ({names}) : ligne {twin.row_number} conservée"
        else:
            msg = f"Doublon de la ligne {twin.row_number} (identique après normalisation) : fusionné"
        anomalies.append(Anomaly(p.sheet, p.row_number, "ligne", p.reg_raw, msg))
    return distinct


def consolidate(products: list[Product]) -> tuple[list[Product], list[Anomaly], list[Case]]:
    """Renvoie (lignes à rapprocher, anomalies, cas).

    Pour chaque cas, le premier candidat est aussi renvoyé dans les lignes à rapprocher (représentant) :
    il porte le rapprochement avec la version publiée ; à la publication, la ligne gardée en hérite.
    """
    groups: dict[tuple, list[Product]] = defaultdict(list)
    for p in products:
        groups[product_identity(p)].append(p)
    kept: list[Product] = []
    anomalies: list[Anomaly] = []
    cases: list[Case] = []
    for group in groups.values():
        by_sheet: dict[str, list[Product]] = defaultdict(list)
        for p in group:
            by_sheet[p.sheet].append(p)
        merged = {s: _merge_same_sheet(rows, anomalies) for s, rows in by_sheet.items()}
        divergent = any(len(rows) > 1 for rows in merged.values())
        if not divergent and "en_vigueur" not in merged and len(merged) == 2:
            # Non renouvelé et retiré : aucun des deux n'est délivrable, le retrait prime.
            nr, rt = merged.pop("non_renouvele")[0], merged["retire"][0]
            anomalies.append(Anomaly(nr.sheet, nr.row_number, "ligne", nr.reg_raw,
                                     f"Aussi présent dans les retraits (ligne {rt.row_number}) : statut retiré retenu"))
        distinct = [p for rows in merged.values() for p in rows]
        if len(distinct) == 1:
            kept.append(distinct[0])
            continue
        kind = "doublon_divergent" if divergent else "double_feuille"
        s = distinct[0]
        cases.append(Case(f"{kind}:{s.sheet}:{s.row_number}", kind, s, None,
                          [Candidate(f"c{i}", None, p) for i, p in enumerate(distinct, start=1)]))
        kept.append(s)  # représentant
    kept.sort(key=lambda p: (p.sheet, p.row_number))
    return kept, anomalies, cases
