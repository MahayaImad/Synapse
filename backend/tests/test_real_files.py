"""Bout en bout sur les vrais fichiers du ministère.

Ignoré sauf si SYNAPSE_REAL_FILES désigne un répertoire contenant AAAA-MM.xlsx.
"""
import os
import random
import time
from collections import Counter
from pathlib import Path

import pytest
import yaml
from sqlalchemy import text

from synapse_admin import repository as repo
from synapse_admin.decisions import write_decisions_template
from synapse_admin.importer import run_import
from synapse_admin.publish import apply_and_publish, published_products
from synapse_admin.search import search

REAL = os.environ.get("SYNAPSE_REAL_FILES")
pytestmark = pytest.mark.skipif(not REAL, reason="SYNAPSE_REAL_FILES non défini")
LABELS = ["2024-08", "2024-12", "2026-04", "2026-06", "2026-08"]


def auto_decide(conn, path, label):
    """Aide de test uniquement : premier choix possible dont le candidat n'est pas déjà pris."""
    write_decisions_template(repo.load_draft(conn, label), path)
    d = yaml.safe_load(path.read_text())
    used = set()
    for c in d["cas"]:
        pid = {k["ref"]: k["produit_id"] for k in c["candidats"]}
        choice = next((ch for ch in c["choix_possibles"]
                       if not ch.startswith("meme_produit:") or pid[ch.split(":")[1]] not in used), "nouveau")
        if choice.startswith("meme_produit:"):
            used.add(pid[choice.split(":")[1]])
        c["choix"], c["par"], c["le"] = choice, "test", "2026-11-01"
    path.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False))
    return path


def test_five_real_versions_in_order(conn, tmp_path, capsys):
    summaries = {}
    for label in LABELS:
        f = Path(REAL) / f"{label}.xlsx"
        s = run_import(conn, f, label)
        draft = repo.load_draft(conn, label)
        vid = draft.version.id
        pv_rows = conn.execute(text("select count(*) from produit_version where version_id=:v"), {"v": vid}).scalar()
        merged = sum(1 for a in draft.anomalies if a.field == "ligne")
        assert s.rows_read == pv_rows + merged, label                       # aucune ligne perdue
        referenced = sum(1 for g in draft.gaps if g.new) + sum(1 for c in draft.cases if c.subject and c.kind != "double_feuille") \
            + sum(len(c.candidates) for c in draft.cases if c.kind == "double_feuille")
        assert referenced == pv_rows, label                                 # chaque ligne a un écart
        summaries[label] = (s.counts_by_category, Counter(c.kind for c in draft.cases), len(draft.anomalies))
        if label == "2026-08":
            titulaire = [c for c in draft.cases if c.kind == "changement_titulaire"]
            assert any(c.subject.brand == "COAGIL-VII" and c.candidates[0].product.brand == "GOAGIL-VII" for c in titulaire)
        apply_and_publish(conn, label, auto_decide(conn, tmp_path / f"{label}.yaml", label), tmp_path / "pub")
    with capsys.disabled():
        for label, (cats, cases, an) in summaries.items():
            print(f"\n{label}: {dict(cats)} | cas {dict(cases)} | anomalies {an}")

    path = tmp_path / "pub" / "nomenclature-2026-08.sqlite"
    brands = [p.brand for _, p in published_products(conn, "2026-08")]
    worst = 0.0
    for b in random.Random(3).sample(brands, 50):
        t = time.perf_counter()
        hits = search(path, b)
        worst = max(worst, time.perf_counter() - t)
        assert any(h.marque == b for h in hits), b
    with capsys.disabled():
        print(f"recherche : pire temps {worst * 1000:.0f} ms sur 50 marques, fichier {path.stat().st_size // 1024} Ko")
    assert worst < 0.3
