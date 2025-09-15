# Техническое видение: ToTheMoon2

Этот документ фиксирует минимальное техническое видение системы скоринга токенов «ToTheMoon2» в соответствии с функциональным заданием `doc/functional_task.md`. Придерживаемся принципа: никакого оверинжиниринга, без Docker.

## 1. Технологии

- Язык и рантайм
  - Python 3.11+
  - Асинхронность: `asyncio`

- Веб/API
  - FastAPI (ASGI) + Uvicorn
  - Pydantic v2 для схем и валидации

- Хранение данных
  - PostgreSQL 15 (dev и prod)
  - SQLAlchemy 2.0 (Declarative, async) для доступа к данным
  - Alembic для миграций

- Интеграции
  - WebSocket-клиент к `wss://pumpportal.fun/data-api/real-time` (подписка `subscribeMigration`)
  - HTTP-клиент к Birdeye API (на `aiohttp`), с ретраями и экспоненциальным бэкоффом

- Фоновые задачи
  - Периодические и долговые задачи на чистом `asyncio` (без сторонних брокеров)

- UI (минимальный)
  - Серверные шаблоны Jinja2 для таблицы токенов и простой админки

- Конфигурация
  - Pydantic Settings; значения из переменных окружения; `.env` только для разработки

- Логирование и наблюдаемость (минимум)
  - Встроенный `logging` с ротацией файлов; уровень и формат из конфигурации
  - Endpoint здоровья `/health` в FastAPI

- Качество кода
  - `pytest` (тесты критичных путей)
  - `ruff` (линт и формат) и `mypy` (умеренный режим)

- Деплой (кратко, детали в соответствующем разделе)
  - Один Linux-сервер, systemd-сервисы для API и фоновых задач; Nginx как reverse proxy

Примечания:
- LLM в проекте не используется (вне скоупа v1).
- Docker не используется.

## 2. Принципы разработки

- KISS: минимальные зависимости и простые решения, только необходимое для v1.
- Моно-сервис: один процесс FastAPI с фоновыми задачами на `asyncio`.
- Малые итерации: маленькие PR (до ~200 строк), одна фича — один PR.
- Надежность интеграций: таймауты, ретраи с экспоненциальным бэкоффом и джиттером; идемпотентность.
- Стабильные интерфейсы: вход/выход через Pydantic-схемы; версионирование API по мере необходимости.
- Миграции БД: Alembic; одна миграция на изменение схемы; только forward.
- Конфигурация: все секреты и параметры — через env; редактируемые админкой параметры — в таблице `settings`.
- Обработка ошибок: не глушить исключения; логировать с уровнем и контекстом; клиенту — краткие сообщения.
- Производительность: ограничивать параллелизм при обращении к внешним API (Semaphore).
- Кэширование Birdeye: краткоживущий in-memory TTL-кэш (15–60 сек) по ключу «метод+URL+параметры», без Redis; обход кэша для критически свежих запросов.
- Тесты по сути: покрыть расчет скоринга и переходы статусов; минимум моков.
- Наблюдаемость: структурированные логи + `/health`; отдельные метрики и трассировка — вне v1.
- Без Docker: локально и на сервере — виртуальные окружения и systemd-сервисы.

## 3. Структура проекта

- `app/main.py` — точка входа FastAPI, регистрация роутов, lifespans.
- `app/core/config.py` — Pydantic Settings, чтение env, дефолты для dev.
- `app/core/logging.py` — настройка `logging`, формат, ротация.
- `app/db/session.py` — создание async `Engine` и `sessionmaker`.
- `app/db/base.py` — базовый класс и импорт моделей для Alembic.
- `app/models/token.py` — модель токена.
- `app/models/pool.py` — модель пула ликвидности.
- `app/models/settings.py` — редактируемые параметры (веса, пороги и т.п.).
- `app/schemas/token.py` — Pydantic-схемы для токенов.
- `app/schemas/pool.py` — Pydantic-схемы для пулов.
- `app/schemas/scoring.py` — схемы скора/метрик.
- `app/repositories/token.py` — DAO для токенов.
- `app/repositories/pool.py` — DAO для пулов.
- `app/services/birdeye.py` — клиент Birdeye (aiohttp, ретраи, TTL-кэш).
- `app/services/pumpportal.py` — WebSocket-клиент (subscribeMigration).
- `app/services/scoring.py` — расчет скора, сглаживание, пороги.
- `app/services/scheduler.py` — периодические задачи и переходы статусов.
- `app/services/cache.py` — простой in-memory TTL-кэш.
- `app/api/health.py` — health-check endpoint.
- `app/api/tokens.py` — ручки для списка/деталей токенов.
- `app/api/admin.py` — ручки админки (параметры скоринга).
- `app/templates/index.html` — список токенов (таблица, sparkline позже).
- `app/templates/token.html` — детальный вид токена.
- `app/templates/admin.html` — простая админка.
- `migrations/` — Alembic миграции.
- `tests/` — pytest: юниты на скоринг и статусы.

## 4. Архитектура проекта

- Потоки данных
  - Инжест: `services/pumpportal.py` держит WebSocket и создаёт записи токенов (status=Initial).
  - Обновления: `services/scheduler.py` периодически запрашивает Birdeye для релевантных токенов; ответы кешируются на 15–60 сек.
  - Скоринг: `services/scoring.py` считает метрики (Tx_Accel, Vol_Momentum, Holder_Growth, Orderflow_Imbalance), взвешивает и применяет EWMA-сглаживание; результат сохраняет.
  - Статусы: в `services/scheduler.py` правила переходов Initial→Active и понижения до Archived.
  - API/UI: FastAPI отдаёт список/детали токенов и минимальную админку.

- Компоненты
  - БД — единственный источник истины; брокеры/очереди не используются.
  - Интеграции изолированы в сервисах; репозитории инкапсулируют доступ к БД.
  - Админка обновляет запись в `settings`, изменения подхватываются без перезапуска.

- Конкурентность и надёжность
  - Один процесс, несколько `asyncio`-задач: WebSocket-слушатель + периодические задачи.
  - Глобальный `asyncio.Semaphore` ограничивает параллелизм внешних запросов; ретраи с backoff+jitter.
  - Идемпотентность: upsert токенов/пулов; уникальные ключи защищают от дублей.

- Кеширование
  - In-memory TTL-кэш в `services/birdeye.py` по ключу «метод+URL+параметры»; флаг bypass для критически свежих запросов.

- Отказоустойчивость
  - Ошибки Birdeye — лог и пропуск итерации без падения процесса.
  - WebSocket — автопереподключение с экспоненциальным бэкоффом.

## 5. Модель данных

- Общие принципы
  - Хранить текущее состояние и час истории для расчёта динамики.
  - Индексы на внешние ключи и метки времени; уникальные ограничения на адреса.

- Таблицы
  - `tokens`
    - `id` (PK, bigint)
    - `address` (text, unique, not null)
    - `symbol` (text, nullable)
    - `status` (enum: Initial|Active|Archived, not null)
    - `created_at` (timestamptz, not null)
    - `activated_at` (timestamptz, null)
    - `last_score_value` (double precision, null)
    - Индексы: `ix_tokens_status`, `ux_tokens_address`

  - `pools`
    - `id` (PK)
    - `token_id` (FK -> tokens.id, not null)
    - `pool_address` (text, unique, not null)
    - `dex_name` (text, not null)
    - Индексы: `ux_pools_address`, `ix_pools_token_id`

  - `token_snapshots`
    - `id` (PK)
    - `token_id` (FK -> tokens.id, not null)
    - `ts` (timestamptz, not null)
    - `holders` (integer, null)
    - `price` (double precision, null)
    - Индексы: `ix_token_snapshots_token_ts (token_id, ts)`

  - `pool_snapshots`
    - `id` (PK)
    - `pool_id` (FK -> pools.id, not null)
    - `ts` (timestamptz, not null)
    - `liquidity` (double precision, null)
    - `tx_count` (integer, null)
    - `volume` (double precision, null)
    - `buys_volume` (double precision, null)
    - `sells_volume` (double precision, null)
    - Индексы: `ix_pool_snapshots_pool_ts (pool_id, ts)`

  - `token_scores`
    - `id` (PK)
    - `token_id` (FK -> tokens.id, not null)
    - `ts` (timestamptz, not null)
    - `score` (double precision, not null)
    - `components` (jsonb, not null) — детали метрик и весов
    - Индексы: `ix_token_scores_token_ts (token_id, ts)`

  - `settings`
    - `key` (text, PK)
    - `value` (jsonb, not null)
    - `updated_at` (timestamptz, not null)

- Политика хранения
  - Снимки (`*_snapshots`, `token_scores`) — хранить минимум 2 часа; регулярная очистка джобой (раз в сутки).

- Вычисления
  - Tx_Accel: (tx_count_5m/5) / (tx_count_1h/60). Агрегаты собираются из `pool_snapshots`.
  - Vol_Momentum: volume_5m / (volume_1h/12). Источник — `pool_snapshots`.
  - Holder_Growth: log(1 + Δholders / holders_1h_ago). Источник — `token_snapshots`.
  - Orderflow_Imbalance: (buys_volume_5m - sells_volume_5m) / (buys_volume_5m + sells_volume_5m).
  - Итоговый скор = сумма компонентов с весами из `settings`, затем EWMA.

## 6. Работа с LLM

- LLM не используется в v1. Раздел зарезервирован; любая интеграция — вне скоупа данного релиза.

## 7. Мониторинг LLM

- Не применяется, так как LLM отсутствует в v1.

## 8. Сценарии работы

- Новые токены
  - WebSocket получает событие — создаём `tokens(address, status=Initial)` если нет.

- Активация токена (Initial→Active)
  - Периодическая задача проверяет наличие пула(ов) с минимальными требованиями (ликвидность, активность) по данным Birdeye.
  - Метрика активности — количество транзакций за 5 минут: `tx_count_5m`.
  - Условие: ликвидность ≥ `min_active_liquidity` ИЛИ `tx_count_5m` ≥ `min_tx_count` (оба порога задаются в настройках).
  - При выполнении условий — обновляем `status=Active`, фиксируем `activated_at`.

- Мониторинг активных токенов
  - По расписанию запрашиваем метрики с кешем Birdeye; обновляем `*_snapshots` и считаем скор; пишем в `token_scores` и `tokens.last_score_value`.

- Понижение статуса до Archived
  - Условия низкой активности оцениваются по 5‑минутному окну: `tx_count_5m` < `min_tx_count` и/или `EWMA(score)` < `min_score_keep_active`.
  - Если одно из условий держится N последовательных проверок в пределах окна `degrade_window_hours`, переводим в `Archived`.

- Админка
  - Обновляет веса, альфу EWMA, пороги в `settings` (включая `min_tx_count` для 5‑минутного окна, `min_active_liquidity`, `min_score_keep_active`, `degrade_checks`, `degrade_window_hours`); изменения вступают в силу без рестарта.

- UI
  - Список активных токенов с основными метриками и скором; деталка — список пулов и недавняя динамика.

## 9. Деплой

- Окружение
  - Один Linux-сервер (Ubuntu/Debian), PostgreSQL 15, Python 3.11+, Nginx.

- Установка (без Docker)
  - Создать системного пользователя, развернуть код, создать venv, установить зависимости.
  - Применить миграции Alembic.

- Сервисы systemd (пример)
  - API (`tothemoon-api.service`): запуск `uvicorn app.main:app --host 0.0.0.0 --port 8000` из venv.
  - Фоновые задачи: в составе того же процесса (lifespan/startup) либо отдельный `--factory` воркер, если понадобится.

- Nginx (в общих чертах)
  - Reverse proxy на 8000; gzip; кэш статических файлов если появятся.

- Обновления
  - `git pull` → `alembic upgrade head` → перезапуск сервиса systemd.

## 10. Подход к конфигурированию

- Инструмент: Pydantic Settings + `.env` в dev; на prod — только переменные окружения.
- Основные переменные
  - `DB_DSN` — строка подключения PostgreSQL.
  - `BIRDEYE_API_KEY` — ключ API.
  - `PUMPPORTAL_WS_URL` — URL WebSocket (дефолт: `wss://pumpportal.fun/data-api/real-time`).
  - `LOG_LEVEL` — уровень логирования (дефолт INFO).
  - `BIRDEYE_CACHE_TTL` — TTL кеша (дефолт 30 сек).
  - `EXT_MAX_CONCURRENCY` — предел параллельных внешних запросов (дефолт 5–10).
  - `SCHED_INTERVAL_INITIAL_SEC` — период проверки Initial (дефолт 30 сек).
  - `SCHED_INTERVAL_ACTIVE_SEC` — период обновления активных (дефолт 30 сек).

- Правила
  - Не хранить секреты в репозитории; `.env` — только локально.
  - Конфигурация должна читаться на старте; часть параметров допускается в `settings` (БД) для онлайн-настройки.

## 11. Подход к логгированию

- Библиотека: стандартный `logging`.
- Формат: компактный JSON или ключ=значение; обязательные поля — `ts`, `level`, `msg`, `module`, `token` (если применимо), `request_id` (если есть).
- Уровни: INFO по умолчанию; DEBUG включается через конфиг.
- Ротация: ротация по размеру/времени средствами `logging.handlers`.
- Категории
  - `app.api` — входящие запросы/ответы (без чувствительных данных).
  - `app.services.birdeye` — вызовы и ошибки интеграции (статус-коды, ретраи).
  - `app.services.pumpportal` — события подписки и переподключения.
  - `app.services.scoring` — результаты расчёта скора (агрегировано, без спама).
- Маскирование: не логировать ключи API и персональные данные.
