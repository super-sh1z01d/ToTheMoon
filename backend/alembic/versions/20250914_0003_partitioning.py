"""Add partitioning for token_metrics

Revision ID: 003_partitioning
Revises: 002_metrics_and_scores
Create Date: 2025-09-14 10:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

# revision identifiers
revision = '003_partitioning'
down_revision = '002_metrics_and_scores'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Добавляем партиционирование для token_metrics по дням
    """
    # Сначала создаем новую партиционированную таблицу
    op.execute("""
        -- Создаем новую партиционированную таблицу token_metrics_partitioned
        CREATE TABLE token_metrics_partitioned (
            LIKE token_metrics INCLUDING ALL
        ) PARTITION BY RANGE (timestamp);
        
        -- Переносим данные из старой таблицы (если есть)
        INSERT INTO token_metrics_partitioned SELECT * FROM token_metrics;
        
        -- Удаляем старую таблицу
        DROP TABLE token_metrics CASCADE;
        
        -- Переименовываем новую таблицу
        ALTER TABLE token_metrics_partitioned RENAME TO token_metrics;
    """)
    
    # Создаем партиции на ближайшие дни
    # Это можно автоматизировать через cron job
    today = datetime.now().date()
    
    for i in range(-1, 32):  # 1 день назад + 31 день вперед
        partition_date = today + timedelta(days=i)
        next_date = partition_date + timedelta(days=1)
        
        partition_name = f"token_metrics_{partition_date.strftime('%Y%m%d')}"
        
        op.execute(f"""
            CREATE TABLE {partition_name} PARTITION OF token_metrics
            FOR VALUES FROM ('{partition_date}') TO ('{next_date}');
        """)
    
    # Создаем функцию для автоматического создания партиций
    op.execute("""
        CREATE OR REPLACE FUNCTION create_token_metrics_partition(partition_date DATE)
        RETURNS TEXT AS $$
        DECLARE
            partition_name TEXT;
            start_date DATE;
            end_date DATE;
        BEGIN
            -- Генерируем имя партиции
            partition_name := 'token_metrics_' || to_char(partition_date, 'YYYYMMDD');
            start_date := partition_date;
            end_date := partition_date + INTERVAL '1 day';
            
            -- Проверяем, не существует ли уже такая партиция
            IF NOT EXISTS (
                SELECT 1 FROM pg_tables 
                WHERE tablename = partition_name
            ) THEN
                -- Создаем партицию
                EXECUTE format(
                    'CREATE TABLE %I PARTITION OF token_metrics FOR VALUES FROM (%L) TO (%L)',
                    partition_name, start_date, end_date
                );
                
                RETURN 'Created partition: ' || partition_name;
            ELSE
                RETURN 'Partition already exists: ' || partition_name;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Создаем функцию для удаления старых партиций (cleanup)
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_token_metrics_partitions(retention_days INTEGER DEFAULT 30)
        RETURNS TEXT AS $$
        DECLARE
            partition_record RECORD;
            cutoff_date DATE;
            result_text TEXT := '';
        BEGIN
            cutoff_date := CURRENT_DATE - retention_days;
            
            -- Находим и удаляем старые партиции
            FOR partition_record IN
                SELECT tablename FROM pg_tables 
                WHERE tablename LIKE 'token_metrics_%'
                AND tablename ~ '^token_metrics_[0-9]{8}$'
                AND to_date(substring(tablename, 15), 'YYYYMMDD') < cutoff_date
            LOOP
                EXECUTE format('DROP TABLE %I', partition_record.tablename);
                result_text := result_text || 'Dropped partition: ' || partition_record.tablename || E'\n';
            END LOOP;
            
            IF result_text = '' THEN
                result_text := 'No old partitions found to cleanup';
            END IF;
            
            RETURN result_text;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Пересоздаем внешние ключи после партиционирования
    op.execute("""
        -- Добавляем обратно foreign key constraint
        ALTER TABLE token_metrics ADD CONSTRAINT token_metrics_token_id_fkey 
        FOREIGN KEY (token_id) REFERENCES tokens(id) ON DELETE CASCADE;
    """)


def downgrade() -> None:
    """
    Откат партиционирования - преобразуем обратно в обычную таблицу
    """
    # Создаем временную обычную таблицу
    op.execute("""
        -- Создаем временную таблицу для данных
        CREATE TABLE token_metrics_temp (
            LIKE token_metrics INCLUDING ALL EXCLUDING CONSTRAINTS
        );
        
        -- Копируем все данные из партиционированной таблицы
        INSERT INTO token_metrics_temp SELECT * FROM token_metrics;
        
        -- Удаляем партиционированную таблицу со всеми партициями
        DROP TABLE token_metrics CASCADE;
        
        -- Переименовываем временную таблицу
        ALTER TABLE token_metrics_temp RENAME TO token_metrics;
        
        -- Восстанавливаем primary key
        ALTER TABLE token_metrics ADD PRIMARY KEY (id);
        
        -- Восстанавливаем foreign key
        ALTER TABLE token_metrics ADD CONSTRAINT token_metrics_token_id_fkey 
        FOREIGN KEY (token_id) REFERENCES tokens(id) ON DELETE CASCADE;
    """)
    
    # Удаляем функции партиционирования
    op.execute("DROP FUNCTION IF EXISTS create_token_metrics_partition(DATE);")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_token_metrics_partitions(INTEGER);")
