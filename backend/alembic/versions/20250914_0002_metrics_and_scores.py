"""Add metrics and scores tables

Revision ID: 002_metrics_and_scores
Revises: 001_initial_schema
Create Date: 2025-09-14 10:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_metrics_and_scores'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Таблица token_metrics (базовая, партиционирование добавим отдельно)
    op.create_table('token_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('token_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, comment='Время снятия метрик'),
        sa.Column('tx_count_5m', sa.Integer(), nullable=False, comment='Количество транзакций за 5 минут'),
        sa.Column('tx_count_1h', sa.Integer(), nullable=False, comment='Количество транзакций за 1 час'),
        sa.Column('volume_5m_usd', sa.Numeric(precision=20, scale=2), nullable=False, comment='Объем торгов за 5 минут в USD'),
        sa.Column('volume_1h_usd', sa.Numeric(precision=20, scale=2), nullable=False, comment='Объем торгов за 1 час в USD'),
        sa.Column('buys_volume_5m_usd', sa.Numeric(precision=20, scale=2), nullable=False, comment='Объем покупок за 5 минут в USD'),
        sa.Column('sells_volume_5m_usd', sa.Numeric(precision=20, scale=2), nullable=False, comment='Объем продаж за 5 минут в USD'),
        sa.Column('holders_count', sa.Integer(), nullable=False, comment='Количество держателей токена'),
        sa.Column('liquidity_usd', sa.Numeric(precision=20, scale=2), nullable=False, comment='Общая ликвидность в USD'),
        sa.ForeignKeyConstraint(['token_id'], ['tokens.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для token_metrics
    op.create_index('ix_token_metrics_created_at', 'token_metrics', ['created_at'])
    op.create_index('ix_token_metrics_token_id', 'token_metrics', ['token_id'])
    op.create_index('ix_token_metrics_timestamp', 'token_metrics', ['timestamp'])
    op.create_index('ix_token_metrics_token_time', 'token_metrics', ['token_id', 'timestamp'])
    op.create_index('ix_token_metrics_volume', 'token_metrics', ['volume_5m_usd', 'timestamp'])
    op.create_index('ix_token_metrics_tx_count', 'token_metrics', ['tx_count_5m', 'timestamp'])
    
    # Таблица token_scores
    op.create_table('token_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('token_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False, comment='Название модели скоринга (например, hybrid_momentum_v1)'),
        sa.Column('score_value', sa.Float(), nullable=False, comment='Значение скора'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время расчета скора'),
        sa.Column('components', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Детали расчета компонентов скора в JSON'),
        sa.ForeignKeyConstraint(['token_id'], ['tokens.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для token_scores
    op.create_index('ix_token_scores_created_at', 'token_scores', ['created_at'])
    op.create_index('ix_token_scores_token_id', 'token_scores', ['token_id'])
    op.create_index('ix_token_scores_model_name', 'token_scores', ['model_name'])
    op.create_index('ix_token_scores_calculated_at', 'token_scores', ['calculated_at'])
    op.create_index('ix_token_scores_token_calculated', 'token_scores', ['token_id', 'calculated_at'])
    op.create_index('ix_token_scores_model_calculated', 'token_scores', ['model_name', 'calculated_at'])
    op.create_index('ix_token_scores_value_calculated', 'token_scores', ['score_value', 'calculated_at'])
    op.create_index('ix_token_scores_model_score', 'token_scores', ['model_name', 'score_value'])
    
    # Таблица birdeye_raw_data
    op.create_table('birdeye_raw_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('token_address', sa.String(length=44), nullable=False, comment='Адрес токена Solana'),
        sa.Column('endpoint', sa.String(length=50), nullable=False, comment='Название API endpoint (token_overview, trades_info, etc.)'),
        sa.Column('response_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Полный ответ от Birdeye API в JSON'),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время получения данных от API'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='Время истечения данных (TTL = 7 дней)'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для birdeye_raw_data
    op.create_index('ix_birdeye_raw_data_created_at', 'birdeye_raw_data', ['created_at'])
    op.create_index('ix_birdeye_raw_data_token_address', 'birdeye_raw_data', ['token_address'])
    op.create_index('ix_birdeye_raw_data_endpoint', 'birdeye_raw_data', ['endpoint'])
    op.create_index('ix_birdeye_raw_data_fetched_at', 'birdeye_raw_data', ['fetched_at'])
    op.create_index('ix_birdeye_raw_data_expires_at', 'birdeye_raw_data', ['expires_at'])
    op.create_index('ix_birdeye_token_endpoint', 'birdeye_raw_data', ['token_address', 'endpoint'])
    op.create_index('ix_birdeye_token_fetched', 'birdeye_raw_data', ['token_address', 'fetched_at'])
    op.create_index('ix_birdeye_expires', 'birdeye_raw_data', ['expires_at'])
    op.create_index('ix_birdeye_endpoint_fetched', 'birdeye_raw_data', ['endpoint', 'fetched_at'])


def downgrade() -> None:
    # Удаление таблиц в обратном порядке
    op.drop_table('birdeye_raw_data')
    op.drop_table('token_scores')
    op.drop_table('token_metrics')
