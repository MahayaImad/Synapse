"""Schéma PostgreSQL (SQLAlchemy Core) et connexion."""
from __future__ import annotations

import os

from sqlalchemy import (ARRAY, Boolean, CheckConstraint, Column, Date, DateTime, Engine, ForeignKey, Index, Integer,
                        MetaData, Table, Text, create_engine, func)
from sqlalchemy.dialects.postgresql import JSONB, UUID

DEFAULT_URL = "postgresql+psycopg://synapse:synapse@localhost:5432/synapse"

metadata = MetaData()

nomenclature_version = Table(
    "nomenclature_version", metadata,
    Column("id", Integer, primary_key=True),
    Column("label", Text, nullable=False, unique=True),
    Column("reference_date", Date, nullable=False),
    Column("source_filename", Text, nullable=False),
    Column("source_sha256", Text, nullable=False),
    Column("state", Text, nullable=False),
    Column("imported_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("published_at", DateTime(timezone=True)),
    CheckConstraint("state in ('brouillon','publiee','remplacee')", name="ck_version_state"),
)

produit = Table(
    "produit", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("created_in_version", Integer, ForeignKey("nomenclature_version.id"), nullable=False),
)

produit_version = Table(
    "produit_version", metadata,
    Column("id", Integer, primary_key=True),
    Column("version_id", Integer, ForeignKey("nomenclature_version.id", ondelete="CASCADE"), nullable=False),
    Column("produit_id", UUID(as_uuid=True)),
    Column("sheet", Text, nullable=False),
    Column("row_number", Integer, nullable=False),
    Column("reg_raw", Text, nullable=False),
    Column("dci_code", Text, nullable=False),
    Column("dci", Text, nullable=False),
    Column("brand", Text, nullable=False),
    Column("form", Text, nullable=False),
    Column("dosage", Text, nullable=False),
    Column("packaging", Text, nullable=False),
    Column("liste", Text),
    Column("hospital", Boolean, nullable=False),
    Column("pharmacy", Boolean, nullable=False),
    Column("type", Text),
    Column("origin", Text),
    Column("lab", Text, nullable=False),
    Column("country", Text, nullable=False),
    Column("initial_date", Date),
    Column("final_date", Date),
    Column("stability", Text, nullable=False),
    Column("obs", Text, nullable=False),
    Column("withdrawal_date", Date),
    Column("withdrawal_reason", Text, nullable=False),
    Column("withdrawal_kind", Text, nullable=False),
    Column("raw", JSONB, nullable=False),
    Index("ix_pv_version", "version_id"),
    Index("ix_pv_brand_trgm", "brand", postgresql_using="gin", postgresql_ops={"brand": "gin_trgm_ops"}),
    Index("ix_pv_dci_trgm", "dci", postgresql_using="gin", postgresql_ops={"dci": "gin_trgm_ops"}),
)

ecart = Table(
    "ecart", metadata,
    Column("id", Integer, primary_key=True),
    Column("version_id", Integer, ForeignKey("nomenclature_version.id", ondelete="CASCADE"), nullable=False),
    Column("category", Text, nullable=False),
    Column("tier", Integer),
    Column("produit_id", UUID(as_uuid=True)),
    Column("old_pv_id", Integer, ForeignKey("produit_version.id")),
    Column("new_pv_id", Integer, ForeignKey("produit_version.id", ondelete="CASCADE")),
    Column("changed_fields", ARRAY(Text), nullable=False, server_default="{}"),
    Column("case_id", Text),
    Column("case_kind", Text),
    Column("candidates", JSONB),
    Index("ix_ecart_version", "version_id"),
    CheckConstraint("category in ('nouveau','disparu','statut','modifie','inchange','a_trancher')", name="ck_ecart_category"),
)

decision = Table(
    "decision", metadata,
    Column("id", Integer, primary_key=True),
    Column("version_id", Integer, ForeignKey("nomenclature_version.id", ondelete="CASCADE"), nullable=False),
    Column("case_id", Text, nullable=False),
    Column("choice", Text, nullable=False),
    Column("decided_by", Text, nullable=False),
    Column("decided_at", Date, nullable=False),
    Column("recorded_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

anomalie = Table(
    "anomalie", metadata,
    Column("id", Integer, primary_key=True),
    Column("version_id", Integer, ForeignKey("nomenclature_version.id", ondelete="CASCADE"), nullable=False),
    Column("sheet", Text, nullable=False),
    Column("row_number", Integer, nullable=False),
    Column("field", Text, nullable=False),
    Column("value", Text, nullable=False),
    Column("message", Text, nullable=False),
)


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_URL)


def get_engine(url: str | None = None) -> Engine:
    return create_engine(url or database_url())
