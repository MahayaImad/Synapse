"""Rapprochement par paliers entre la version publiée et la nouvelle version."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, fields
from typing import Literal
from uuid import UUID

from rapidfuzz import fuzz

from .model import CLINICAL_FIELDS, NON_COMPARED_FIELDS, Candidate, Case, Product

# Ressemblance minimale des marques pour proposer un changement de titulaire (rapidfuzz fuzz.ratio, 0-100).
BRAND_SIMILARITY_THRESHOLD = 85

GapCategory = Literal["nouveau", "disparu", "statut", "modifie", "inchange"]


@dataclass
class PreviousProduct:
    product_id: UUID
    product: Product
    pv_id: int | None = None  # ligne produit_version d'origine, quand elle vient de la base


@dataclass
class Gap:
    category: GapCategory
    tier: int | None
    product_id: UUID | None
    old: Product | None
    new: Product | None
    changed_fields: list[str]


@dataclass
class MatchResult:
    gaps: list[Gap]
    cases: list[Case]


_COMPARED = [f.name for f in fields(Product) if f.name not in NON_COMPARED_FIELDS]


def changed_fields(old: Product, new: Product) -> list[str]:
    return [name for name in _COMPARED if getattr(old, name) != getattr(new, name)]


def _new_case_id(kind: str, p: Product) -> str:
    return f"{kind}:{p.sheet}:{p.row_number}"


def match_versions(previous: list[PreviousProduct], new: list[Product]) -> MatchResult:
    gaps: list[Gap] = []
    cases: list[Case] = []
    old_left: dict[int, PreviousProduct] = {i: o for i, o in enumerate(previous)}
    new_left: dict[int, Product] = {i: n for i, n in enumerate(new)}
    in_case: set[int] = set()  # anciens produits déjà proposés comme candidats

    def pair(oi: int, ni: int, tier: int) -> None:
        o, n = old_left.pop(oi), new_left.pop(ni)
        diff = changed_fields(o.product, n)
        if any(f in diff for f in CLINICAL_FIELDS):
            cases.append(Case(_new_case_id("champ_clinique", n), "champ_clinique", n, None,
                              [Candidate("c1", o.product_id, o.product)]))
            in_case.add(oi)
            return
        if o.product.sheet != n.sheet:
            category = "statut"
        else:
            category = "modifie" if diff else "inchange"
        gaps.append(Gap(category, tier, o.product_id, o.product, n, diff))

    # Paliers 1 et 2 : clé exacte.
    for tier, key in ((1, lambda p: (p.reg_raw, p.presentation_key)),
                      (2, lambda p: (p.stem, p.presentation_key) if p.stem else None)):
        index: dict[tuple, list[int]] = defaultdict(list)
        for oi, o in old_left.items():
            k = key(o.product)
            if k is not None:
                index[k].append(oi)
        for ni, n in list(new_left.items()):
            k = key(n)
            if k is not None and index.get(k):
                pair(index[k].pop(0), ni, tier)

    # Palier 3 : même racine.
    olds_by_stem: dict[tuple, list[int]] = defaultdict(list)
    news_by_stem: dict[tuple, list[int]] = defaultdict(list)
    for oi, o in old_left.items():
        if o.product.stem:
            olds_by_stem[o.product.stem].append(oi)
    for ni, n in new_left.items():
        if n.stem:
            news_by_stem[n.stem].append(ni)
    for stem, nis in news_by_stem.items():
        ois = olds_by_stem.get(stem, [])
        if not ois:
            continue
        if len(ois) == 1 and len(nis) == 1:
            pair(ois[0], nis[0], 3)
            continue
        candidates = [Candidate(f"c{i}", old_left[oi].product_id, old_left[oi].product) for i, oi in enumerate(ois, 1)]
        for ni in nis:
            n = new_left.pop(ni)
            cases.append(Case(_new_case_id("candidats_multiples", n), "candidats_multiples", n, None, list(candidates)))
        in_case.update(ois)

    # Palier 4 : changement de titulaire probable.
    for ni, n in list(new_left.items()):
        matches = [oi for oi, o in old_left.items()
                   if o.product.dci_code == n.dci_code and o.product.dosage == n.dosage and o.product.lab != n.lab
                   and fuzz.ratio(o.product.brand, n.brand) >= BRAND_SIMILARITY_THRESHOLD]
        if matches:
            new_left.pop(ni)
            cases.append(Case(_new_case_id("changement_titulaire", n), "changement_titulaire", n, None,
                              [Candidate(f"c{i}", old_left[oi].product_id, old_left[oi].product)
                               for i, oi in enumerate(matches, 1)]))
            in_case.update(matches)

    # Palier 5 : nouveaux et disparus.
    for n in new_left.values():
        gaps.append(Gap("nouveau", None, None, None, n, []))
    for oi, o in old_left.items():
        if oi in in_case:
            continue  # sort de l'un des cas ; non retenu à la publication = disparu
        if o.product.sheet == "en_vigueur":
            cases.append(Case(f"disparu_sans_retrait:{o.product_id}", "disparu_sans_retrait", None, o.product_id, []))
        else:
            gaps.append(Gap("disparu", None, o.product_id, o.product, None, []))
    return MatchResult(gaps, cases)
