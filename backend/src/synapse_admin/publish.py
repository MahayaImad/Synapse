"""Application des décisions et publication d'une version."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import Connection, func, insert, select, update

from . import repository
from .db import decision, ecart, nomenclature_version, produit, produit_version
from .decisions import load_decisions
from .export import export_sqlite
from .importer import atomic
from .model import Product


class PublishRefused(Exception):
    pass


@dataclass
class PublishSummary:
    label: str
    products: int
    decisions: int
    sqlite_path: Path | None = None


def _set_produit(conn: Connection, pv_id: int, produit_id: UUID | None) -> None:
    conn.execute(update(produit_version).where(produit_version.c.id == pv_id).values(produit_id=produit_id))


def apply_and_publish(conn: Connection, label: str, decisions_path: Path, out_dir: Path | None = None) -> PublishSummary:
    with atomic(conn):
        version = repository.find_version(conn, label)
        if version is None:
            raise PublishRefused(f"Version {label} inconnue")
        if version.state != "brouillon":
            raise PublishRefused(f"La version {label} est {version.state} : seule une version brouillon se publie")
        draft = repository.load_draft(conn, label)
        decisions = load_decisions(decisions_path, draft)

        rows = {r.case_id: r for r in conn.execute(select(ecart).where(
            ecart.c.version_id == version.id, ecart.c.category == "a_trancher"))}
        # Les choix « garder » s'appliquent en dernier : la ligne gardée hérite de l'identifiant du représentant.
        for d in sorted(decisions, key=lambda d: d.choice.startswith("garder:")):
            row = rows[d.case_id]
            action, _, ref = d.choice.partition(":")
            candidates = {k["ref"]: k for k in row.candidates}
            if action == "meme_produit":
                _set_produit(conn, row.new_pv_id, UUID(candidates[ref]["produit_id"]))
            elif action in ("nouveau", "nouveau_et_disparu"):
                _set_produit(conn, row.new_pv_id, uuid4())
            elif action == "garder":
                kept_pv, rep_pv = candidates[ref]["pv_id"], candidates["c1"]["pv_id"]
                rep_id = conn.execute(select(produit_version.c.produit_id).where(produit_version.c.id == rep_pv)).scalar()
                if kept_pv != rep_pv:
                    _set_produit(conn, rep_pv, None)
                _set_produit(conn, kept_pv, rep_id or uuid4())
            # disparu : rien à publier

        dup = conn.execute(select(produit_version.c.produit_id).where(
            produit_version.c.version_id == version.id, produit_version.c.produit_id.is_not(None))
            .group_by(produit_version.c.produit_id).having(func.count() > 1)).scalars().all()
        if dup:
            raise PublishRefused(f"Identifiant produit attribué à plusieurs lignes : {', '.join(map(str, dup))}")

        existing = select(produit.c.id)
        new_ids = conn.execute(select(produit_version.c.produit_id).where(
            produit_version.c.version_id == version.id, produit_version.c.produit_id.is_not(None),
            produit_version.c.produit_id.not_in(existing))).scalars().all()
        if new_ids:
            conn.execute(insert(produit), [{"id": i, "created_in_version": version.id} for i in new_ids])
        if decisions:
            conn.execute(insert(decision), [dict(version_id=version.id, case_id=d.case_id, choice=d.choice,
                                                 decided_by=d.decided_by, decided_at=d.decided_at) for d in decisions])
        conn.execute(update(nomenclature_version).where(nomenclature_version.c.state == "publiee")
                     .values(state="remplacee"))
        conn.execute(update(nomenclature_version).where(nomenclature_version.c.id == version.id)
                     .values(state="publiee", published_at=func.now()))
        count = len(published_products(conn, label))
    summary = PublishSummary(label, count, len(decisions))
    if out_dir is not None:
        summary.sqlite_path = export_version(conn, label, out_dir)
    return summary


def export_version(conn: Connection, label: str, out_dir: Path) -> Path:
    """(Re)génère le fichier SQLite et le manifeste d'une version publiée."""
    version = repository.find_version(conn, label)
    if version is None or version.state == "brouillon":
        raise PublishRefused(f"La version {label} n'est pas publiée")
    meta = {"version": label, "reference_date": version.reference_date.isoformat(),
            "source_sha256": version.source_sha256, "source_filename": version.source_filename}
    # Seule la version en vigueur met à jour le manifeste lu par l'app.
    return export_sqlite(published_products(conn, label), meta, out_dir, write_manifest=version.state == "publiee")


def published_products(conn: Connection, label: str) -> list[tuple[UUID, Product]]:
    version = repository.find_version(conn, label)
    if version is None:
        raise LookupError(f"Version {label} inconnue")
    rows = conn.execute(select(produit_version).where(produit_version.c.version_id == version.id,
                                                      produit_version.c.produit_id.is_not(None))
                        .order_by(produit_version.c.id))
    return [(r.produit_id, repository.product_from_row(r)) for r in rows]
