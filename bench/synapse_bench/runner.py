"""Exécution d'un ou plusieurs moteurs sur le jeu d'essai, avec garde-fou d'anonymisation."""
from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .dataset import Ordonnance
from .images import prepare
from .linking import lier
from .scoring import apparier, posologie_ok, verdict_produit


class EnvoiRefuse(Exception):
    pass


def garde_fou(engine, o: Ordonnance) -> None:
    """Une image non anonymisée ne part jamais vers un moteur hors d'Algérie."""
    if engine.external and not o.anonymisee:
        raise EnvoiRefuse(f"{o.id} : aucun masque ni zone — envoi vers {engine.name} refusé")


def run(engines: list, ordonnances: list[Ordonnance], db: Path, results_dir: Path | None = None):
    """Renvoie (lignes, ordonnances, details) : deux DataFrames de notation et la trace complète par ordonnance."""
    lignes, ords, details = [], [], []
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for engine in engines:
        for o in ordonnances:
            base = {"moteur": engine.name, "ordonnance": o.id, "type": o.type}
            try:
                garde_fou(engine, o)
            except EnvoiRefuse as e:
                ords.append({**base, "secondes": 0.0, "erreur": str(e), "lignes_inventees": 0, "lignes_inventees_dose": 0})
                for a in o.lignes:
                    lignes.append({**base, "attendu": a.marque, "lu": None, "choisi": None, "verdict": "manquee",
                                   "posologie_ok": False, "dose_inventee": False})
                continue
            prep = prepare(o.image_path.read_bytes(), o.masques, o.zone)
            t = time.perf_counter()
            r = engine.read(prep.png)
            lues = r.lecture.lignes if r.lecture else []
            liaisons = [lier(engine, db, l) for l in lues]
            total = time.perf_counter() - t
            paires = apparier(o.lignes, lues)
            appariees = {j for _, j in paires if j is not None}
            inventees = [j for j in range(len(lues)) if j not in appariees]
            for i, j in paires:
                a = o.lignes[i]
                if j is None:
                    lignes.append({**base, "attendu": a.marque, "lu": None, "choisi": None, "verdict": "manquee",
                                   "posologie_ok": False, "dose_inventee": False})
                    continue
                l, li = lues[j], liaisons[j]
                choisi = next((h for h in li.candidats if h.product_id == li.produit_id), None)
                produit = None if choisi is None else {"id": choisi.product_id, "marque": choisi.marque,
                                                      "dosage": choisi.dosage, "forme": choisi.forme}
                lue_pos = l.posologie.model_dump()
                lignes.append({
                    **base, "attendu": f"{a.marque} {a.dosage or ''}".strip(), "lu": l.texte_brut,
                    "choisi": None if choisi is None else f"{choisi.marque} {choisi.dosage} {choisi.forme}",
                    "verdict": verdict_produit(a, produit), "raison": li.raison, "hors_liste": li.hors_liste,
                    "posologie_ok": posologie_ok(a.posologie, lue_pos),
                    "dose_inventee": a.posologie.get("dose_par_prise") is None and lue_pos["dose_par_prise"] is not None,
                })
            ords.append({**base, "secondes": total, "erreur": r.erreur,
                         "lignes_inventees": len(inventees),
                         "lignes_inventees_dose": sum(lues[j].posologie.dose_par_prise is not None for j in inventees)})
            details.append({**base, "lecture": r.lecture.model_dump() if r.lecture else None, "erreur": r.erreur,
                            "usage": r.usage, "secondes": total,
                            "liaisons": [{"candidats": [asdict(h) for h in li.candidats], "produit_id": li.produit_id,
                                          "raison": li.raison, "hors_liste": li.hors_liste, "erreur": li.erreur}
                                         for li in liaisons]})
    if results_dir is not None:
        results_dir = Path(results_dir)
        results_dir.mkdir(parents=True, exist_ok=True)
        with open(results_dir / f"run-{stamp}.jsonl", "w", encoding="utf-8") as f:
            for d in details:
                f.write(json.dumps(d, ensure_ascii=False, default=str) + "\n")
    cols_l = ["moteur", "ordonnance", "type", "attendu", "lu", "choisi", "verdict", "posologie_ok", "dose_inventee"]
    return (pd.DataFrame(lignes, columns=cols_l + ["raison", "hors_liste"]),
            pd.DataFrame(ords, columns=["moteur", "ordonnance", "type", "secondes", "erreur", "lignes_inventees",
                                        "lignes_inventees_dose"]),
            details)
