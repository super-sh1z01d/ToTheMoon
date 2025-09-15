"""create core schema

Revision ID: 0002_schema
Revises: 0001_initial
Create Date: 2025-09-15 00:10:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_schema"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tokenstatus = sa.Enum("Initial", "Active", "Archived", name="tokenstatus")
    tokenstatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tokens",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("address", sa.String(), nullable=False, unique=True),
        sa.Column("symbol", sa.String(), nullable=True),
        sa.Column("status", tokenstatus, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("activated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_score_value", sa.Float(), nullable=True),
    )
    op.create_index("ix_tokens_status", "tokens", ["status"]) 

    op.create_table(
        "pools",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("token_id", sa.BigInteger(), sa.ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pool_address", sa.String(), nullable=False, unique=True),
        sa.Column("dex_name", sa.String(), nullable=False),
    )
    op.create_index("ix_pools_token_id", "pools", ["token_id"]) 

    op.create_table(
        "token_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("token_id", sa.BigInteger(), sa.ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ts", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("holders", sa.Integer(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
    )
    op.create_index("ix_token_snapshots_token_ts", "token_snapshots", ["token_id", "ts"]) 

    op.create_table(
        "pool_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("pool_id", sa.BigInteger(), sa.ForeignKey("pools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ts", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("liquidity", sa.Float(), nullable=True),
        sa.Column("tx_count", sa.Integer(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("buys_volume", sa.Float(), nullable=True),
        sa.Column("sells_volume", sa.Float(), nullable=True),
    )
    op.create_index("ix_pool_snapshots_pool_ts", "pool_snapshots", ["pool_id", "ts"]) 

    op.create_table(
        "token_scores",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("token_id", sa.BigInteger(), sa.ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ts", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("components", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index("ix_token_scores_token_ts", "token_scores", ["token_id", "ts"]) 

    op.create_table(
        "settings",
        sa.Column("key", sa.String(), primary_key=True),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_index("ix_token_scores_token_ts", table_name="token_scores")
    op.drop_table("token_scores")
    op.drop_index("ix_pool_snapshots_pool_ts", table_name="pool_snapshots")
    op.drop_table("pool_snapshots")
    op.drop_index("ix_token_snapshots_token_ts", table_name="token_snapshots")
    op.drop_table("token_snapshots")
    op.drop_index("ix_pools_token_id", table_name="pools")
    op.drop_table("pools")
    op.drop_index("ix_tokens_status", table_name="tokens")
    op.drop_table("tokens")
    sa.Enum(name="tokenstatus").drop(op.get_bind(), checkfirst=True)

