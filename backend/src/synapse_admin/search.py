"""Recherche hors connexion dans le fichier SQLite publié (référence pour l'app)."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .normalize import strip_accents

STATUS_RANK = {"en_vigueur": 0, "non_renouvele": 1, "retire": 2}
_ORDER = "CASE p.statut WHEN 'en_vigueur' THEN 0 WHEN 'non_renouvele' THEN 1 ELSE 2 END"
MAX_TOKENS = 8
TRIGRAM_CANDIDATES = 400
TRIGRAM_MIN_SIMILARITY = 0.5  # coefficient de Dice sur les trigrammes


@dataclass
class SearchHit:
    product_id: str
    marque: str
    dci: str
    forme: str
    dosage: str
    conditionnement: str
    statut: str


_ELISION = re.compile(r"\b[LDJCMNST]['’]")


def _tokens(query: str) -> list[str]:
    text = _ELISION.sub(" ", strip_accents(query).upper())
    return re.findall(r"[A-Z0-9]+", text)[:MAX_TOKENS]


def _trigrams(text: str) -> set[str]:
    t = re.sub(r"[^A-Z0-9]", "", strip_accents(text).upper())
    return {t[i:i + 3] for i in range(len(t) - 2)}


def _hit(r) -> SearchHit:
    return SearchHit(r["id"], r["marque"], r["dci"], r["forme"], r["dosage"], r["conditionnement"], r["statut"])


def search(db_path: Path, query: str, limit: int = 20) -> list[SearchHit]:
    tokens = _tokens(query)
    if not tokens:
        return []
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        fts = " ".join(f'"{t}"*' for t in tokens)
        rows = con.execute(
            f"SELECT p.*, bm25(produit_fts) AS score FROM produit_fts JOIN produit p ON p.rowid = produit_fts.rowid "
            f"WHERE produit_fts MATCH ? ORDER BY {_ORDER}, score, p.rowid LIMIT ?", (fts, limit)).fetchall()
        hits = [_hit(r) for r in rows]
        compact = "".join(tokens)
        if len(hits) < limit and len(compact) >= 4:
            hits += _fuzzy(con, compact, limit - len(hits), {h.product_id for h in hits})
        return hits
    finally:
        con.close()


def _fuzzy(con: sqlite3.Connection, compact: str, limit: int, seen: set[str]) -> list[SearchHit]:
    """Fautes de frappe : candidats partageant des trigrammes avec la requête, triés par similarité."""
    grams = sorted(_trigrams(compact))
    if not grams:
        return []
    rows = con.execute(
        "SELECT p.* FROM marque_trgm JOIN produit p ON p.rowid = marque_trgm.rowid WHERE marque_trgm MATCH ? "
        "ORDER BY bm25(marque_trgm), marque_trgm.rowid LIMIT ?", (" OR ".join(f'"{g}"' for g in grams), TRIGRAM_CANDIDATES)).fetchall()
    q = set(grams)
    scored = []
    for r in rows:
        if r["id"] in seen:
            continue
        g = _trigrams(r["marque"])
        sim = 2 * len(q & g) / (len(q) + len(g)) if g else 0.0
        if sim >= TRIGRAM_MIN_SIMILARITY:
            scored.append((STATUS_RANK.get(r["statut"], 3), -sim, r))
    scored.sort(key=lambda x: (x[1], x[0]))
    return [_hit(r) for _, _, r in scored[:limit]]
