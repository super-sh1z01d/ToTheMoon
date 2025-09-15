"""Add initial system configuration

Revision ID: 004_initial_config
Revises: 003_partitioning
Create Date: 2025-09-14 10:03:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

# revision identifiers
revision = '004_initial_config'
down_revision = '003_partitioning'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Добавляем начальную конфигурацию системы
    """
    # Определяем таблицу для работы с данными
    system_config = table('system_config',
        column('id', UUID),
        column('key', sa.String),
        column('value', JSONB),
        column('description', sa.String),
        column('category', sa.String),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )
    
    # Начальные конфигурационные параметры согласно vision.md
    initial_configs = [
        {
            'id': str(uuid.uuid4()),
            'key': 'SCORING_MODEL',
            'value': '"hybrid_momentum_v1"',
            'description': 'Активная модель скоринга',
            'category': 'scoring'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'SCORING_WEIGHTS',
            'value': '{"W_tx": 0.25, "W_vol": 0.35, "W_hld": 0.20, "W_oi": 0.20}',
            'description': 'Весовые коэффициенты для формулы скоринга',
            'category': 'scoring'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'EWMA_ALPHA',
            'value': '0.3',
            'description': 'Параметр сглаживания EWMA',
            'category': 'scoring'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'MIN_SCORE_THRESHOLD',
            'value': '0.5',
            'description': 'Минимальный скор для удержания статуса Active',
            'category': 'scoring'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'LOW_SCORE_HOURS',
            'value': '6',
            'description': 'Временное окно для понижения статуса из-за низкого скора (в часах)',
            'category': 'lifecycle'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'MIN_TX_COUNT',
            'value': '300',
            'description': 'Минимальное количество транзакций для активации и удержания статуса Active',
            'category': 'lifecycle'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'LOW_ACTIVITY_CHECKS',
            'value': '10',
            'description': 'Количество последовательных проверок для понижения статуса из-за низкой активности',
            'category': 'lifecycle'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'MIN_LIQUIDITY_USD',
            'value': '500',
            'description': 'Минимальная ликвидность в пуле для активации (в USD)',
            'category': 'lifecycle'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'ARCHIVAL_TIMEOUT_HOURS',
            'value': '24',
            'description': 'Время в статусе Initial до архивации (в часах)',
            'category': 'lifecycle'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'MIN_SCORE_FOR_CONFIG',
            'value': '0.7',
            'description': 'Минимальный скор для включения в TOML конфигурацию',
            'category': 'export'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'CONFIG_TOP_COUNT',
            'value': '3',
            'description': 'Количество топ токенов в TOML конфигурации',
            'category': 'export'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'BIRDEYE_CACHE_TTL_SECONDS',
            'value': '60',
            'description': 'TTL кеша для Birdeye API в секундах',
            'category': 'api'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'BIRDEYE_RAW_DATA_TTL_DAYS',
            'value': '7',
            'description': 'TTL для raw данных Birdeye в днях',
            'category': 'api'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'METRICS_RETENTION_DAYS',
            'value': '30',
            'description': 'Период хранения метрик в днях',
            'category': 'storage'
        },
        {
            'id': str(uuid.uuid4()),
            'key': 'SCORES_RETENTION_DAYS',
            'value': '30',
            'description': 'Период хранения скоров в днях',
            'category': 'storage'
        }
    ]
    
    # Вставляем начальные данные
    for config in initial_configs:
        op.execute(
            system_config.insert().values(
                id=config['id'],
                key=config['key'],
                value=config['value'],
                description=config['description'],
                category=config['category']
            )
        )


def downgrade() -> None:
    """
    Удаляем начальную конфигурацию
    """
    # Удаляем все записи конфигурации, созданные в upgrade
    config_keys = [
        'SCORING_MODEL', 'SCORING_WEIGHTS', 'EWMA_ALPHA', 'MIN_SCORE_THRESHOLD',
        'LOW_SCORE_HOURS', 'MIN_TX_COUNT', 'LOW_ACTIVITY_CHECKS', 'MIN_LIQUIDITY_USD',
        'ARCHIVAL_TIMEOUT_HOURS', 'MIN_SCORE_FOR_CONFIG', 'CONFIG_TOP_COUNT',
        'BIRDEYE_CACHE_TTL_SECONDS', 'BIRDEYE_RAW_DATA_TTL_DAYS', 
        'METRICS_RETENTION_DAYS', 'SCORES_RETENTION_DAYS'
    ]
    
    for key in config_keys:
        op.execute(f"DELETE FROM system_config WHERE key = '{key}'")
