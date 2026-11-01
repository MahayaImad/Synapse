"""Schéma initial de la nomenclature.

Revision ID: 0001
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.create_table(
        "nomenclature_version",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("label", sa.Text, nullable=False, unique=True),
        sa.Column("reference_date", sa.Date, nullable=False),
        sa.Column("source_filename", sa.Text, nullable=False),
        sa.Column("source_sha256", sa.Text, nullable=False),
        sa.Column("state", sa.Text, nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("state in ('brouillon','publiee','remplacee')", name="ck_version_state"),
    )
    op.create_table(
        "produit",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_in_version", sa.Integer, sa.ForeignKey("nomenclature_version.id"), nullable=False),
    )
    op.create_table(
        "produit_version",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("version_id", sa.Integer, sa.ForeignKey("nomenclature_version.id", ondelete="CASCADE"), nullable=False),
        sa.Column("produit_id", UUID(as_uuid=True)),
        sa.Column("sheet", sa.Text, nullable=False),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("reg_raw", sa.Text, nullable=False),
        sa.Column("dci_code", sa.Text, nullable=False),
        sa.Column("dci", sa.Text, nullable=False),
        sa.Column("brand", sa.Text, nullable=False),
        sa.Column("form", sa.Text, nullable=False),
        sa.Column("dosage", sa.Text, nullable=False),
        sa.Column("packaging", sa.Text, nullable=False),
        sa.Column("liste", sa.Text),
        sa.Column("hospital", sa.Boolean, nullable=False),
        sa.Column("pharmacy", sa.Boolean, nullable=False),
        sa.Column("type", sa.Text),
        sa.Column("origin", sa.Text),
        sa.Column("lab", sa.Text, nullable=False),
        sa.Column("country", sa.Text, nullable=False),
        sa.Column("initial_date", sa.Date),
        sa.Column("final_date", sa.Date),
        sa.Column("stability", sa.Text, nullable=False),
        sa.Column("obs", sa.Text, nullable=False),
        sa.Column("withdrawal_date", sa.Date),
        sa.Column("withdrawal_reason", sa.Text, nullable=False),
        sa.Column("withdrawal_kind", sa.Text, nullable=False),
        sa.Column("raw", JSONB, nullable=False),
    )
    op.create_index("ix_pv_version", "produit_version", ["version_id"])
    op.create_index("ix_pv_brand_trgm", "produit_version", ["brand"], postgresql_using="gin",
                    postgresql_ops={"brand": "gin_trgm_ops"})
    op.create_index("ix_pv_dci_trgm", "produit_version", ["dci"], postgresql_using="gin",
                    postgresql_ops={"dci": "gin_trgm_ops"})
    op.create_table(
        "ecart",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("version_id", sa.Integer, sa.ForeignKey("nomenclature_version.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("tier", sa.Integer),
        sa.Column("produit_id", UUID(as_uuid=True)),
        sa.Column("old_pv_id", sa.Integer, sa.ForeignKey("produit_version.id")),
        sa.Column("new_pv_id", sa.Integer, sa.ForeignKey("produit_version.id", ondelete="CASCADE")),
        sa.Column("changed_fields", sa.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("case_id", sa.Text),
        sa.Column("case_kind", sa.Text),
        sa.Column("candidates", JSONB),
        sa.CheckConstraint("category in ('nouveau','disparu','statut','modifie','inchange','a_trancher')",
                           name="ck_ecart_category"),
    )
    op.create_index("ix_ecart_version", "ecart", ["version_id"])
    op.create_table(
        "decision",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("version_id", sa.Integer, sa.ForeignKey("nomenclature_version.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", sa.Text, nullable=False),
        sa.Column("choice", sa.Text, nullable=False),
        sa.Column("decided_by", sa.Text, nullable=False),
        sa.Column("decided_at", sa.Date, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "anomalie",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("version_id", sa.Integer, sa.ForeignKey("nomenclature_version.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sheet", sa.Text, nullable=False),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("field", sa.Text, nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
    )


def downgrade() -> None:
    for t in ("anomalie", "decision", "ecart", "produit_version", "produit", "nomenclature_version"):
        op.drop_table(t)
