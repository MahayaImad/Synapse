"""Liaison à la nomenclature : la recherche hors connexion de Synapse propose des candidats réels,
le modèle choisit l'un d'eux ou répond « incertain » (jamais un produit hors de la liste)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz
from synapse_admin.search import SearchHit, search

from .schema import LigneLue

MAX_CANDIDATS = 10


@dataclass
class Liaison:
    candidats: list[SearchHit]
    produit_id: str | None  # None = incertain
    raison: str
    hors_liste: bool = False  # le modèle a répondu une référence inexistante (comptée comme incertain)
    erreur: str | None = None
    secondes: float = 0.0


_QTE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(MG|G|UG|ΜG|MCG|µG|UI|ML|%)?")
_MG = {"G": 1000.0, "MG": 1.0, "UG": 0.001, "ΜG": 0.001, "MCG": 0.001, "µG": 0.001}


def quantites(dosage: str | None) -> list[tuple[float, str]]:
    """« 1g » → [(1000, 'MG')] ; « 1G/125MG » → [(1000, 'MG'), (125, 'MG')] ; les autres unités restent telles quelles."""
    out = []
    for n, u in _QTE.findall((dosage or "").upper()):
        v = float(n.replace(",", "."))
        u = u or "MG"
        out.append((v * _MG[u], "MG") if u in _MG else (v, u))
    return out


def score_candidat(ligne: LigneLue, h: SearchHit) -> float:
    nom = fuzz.WRatio(ligne.nom_lu or "", h.marque)
    lu, nomen = quantites(ligne.dosage_lu), quantites(h.dosage)
    dosage = 30 if lu and nomen and lu[0] == nomen[0] else 0
    return nom + dosage


def candidats(db: Path, ligne: LigneLue) -> list[SearchHit]:
    """Réservoir de candidats par le nom (la recherche n'indexe pas le dosage), classés par nom puis dosage."""
    if not ligne.nom_lu or ligne.lisibilite == "illisible":
        return []
    requetes = [f"{ligne.nom_lu} {ligne.dosage_lu or ''}".strip(), ligne.nom_lu, ligne.nom_lu.split()[0]]
    pool: dict[str, SearchHit] = {}
    for q in requetes:
        for h in search(db, q, limit=30):
            pool.setdefault(h.product_id, h)
    classes = sorted(pool.values(), key=lambda h: -score_candidat(ligne, h))
    return classes[:MAX_CANDIDATS]


def texte_candidats(hits: list[SearchHit]) -> str:
    return "\n".join(f"p{i} — {h.marque} | {h.dosage} | {h.forme} | {h.conditionnement} | {h.dci} | {h.statut}"
                     for i, h in enumerate(hits, 1))


def texte_ligne(ligne: LigneLue) -> str:
    p = ligne.posologie
    return (f"texte : {ligne.texte_brut}\nnom lu : {ligne.nom_lu}\ndosage lu : {ligne.dosage_lu}\n"
            f"forme lue : {ligne.forme_lue}\nlisibilité : {ligne.lisibilite}\n"
            f"posologie : {p.dose_par_prise} {p.unite or ''}, {p.frequence or '?'}, {p.duree or '?'}")


def lier(engine, db: Path, ligne: LigneLue) -> Liaison:
    hits = candidats(db, ligne)
    if not hits:
        return Liaison([], None, "aucun candidat dans la nomenclature")
    choix, secondes, erreur = engine.choose(texte_ligne(ligne), texte_candidats(hits))
    if choix is None:
        return Liaison(hits, None, "", erreur=erreur, secondes=secondes)
    ref = choix.choix.strip().lower()
    if ref == "incertain":
        return Liaison(hits, None, choix.raison, secondes=secondes)
    if ref.startswith("p") and ref[1:].isdigit() and 1 <= int(ref[1:]) <= len(hits):
        return Liaison(hits, hits[int(ref[1:]) - 1].product_id, choix.raison, secondes=secondes)
    return Liaison(hits, None, choix.raison, hors_liste=True, secondes=secondes)
