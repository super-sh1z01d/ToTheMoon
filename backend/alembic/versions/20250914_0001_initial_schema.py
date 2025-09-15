"""Initial schema creation

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-09-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание enum типов
    tokenstatus_enum = sa.Enum('INITIAL', 'ACTIVE', 'ARCHIVED', name='tokenstatus')
    statuschangereason_enum = sa.Enum(
        'DISCOVERY', 'ACTIVATION', 'LOW_SCORE', 'LOW_ACTIVITY', 'ARCHIVAL_TIMEOUT', 
        name='statuschangereason'
    )
    
    tokenstatus_enum.create(op.get_bind())
    statuschangereason_enum.create(op.get_bind())
    
    # Таблица tokens
    op.create_table('tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('token_address', sa.String(length=44), nullable=False, comment='Адрес контракта токена в сети Solana'),
        sa.Column('status', tokenstatus_enum, nullable=False, comment='Текущий статус токена в системе'),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True, comment='Время перехода в статус Active'),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True, comment='Время перехода в статус Archived'),
        sa.Column('last_score_value', sa.Float(), nullable=True, comment='Последнее значение скора'),
        sa.Column('last_score_calculated_at', sa.DateTime(timezone=True), nullable=True, comment='Время последнего расчета скора'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_address')
    )
    
    # Индексы для tokens
    op.create_index('ix_tokens_created_at', 'tokens', ['created_at'])
    op.create_index('ix_tokens_token_address', 'tokens', ['token_address'])
    op.create_index('ix_tokens_status', 'tokens', ['status'])
    op.create_index('ix_tokens_status_created', 'tokens', ['status', 'created_at'])
    op.create_index('ix_tokens_score_active', 'tokens', ['last_score_value', 'status'])
    op.create_index('ix_tokens_address_status', 'tokens', ['token_address', 'status'])
    
    # Таблица token_status_history
    op.create_table('token_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('token_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_status', tokenstatus_enum, nullable=True, comment='Предыдущий статус'),
        sa.Column('new_status', tokenstatus_enum, nullable=False, comment='Новый статус'),
        sa.Column('reason', statuschangereason_enum, nullable=False, comment='Причина смены статуса'),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время изменения статуса'),
        sa.Column('change_metadata', sa.String(), nullable=True, comment='Дополнительная информация об изменении'),
        sa.ForeignKeyConstraint(['token_id'], ['tokens.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для token_status_history
    op.create_index('ix_token_status_history_created_at', 'token_status_history', ['created_at'])
    op.create_index('ix_token_status_history_token_id', 'token_status_history', ['token_id'])
    op.create_index('ix_token_status_history_changed_at', 'token_status_history', ['changed_at'])
    op.create_index('ix_status_history_token_time', 'token_status_history', ['token_id', 'changed_at'])
    op.create_index('ix_status_history_reason', 'token_status_history', ['reason', 'changed_at'])
    op.create_index('ix_status_history_new_status', 'token_status_history', ['new_status', 'changed_at'])
    
    # Таблица pools
    op.create_table('pools',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('pool_address', sa.String(length=44), nullable=False, comment='Адрес пула ликвидности'),
        sa.Column('token_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dex_name', sa.String(length=50), nullable=False, comment='Название DEX (raydium, orca, etc.)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Активен ли пул для торгов'),
        sa.ForeignKeyConstraint(['token_id'], ['tokens.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pool_address')
    )
    
    # Индексы для pools
    op.create_index('ix_pools_created_at', 'pools', ['created_at'])
    op.create_index('ix_pools_pool_address', 'pools', ['pool_address'])
    op.create_index('ix_pools_token_id', 'pools', ['token_id'])
    op.create_index('ix_pools_dex_name', 'pools', ['dex_name'])
    op.create_index('ix_pools_is_active', 'pools', ['is_active'])
    op.create_index('ix_pools_token_active', 'pools', ['token_id', 'is_active'])
    op.create_index('ix_pools_dex_active', 'pools', ['dex_name', 'is_active'])
    op.create_index('ix_pools_address_token', 'pools', ['pool_address', 'token_id'])
    
    # Таблица system_config
    op.create_table('system_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False, comment='Ключ конфигурационного параметра'),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Значение параметра в JSON формате'),
        sa.Column('description', sa.String(length=500), nullable=True, comment='Описание назначения параметра'),
        sa.Column('category', sa.String(length=50), nullable=True, comment='Категория параметра (scoring, limits, etc.)'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    
    # Индексы для system_config
    op.create_index('ix_system_config_created_at', 'system_config', ['created_at'])
    op.create_index('ix_system_config_key', 'system_config', ['key'])
    op.create_index('ix_system_config_category', 'system_config', ['category'])
    op.create_index('ix_system_config_category_key', 'system_config', ['category', 'key'])


def downgrade() -> None:
    # Удаление таблиц в обратном порядке
    op.drop_table('system_config')
    op.drop_table('pools')
    op.drop_table('token_status_history')
    op.drop_table('tokens')
    
    # Удаление enum типов
    sa.Enum(name='statuschangereason').drop(op.get_bind())
    sa.Enum(name='tokenstatus').drop(op.get_bind())
