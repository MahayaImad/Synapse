"""Notation selon les cibles du cahier des charges (§ 8)."""
from __future__ import annotations

import re
import unicodedata

import pandas as pd
from rapidfuzz import fuzz

CIBLES = {
    "imprimee": {"exact": 0.95},
    "manuscrite": {"exact": 0.85},
    "posologie": 0.90,
    "doses_inventees": 0,
}

_UNITES = {"COMPRIME": "CP", "COMPRIMES": "CP", "CPR": "CP", "CP": "CP", "GELULE": "GELULE", "GELULES": "GELULE",
           "GEL": "GELULE", "SACHET": "SACHET", "SACHETS": "SACHET", "ML": "ML", "MG": "MG", "G": "G",
           "GOUTTE": "GOUTTE", "GOUTTES": "GOUTTE", "GTT": "GOUTTE", "CUILLERE": "CUILLERE", "CUILLERES": "CUILLERE",
           "CAC": "CUILLERE_CAFE", "CUILLERE A CAFE": "CUILLERE_CAFE", "CAS": "CUILLERE_SOUPE",
           "CUILLERE A SOUPE": "CUILLERE_SOUPE", "BOUFFEE": "BOUFFEE", "BOUFFEES": "BOUFFEE", "SUPPO": "SUPPOSITOIRE",
           "SUPPOSITOIRE": "SUPPOSITOIRE", "APPLICATION": "APPLICATION", "AMPOULE": "AMPOULE", "AMP": "AMPOULE",
           "INJECTION": "INJECTION", "UI": "UI"}


def norm(s: str | None) -> str:
    if s is None:
        return ""
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c)).upper()
    return " ".join(re.sub(r"[^A-Z0-9/,.%]+", " ", s).split())


def norm_dosage(s: str | None) -> str:
    return norm(s).replace(" ", "").replace(",", ".")


def norm_unite(s: str | None) -> str:
    n = norm(s).rstrip(".")
    return _UNITES.get(n, n)


def norm_frequence(s: str | None) -> str:
    n = norm(s).replace(" ", "").replace("FOIS", "").replace("PARJOUR", "/J").replace("XJ", "/J")
    return n.replace("PAR", "/").replace("JOUR", "J")


def norm_duree(s: str | None) -> str:
    n = norm(s)
    n = re.sub(r"\bJOURS?\b", "J", n)
    n = re.sub(r"\bSEMAINES?\b", "SEM", n)
    return n.replace(" ", "")


def posologie_ok(attendu: dict, lue: dict) -> bool:
    def num(v):
        return None if v in (None, "") else float(v)
    return (num(attendu.get("dose_par_prise")) == num(lue.get("dose_par_prise"))
            and norm_unite(attendu.get("unite")) == norm_unite(lue.get("unite"))
            and norm_frequence(attendu.get("frequence")) == norm_frequence(lue.get("frequence"))
            and norm_duree(attendu.get("duree")) == norm_duree(lue.get("duree"))
            and norm(attendu.get("voie")) == norm(lue.get("voie")))


def apparier(attendues: list, lues: list, seuil: int = 60) -> list[tuple[int, int | None]]:
    """Associe chaque ligne attendue à la ligne lue la plus proche (marque vs nom lu), sans réutilisation."""
    paires, prises = [], set()
    scores = sorted(((fuzz.WRatio(norm(a.marque), norm(l.nom_lu or l.texte_brut)), i, j)
                     for i, a in enumerate(attendues) for j, l in enumerate(lues)), reverse=True)
    vues = set()
    for s, i, j in scores:
        if s < seuil or i in vues or j in prises:
            continue
        paires.append((i, j))
        vues.add(i)
        prises.add(j)
    paires += [(i, None) for i in range(len(attendues)) if i not in vues]
    return sorted(paires)


def verdict_produit(attendu, produit_choisi: dict | None) -> str:
    """exact | incertain | erreur — une erreur (mauvais produit avec assurance) est le pire cas."""
    if produit_choisi is None:
        return "incertain"
    if attendu.produit_id:
        return "exact" if produit_choisi["id"] == attendu.produit_id else "erreur"
    same = (norm(produit_choisi["marque"]) == norm(attendu.marque)
            and norm_dosage(produit_choisi["dosage"]) == norm_dosage(attendu.dosage)
            and (not attendu.forme or norm(attendu.forme) in norm(produit_choisi["forme"])))
    return "exact" if same else "erreur"


def synthese(lignes: pd.DataFrame, ordonnances: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par moteur × type d'ordonnance, comparée aux cibles."""
    rows = []
    for (moteur, typ), g in lignes.groupby(["moteur", "type"]):
        o = ordonnances[(ordonnances.moteur == moteur) & (ordonnances.type == typ)]
        n = len(g)
        appariees = g[g.verdict != "manquee"]
        rows.append({
            "moteur": moteur, "type": typ, "lignes": n,
            "exact": (g.verdict == "exact").mean() if n else float("nan"),
            "incertain": g.verdict.isin(["incertain", "manquee"]).mean() if n else float("nan"),
            "erreur": (g.verdict == "erreur").mean() if n else float("nan"),
            "posologie_ok": appariees.posologie_ok.mean() if len(appariees) else float("nan"),
            "doses_inventees": int(g.dose_inventee.sum()) + int(o.lignes_inventees_dose.sum()),
            "lignes_inventees": int(o.lignes_inventees.sum()),
            "echecs_lecture": int(o.erreur.notna().sum()),
            "s_moyenne": o.secondes.mean(),
            "s_p95": o.secondes.quantile(0.95) if len(o) else float("nan"),
            "cible_exact": CIBLES[typ]["exact"],
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["atteint"] = ((df.exact >= df.cible_exact) & (df.posologie_ok >= CIBLES["posologie"])
                         & (df.doses_inventees == 0) & (df.erreur == 0))
    return df
