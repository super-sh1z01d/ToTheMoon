"""add status_updated_at to tokens

Revision ID: 0003_add_status_updated_at
Revises: 0002_schema
Create Date: 2025-09-15 00:30:00

"""
from alembic import op
import sqlalchemy as sa


revision = "0003_add_status_updated_at"
down_revision = "0002_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tokens",
        sa.Column("status_updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tokens", "status_updated_at")

