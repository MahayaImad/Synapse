"""Export du fichier SQLite embarqué par l'app et de son manifeste."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from .model import Product

SCHEMA = """
CREATE TABLE produit (
    id TEXT NOT NULL UNIQUE,
    marque TEXT NOT NULL, dci TEXT NOT NULL, code_dci TEXT NOT NULL, forme TEXT NOT NULL, dosage TEXT NOT NULL,
    conditionnement TEXT NOT NULL, liste TEXT, statut TEXT NOT NULL, origine TEXT, date_retrait TEXT,
    type_retrait TEXT, motif_retrait TEXT, labo TEXT NOT NULL, pays TEXT NOT NULL, type TEXT,
    hopital INTEGER NOT NULL, officine INTEGER NOT NULL, n_enregistrement TEXT NOT NULL
);
CREATE TABLE meta (cle TEXT PRIMARY KEY, valeur TEXT NOT NULL);
CREATE VIRTUAL TABLE produit_fts USING fts5(
    marque, dci, code_dci, labo, content='produit', content_rowid='rowid', tokenize="unicode61 remove_diacritics 2"
);
CREATE VIRTUAL TABLE marque_trgm USING fts5(
    marque, content='produit', content_rowid='rowid', tokenize='trigram'
);
"""


def _row(pid: UUID, p: Product) -> tuple:
    return (str(pid), p.brand, p.dci, p.dci_code, p.form, p.dosage, p.packaging, p.liste, p.sheet, p.origin,
            p.withdrawal_date.isoformat() if p.withdrawal_date else None, p.withdrawal_kind or None,
            p.withdrawal_reason or None, p.lab, p.country, p.type, int(p.hospital), int(p.pharmacy), p.reg_raw)


def export_sqlite(products: list[tuple[UUID, Product]], meta: dict[str, str], out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"nomenclature-{meta['version']}.sqlite"
    tmp = target.with_suffix(".sqlite.tmp")
    tmp.unlink(missing_ok=True)
    published_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con = sqlite3.connect(tmp)
    try:
        con.executescript(SCHEMA)
        con.executemany("INSERT INTO produit VALUES (" + ",".join("?" * 19) + ")", [_row(i, p) for i, p in products])
        con.execute("INSERT INTO produit_fts(produit_fts) VALUES('rebuild')")
        con.execute("INSERT INTO marque_trgm(marque_trgm) VALUES('rebuild')")
        con.executemany("INSERT INTO meta VALUES (?, ?)",
                        sorted({**meta, "published_at": published_at, "products": str(len(products))}.items()))
        con.commit()
        con.execute("VACUUM")
    finally:
        con.close()
    tmp.replace(target)
    data = target.read_bytes()
    manifest = {"version": meta["version"], "reference_date": meta.get("reference_date"), "file": target.name,
                "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "source_sha256": meta.get("source_sha256"), "published_at": published_at}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return target
