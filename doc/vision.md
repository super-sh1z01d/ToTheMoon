# Техническое видение: Система скоринга токенов "ToTheMoon2"

Версия: 1.0  
Дата: 14 сентября 2025 г.

## 1. Технологии

### Backend
- **Python 3.11+** - основной язык разработки
- **FastAPI** - веб-фреймворк (производительность, автодокументация, типизация)
- **SQLAlchemy + Alembic** - ORM и миграции базы данных
- **PostgreSQL** - основная база данных (включая временные ряды)
- **Redis** - кеширование и очереди задач
- **Celery** - фоновые задачи и планировщик
- **WebSockets** - real-time обновления данных (встроенные в FastAPI)

### Frontend
- **React** - основной фреймворк интерфейса
- **TypeScript** - статическая типизация
- **Tailwind CSS** - утилитарные стили
- **Recharts** - графики и sparklines
- **React Query** - управление состоянием и кеширование запросов

### Инфраструктура
- **Nginx** - reverse proxy и раздача статики
- **Systemd** - управление сервисами (backend, Celery)
- **GitHub Actions** - CI/CD pipeline

### Мониторинг и логирование
- **Prometheus + Grafana** - сбор метрик и дашборды
- **Structured logging (JSON)** - структурированное логирование
- **Python logging** - встроенные возможности

### Деплой
- **VPS** - целевая платформа развертывания

## 2. Принципы разработки

### Основные принципы
- **Простота превыше всего** - никакого оверинжиниринга, выбираем самые простые решения
- **KISS (Keep It Simple, Stupid)** - каждый компонент решает одну задачу хорошо
- **Модульность скоринга** - легкое добавление новых моделей расчета без изменения основной логики
- **Fail Fast** - быстрое обнаружение ошибок на раннем этапе
- **Explicit is better than implicit** - явные зависимости и конфигурация

### Архитектурные принципы
- **Разделение ответственности** - четкие границы между сбором данных, обработкой и представлением
- **Dependency Injection** - для тестируемости и гибкости
- **Event-driven подход** - для обработки WebSocket событий и фоновых задач
- **Configuration over code** - настраиваемые параметры через конфигурацию
- **Graceful degradation** - система работает даже при недоступности внешних API

### Подход к коду
- **Type hints обязательны** в Python
- **Pydantic** для валидации данных и моделей
- **Asyncio** для I/O операций
- **Ручное тестирование** - фокус на функциональном тестировании
- **Минимальная документация** - комментарии в коде + docstrings для публичных методов
- **Минимум зависимостей** - только необходимые библиотеки

## 3. Структура проекта

```
ToTheMoon2/
├── backend/                    # Backend приложение
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Основная бизнес-логика
│   │   │   ├── scoring/       # Модули скоринга (модульность!)
│   │   │   ├── data_sources/  # Интеграции с внешними API
│   │   │   └── lifecycle/     # Жизненный цикл токенов
│   │   ├── models/            # SQLAlchemy модели
│   │   ├── schemas/           # Pydantic схемы
│   │   └── workers/           # Celery воркеры
│   ├── tests/                 # Тесты (для будущего использования)
│   ├── alembic/               # Миграции БД
│   ├── config/                # Конфигурационные файлы
│   └── requirements.txt
├── frontend/                   # React приложение
│   ├── src/
│   │   ├── components/        # React компоненты
│   │   ├── pages/            # Страницы (главная, админ-панель)
│   │   ├── hooks/            # Кастомные хуки
│   │   └── types/            # TypeScript типы
│   ├── tests/                # Frontend тесты
│   └── package.json
├── deploy/                     # Примеры системной конфигурации (nginx)
├── scripts/                    # Утилиты развертывания и обслуживания
├── logs/                      # Логи приложения
├── docs/                      # Документация проекта
└── .env                       # Переменные окружения
```

### Принципы структуры
- **Модульность скоринга** - `backend/app/core/scoring/` для разных моделей расчета
- **Разделение ответственности** - четкие границы между API, бизнес-логикой, моделями
- **Простота навигации** - плоская структура без глубокой вложенности
- **Наглядность тестов** - отдельные папки `tests/` для frontend и backend
- **Операционное удобство** - `scripts/` для автоматизации, `logs/` для мониторинга

## 4. Архитектура системы

### Общая схема компонентов

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   Birdeye API   │    │   Web UI        │
│   pumpportal    │    │                 │    │   (React)       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          v                      v                      v
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  WebSocket  │  │     API     │  │ Admin Panel │            │
│  │  Handler    │  │ Endpoints   │  │    API      │            │
│  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘            │
└────────┼──────────────────┼──────────────────┼─────────────────┘
         │                  │                  │
         v                  v                  v
┌─────────────────────────────────────────────────────────────────┐
│                     Business Logic                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Token     │  │   Scoring   │  │Configuration│            │
│  │ Lifecycle   │  │   Engine    │  │  Manager    │            │
│  │  Manager    │  │             │  │             │            │
│  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘            │
└────────┼──────────────────┼──────────────────┼─────────────────┘
         │                  │                  │
         v                  v                  v
┌─────────────────────────────────────────────────────────────────┐
│              Background Workers (Celery)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Lifecycle   │  │  Scoring    │  │ Data Fetch  │            │
│  │ Processor   │  │ Calculator  │  │   Worker    │            │
│  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘            │
└────────┼──────────────────┼──────────────────┼─────────────────┘
         │                  │                  │
         v                  v                  v
┌─────────────────────────────────────────────────────────────────┐
│                   Data Storage                                  │
│  ┌─────────────┐                    ┌─────────────┐            │
│  │ PostgreSQL  │                    │    Redis    │            │
│  │  (Main DB)  │                    │ (Cache,     │            │
│  │             │                    │ Queue,      │            │
│  │             │                    │ Pub/Sub)    │            │
│  └─────────────┘                    └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Ключевые потоки данных

1. **Создание токена**: WebSocket → Token Lifecycle Manager → PostgreSQL
2. **Обновление данных**: Celery Worker → Birdeye API → Redis Cache → Scoring Engine → PostgreSQL
3. **Real-time обновления**: Scoring Engine → Redis Pub/Sub → WebSocket → React UI
4. **Просмотр данных**: React UI → FastAPI → Redis Cache/PostgreSQL → JSON Response
5. **Конфигурация**: Admin Panel → Configuration Manager → PostgreSQL

### Архитектурные решения

- **Redis Cache** - кеширование API ответов от Birdeye (TTL 30-60 сек)
- **Redis Pub/Sub** - real-time уведомления об изменении скоров
- **Configuration Manager** - динамическое управление параметрами без перезапуска
- **Отказоустойчивость** - graceful degradation при недоступности внешних API
- **Слабая связанность** - компоненты общаются через четкие интерфейсы
- **Горизонтальное масштабирование** - Celery workers по необходимости

## 5. Модель данных

### Основные таблицы

```sql
-- Основная таблица токенов
tokens:
  - id (UUID, PK)
  - token_address (String, уникальный, индекс)
  - status (Enum: initial, active, archived) 
  - created_at (DateTime)
  - activated_at (DateTime, nullable)
  - archived_at (DateTime, nullable)
  - last_score_value (Float, nullable)
  - last_score_calculated_at (DateTime, nullable)

-- История смены статусов (для аналитики)
token_status_history:
  - id (UUID, PK)
  - token_id (UUID, FK -> tokens.id)
  - old_status (Enum: initial, active, archived)
  - new_status (Enum: initial, active, archived)
  - changed_at (DateTime, индекс)
  - reason (String: 'low_score', 'low_activity', 'activation', etc.)

-- Пулы ликвидности
pools:
  - id (UUID, PK) 
  - pool_address (String, уникальный)
  - token_id (UUID, FK -> tokens.id)
  - dex_name (String: 'raydium', 'orca', etc.)
  - is_active (Boolean)
  - created_at (DateTime)

-- Исторические метрики (партиционировано по дням)
token_metrics:
  - id (UUID, PK)
  - token_id (UUID, FK -> tokens.id)
  - timestamp (DateTime, индекс)
  - tx_count_5m (Integer)
  - tx_count_1h (Integer) 
  - volume_5m_usd (Decimal)
  - volume_1h_usd (Decimal)
  - buys_volume_5m_usd (Decimal)
  - sells_volume_5m_usd (Decimal)
  - holders_count (Integer)
  - liquidity_usd (Decimal)
  -- Партиция: PARTITION BY RANGE (timestamp)

-- Скоры токенов (история расчетов)
token_scores:
  - id (UUID, PK)
  - token_id (UUID, FK -> tokens.id)
  - model_name (String: 'hybrid_momentum_v1')
  - score_value (Float)
  - calculated_at (DateTime, индекс)
  - components (JSONB: детали расчета компонентов)

-- Raw данные от API (с TTL)
birdeye_raw_data:
  - id (UUID, PK)
  - token_address (String, индекс)
  - endpoint (String: 'token_overview', 'trades_info')
  - response_data (JSONB)
  - fetched_at (DateTime, индекс)
  - expires_at (DateTime, индекс) -- TTL = 7 дней

-- Конфигурация системы
system_config:
  - id (UUID, PK)
  - key (String, уникальный)
  - value (JSONB)
  - updated_at (DateTime)
```

### Стратегия управления данными

- **Партиционирование**: `token_metrics` по дням (автоматическое создание партиций)
- **Retention Policy**: 
  - `birdeye_raw_data` - 7 дней (TTL)
  - `token_metrics` - 30 дней (автоочистка старых партиций)
  - `token_scores` - 30 дней
  - `token_status_history` - без ограничений (для аналитики)
- **Индексы**: По token_address, timestamp, status для быстрых запросов
- **Автоочистка**: Cron задача для удаления устаревших данных

### Принципы модели

- **Простота связей** - минимум FK, четкая иерархия
- **Временные ряды** - эффективное хранение с партиционированием
- **Контроль размера БД** - автоматическая очистка устаревших данных
- **Аналитические возможности** - история статусов и компонентов скоров
- **Восстановление данных** - raw данные доступны в течение недели

## 6. Сценарии работы

### Основные системные сценарии

**1. Обнаружение нового токена**
- Триггер: WebSocket сообщение от pumpportal.fun (subscribeMigration)
- Система: Создает запись токена со статусом "Initial"
- Результат: Токен появляется в списке "Начальных" в веб-интерфейсе

**2. Активация токена**
- Триггер: Celery worker проверяет токены в статусе "Initial"
- Условие: Пул с ликвидностью ≥$500 и транзакциями ≥300 (min_tx_count)
- Система: Меняет статус на "Active", запускает периодический скоринг
- Результат: Токен переходит в основную таблицу с расчетом скора

**3. Мониторинг и скоринг активных токенов**
- Периодичность: Каждые 1-5 минут (настраиваемо)
- Процесс: Birdeye API → Кеш → Расчет скора → Обновление БД → Real-time UI
- Технология: WebSocket обновления в интерфейс через Redis Pub/Sub

**4. Экспорт конфигурации для арбитражного бота**
- URL: `/config/dynamic_strategy.toml` (публичный endpoint)
- Логика: Активные токены → Фильтр по min_score_for_config → Топ-3 по скору
- Формат: TOML файл с токенами и их активными пулами
- Интеграция: Для бота [NotArb](https://github.com/NotArb/Release/tree/main/onchain-bot)

**5. Деактивация токена** 
- Условие А: Скор < минимального 6 часов подряд
- Условие Б: Активность пула < min_tx_count в течение N проверок
- Система: Возврат в статус "Initial" для повторного мониторинга

**6. Архивация токена**
- Условие: Токен в статусе "Initial" более 24 часов без активации
- Система: Перевод в "Archived", исключение из всех проверок

### Пользовательские сценарии

**Арбитражный трейдер:**
- Открывает https://tothemoon.sh1z01d.ru
- Просматривает таблицу активных токенов, отсортированную по скору
- Анализирует sparkline графики динамики скоров
- Кликает на токен для детального просмотра пулов и метрик
- Настраивает своего бота на автоматическое получение конфига

**Администратор системы:**
- Заходит в админ-панель веб-интерфейса
- Настраивает параметры скоринга (веса W_tx, W_vol, пороги)
- Переключает активную модель расчета скора
- Мониторит распределение токенов по статусам
- Настраивает параметры экспорта (min_score_for_config)

### Архитектурные заметки
- **API готовность** - FastAPI структура позволит легко добавить REST API
- **Масштабируемость** - возможность добавления новых endpoint'ов экспорта
- **Интеграция** - публичный TOML endpoint для внешних ботов

## 7. Деплой

### Целевая инфраструктура
**VPS:** Cloud MSK 40 (2x 3.3 ГГц CPU, 2 ГБ RAM, 40 ГБ NVMe)  
**Домен:** tothemoon.sh1z01d.ru  
**Окружения:** Development → Production (без staging)

### Docker Compose архитектура (оптимизированная под 2 ГБ RAM)

```yaml
services:
  nginx:          # ~50 MB RAM
  backend:        # ~200-300 MB RAM
  frontend:       # статика (nginx serve)
  postgres:       # ~100-150 MB RAM  
  redis:          # ~50-100 MB RAM
  celery-worker:  # ~150-200 MB RAM (1 воркер)
  celery-beat:    # ~50 MB RAM
```

**Общее потребление:** ~600-850 MB (достаточный запас для ОС)

### CI/CD Pipeline (автоматический)

```yaml
GitHub Actions:
  trigger: push to main
  steps:
    1. Build & test (optional)
    2. Build Docker images  
    3. SSH deploy to VPS
    4. Health check
    5. Notify (Telegram/Discord)
```

### Настройки для ограниченных ресурсов

**PostgreSQL:**
- `shared_buffers = 64MB`
- `max_connections = 20`
- `work_mem = 4MB`

**Redis:**
- `maxmemory 100mb`
- `maxmemory-policy allkeys-lru`

**Celery:**
- 1 worker процесс
- `--concurrency=2` (2 задачи параллельно)

**Backend:**
- `workers=1` (Uvicorn)
- Connection pooling: max 5 соединений к БД

### Persistence и backup

```yaml
volumes:
  postgres_data: /var/lib/postgresql/data
  redis_data: /var/lib/redis  
  logs: /app/logs
  
backups:
  frequency: ежедневно в 03:00
  retention: 7 дней
  location: /backups/ (+ копия в облако)
```

### SSL и безопасность
- **Let's Encrypt** - автообновление сертификатов
- **Nginx rate limiting** - защита от DDoS
- **Firewall** - только порты 22, 80, 443

### Мониторинг (lightweight)
- **Health checks** - FastAPI `/health` endpoint
- **Simple metrics** - через logs + grep скрипты
- **Alerts** - при падении сервисов (Telegram бот)

*Примечание: Prometheus+Grafana исключены из-за потребления RAM*

## 8. Подход к конфигурированию

### Трехуровневая система конфигурации

**1. Системная конфигурация (environment variables)**
```bash
# Окружение и подключения
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
BIRDEYE_API_KEY=...
PUMPPORTAL_WS_URL=wss://pumpportal.fun/data-api/real-time

# Базовые настройки
LOG_LEVEL=INFO
SECRET_KEY=...
CORS_ORIGINS=https://tothemoon.sh1z01d.ru
```

**2. Бизнес-параметры (админ-панель → БД)**
```python
# Хранятся в таблице system_config
SCORING_MODEL = "hybrid_momentum_v1"
SCORING_WEIGHTS = {
    "W_tx": 0.25, "W_vol": 0.35, 
    "W_hld": 0.20, "W_oi": 0.20
}
EWMA_ALPHA = 0.3
MIN_SCORE_THRESHOLD = 0.5
LOW_SCORE_HOURS = 6
MIN_TX_COUNT = 300
LOW_ACTIVITY_CHECKS = 10
MIN_SCORE_FOR_CONFIG = 0.7
```

**3. Операционные настройки (конфиг файлы)**
```yaml
# backend/config/app.yaml
celery:
  beat_schedule:
    lifecycle_check: "*/5 * * * *"  # каждые 5 минут
    scoring_update: "*/2 * * * *"   # каждые 2 минуты
    
cache:
  birdeye_ttl: 60  # секунды
  ui_data_ttl: 30  # секунды
  
limits:
  max_tokens_per_status: 10000
  api_rate_limit: "100/minute"
```

### Архитектура

**Configuration Manager:**
- Dependency Injection для всех компонентов
- Hot reload параметров из БД без перезапуска
- Fallback на значения по умолчанию
- Валидация значений (например, сумма весов = 1.0)

**Админ-панель:**
- Простые формы для редактирования параметров
- Валидация в real-time
- Сохранение с подтверждением

### Принципы
- **Простота** - минимум функций, максимум пользы
- **Hot reload** - изменения применяются мгновенно
- **Environment first** - системные переменные имеют приоритет
- **Валидация** - предотвращение некорректных значений

## 9. Подход к логгированию

### Структурированное логгирование (JSON)

```json
{
  "timestamp": "2025-09-14T10:30:00Z",
  "level": "INFO",
  "service": "scoring_engine", 
  "message": "Score calculated for token",
  "token_address": "So11111...112",
  "score_value": 0.75,
  "execution_time_ms": 45,
  "correlation_id": "uuid-here"
}
```

### Уровни и категории

**Уровни:**
- **ERROR** - ошибки, требующие внимания
- **WARNING** - проблемы, не критичные для работы  
- **INFO** - ключевые события системы
- **DEBUG** - детальная информация (только в dev)

**Компоненты:**
- **FastAPI** - HTTP запросы, валидация, performance
- **Celery** - задачи скоринга, API Birdeye, статусы токенов
- **WebSocket** - pumpportal.fun события, соединения
- **Database** - медленные запросы (>100ms), ошибки

### Ротация и хранение

```yaml
log_rotation:
  max_size: 50MB     # размер файла
  max_files: 7       # количество файлов  
  compression: gzip  # сжатие старых логов
  
paths:
  app: /app/logs/app.log
  celery: /app/logs/celery.log
  nginx: /app/logs/nginx.log
  errors: /app/logs/errors.log
```

### Анализ и мониторинг

**Простые скрипты:**
```bash
# Ошибки за последний час
grep '"level":"ERROR"' app.log | tail -100

# Статистика по токенам  
grep "token_status_changed" app.log | jq '.new_status' | sort | uniq -c

# Performance issues
grep '"execution_time_ms"' app.log | jq 'select(.execution_time_ms > 1000)'
```

**Алерты:**
- Проверка ERROR логов каждые 5 минут
- Telegram уведомления при критических ошибках
- Health check мониторинг доступности

### Принципы
- **Correlation ID** - отслеживание запросов через компоненты
- **Минимальная детализация** - только необходимая информация
- **Performance aware** - логгирование не замедляет систему
- **Privacy compliant** - без чувствительных данных
- **Операционная простота** - легко читать и анализировать

---

## Заключение

Техническое видение системы "ToTheMoon2" готово. Документ описывает простую, но функциональную архитектуру для автоматического скоринга токенов Solana с экспортом конфигурации для арбитражного бота.

**Ключевые особенности:**
- Модульная архитектура скоринга
- Оптимизация под ограниченные ресурсы VPS (2 ГБ RAM)
- Автоматический деплой и мониторинг
- Простота разработки и сопровождения

Документ служит основой для начала разработки.
