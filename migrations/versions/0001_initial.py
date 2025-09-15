"""initial empty revision

Revision ID: 0001_initial
Revises: 
Create Date: 2025-09-15 00:00:00

"""
from alembic import op  # noqa
import sqlalchemy as sa  # noqa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

