"""Lecture/écriture des versions de nomenclature dans PostgreSQL."""
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Connection, delete, insert, select

from .db import anomalie, decision, ecart, nomenclature_version, produit_version
from .matching import Gap, MatchResult, PreviousProduct
from .model import Anomaly, Candidate, Case, Product
from .regnum import parse_registration

_PRODUCT_COLUMNS = [f.name for f in fields(Product) if f.name != "registration"]


@dataclass
class VersionRow:
    id: int
    label: str
    reference_date: date
    source_filename: str
    source_sha256: str
    state: str
    imported_at: datetime
    published_at: datetime | None


@dataclass
class Draft:
    version: VersionRow
    gaps: list[Gap]
    cases: list[Case]
    anomalies: list[Anomaly]


def _version(row) -> VersionRow:
    return VersionRow(**{k: row._mapping[k] for k in VersionRow.__dataclass_fields__})


def product_from_row(row) -> Product:
    m = row._mapping
    values = {k: m[k] for k in _PRODUCT_COLUMNS}
    return Product(registration=parse_registration(values["reg_raw"]), **values)


def find_version(conn: Connection, label: str) -> VersionRow | None:
    row = conn.execute(select(nomenclature_version).where(nomenclature_version.c.label == label)).first()
    return _version(row) if row else None


def list_versions(conn: Connection) -> list[VersionRow]:
    rows = conn.execute(select(nomenclature_version).order_by(nomenclature_version.c.reference_date))
    return [_version(r) for r in rows]


def latest_published(conn: Connection) -> tuple[VersionRow, list[PreviousProduct]] | None:
    row = conn.execute(select(nomenclature_version).where(nomenclature_version.c.state == "publiee")
                       .order_by(nomenclature_version.c.reference_date.desc()).limit(1)).first()
    if row is None:
        return None
    version = _version(row)
    rows = conn.execute(select(produit_version).where(produit_version.c.version_id == version.id,
                                                      produit_version.c.produit_id.is_not(None))
                        .order_by(produit_version.c.id))
    return version, [PreviousProduct(r.produit_id, product_from_row(r), r.id) for r in rows]


def _insert_pv(conn: Connection, version_id: int, p: Product, produit_id: UUID | None) -> int:
    values = {k: getattr(p, k) for k in _PRODUCT_COLUMNS}
    return conn.execute(insert(produit_version).values(version_id=version_id, produit_id=produit_id, **values)
                        .returning(produit_version.c.id)).scalar_one()


def save_draft(conn: Connection, label: str, reference_date: date, filename: str, sha256: str,
               products: list[Product], anomalies: list[Anomaly], match: MatchResult,
               consolidation_cases: list[Case], previous: list[PreviousProduct] = ()) -> int:
    vid = conn.execute(insert(nomenclature_version).values(
        label=label, reference_date=reference_date, source_filename=filename, source_sha256=sha256, state="brouillon",
    ).returning(nomenclature_version.c.id)).scalar_one()

    old_pv = {id(p.product): p.pv_id for p in previous}  # Product de la version publiée -> sa ligne
    prev_pv = {p.product_id: p.pv_id for p in previous}
    new_ids: dict[int, UUID | None] = {}  # id(Product) -> produit_id
    for g in match.gaps:
        if g.new is not None:
            new_ids[id(g.new)] = g.product_id if g.product_id else uuid4()
    pv_of: dict[int, int] = {}
    for p in products:
        pv_of[id(p)] = _insert_pv(conn, vid, p, new_ids.get(id(p)))
    for c in consolidation_cases:
        for k in c.candidates:
            if id(k.product) not in pv_of:
                pv_of[id(k.product)] = _insert_pv(conn, vid, k.product, None)

    rows = []
    for g in match.gaps:
        rows.append(dict(version_id=vid, category=g.category, tier=g.tier,
                         produit_id=new_ids[id(g.new)] if g.new is not None else g.product_id,
                         old_pv_id=old_pv.get(id(g.old)) if g.old is not None else None, new_pv_id=pv_of.get(id(g.new)) if g.new else None,
                         changed_fields=g.changed_fields, case_id=None, case_kind=None, candidates=None))
    for c in list(match.cases) + list(consolidation_cases):
        rows.append(dict(version_id=vid, category="a_trancher", tier=None, produit_id=c.subject_product_id,
                         old_pv_id=None, new_pv_id=pv_of.get(id(c.subject)) if c.subject else None, changed_fields=[],
                         case_id=c.case_id, case_kind=c.kind,
                         candidates=[{"ref": k.ref, "produit_id": str(k.product_id) if k.product_id else None,
                                      "pv_id": pv_of.get(id(k.product)) or prev_pv.get(k.product_id)}
                                     for k in c.candidates]))
    if rows:
        conn.execute(insert(ecart), rows)
    if anomalies:
        conn.execute(insert(anomalie), [dict(version_id=vid, sheet=a.sheet, row_number=a.row_number, field=a.field,
                                             value=a.value, message=a.message) for a in anomalies])
    return vid


def load_draft(conn: Connection, label: str) -> Draft:
    version = find_version(conn, label)
    if version is None:
        raise LookupError(f"Version {label} inconnue")
    pvs = {r.id: r for r in conn.execute(select(produit_version).where(
        produit_version.c.version_id == version.id))}
    ecarts = conn.execute(select(ecart).where(ecart.c.version_id == version.id).order_by(ecart.c.id)).all()
    old_ids = {e.old_pv_id for e in ecarts if e.old_pv_id} | {
        k["pv_id"] for e in ecarts if e.candidates for k in e.candidates if k["pv_id"]}
    missing = old_ids - pvs.keys()
    if missing:
        pvs.update({r.id: r for r in conn.execute(select(produit_version).where(produit_version.c.id.in_(missing)))})

    def prod(pv_id):
        return product_from_row(pvs[pv_id]) if pv_id else None

    gaps, cases = [], []
    for e in ecarts:
        if e.category == "a_trancher":
            cases.append(Case(e.case_id, e.case_kind, prod(e.new_pv_id), e.produit_id,
                              [Candidate(k["ref"], UUID(k["produit_id"]) if k["produit_id"] else None, prod(k["pv_id"]))
                               for k in e.candidates]))
        else:
            gaps.append(Gap(e.category, e.tier, e.produit_id, prod(e.old_pv_id), prod(e.new_pv_id), list(e.changed_fields)))
    anomalies = [Anomaly(r.sheet, r.row_number, r.field, r.value, r.message) for r in conn.execute(
        select(anomalie).where(anomalie.c.version_id == version.id).order_by(anomalie.c.id))]
    return Draft(version, gaps, cases, anomalies)


def delete_draft(conn: Connection, label: str) -> None:
    version = find_version(conn, label)
    if version is None:
        return
    if version.state != "brouillon":
        raise ValueError(f"La version {label} est {version.state} : seule une version brouillon peut être supprimée")
    for t in (decision, anomalie, ecart, produit_version):
        conn.execute(delete(t).where(t.c.version_id == version.id))
    conn.execute(delete(nomenclature_version).where(nomenclature_version.c.id == version.id))
