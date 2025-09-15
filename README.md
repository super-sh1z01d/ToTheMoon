# 🌙 ToTheMoon2

Система скоринга токенов Solana для выявления арбитражных возможностей.

## 📋 Статус разработки

**Текущая итерация:** 11 из 11 ✅  
**Состояние:** ГОТОВ К PRODUCTION ДЕПЛОЮ 🚀  

## 🚀 Быстрый старт (без Docker)

1) Установите зависимости (Ubuntu 20.04+):
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3 python3-venv python3-pip build-essential \
       postgresql postgresql-contrib redis-server \
       nodejs npm
   ```

2) Настройте PostgreSQL и Redis:
   - Убедитесь, что сервисы запущены: `sudo systemctl enable --now postgresql redis-server`
   - Создайте БД/пользователя или используйте готовый `DATABASE_URL` (см. `.env` пример)

3) Клонируйте проект и подготовьте окружение:
   ```bash
   sudo mkdir -p /opt/tothemoon2 && cd /opt/tothemoon2
   git clone https://github.com/super-sh1z01d/ToTheMoon2.git .
   cp environment.example .env
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

4) Примените миграции БД:
   ```bash
   # Убедитесь, что в .env задан корректный DATABASE_URL
   python3 scripts/migrate.py
   ```

5) Запустите backend и фоновые задачи:
   ```bash
   # Терминал 1 (backend API)
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

   # Терминал 2 (Celery worker)
   python3 scripts/start_celery.py worker

   # Терминал 3 (Celery beat)
   python3 scripts/start_celery.py beat
   ```

6) Frontend:
   ```bash
   cd frontend
   npm ci || npm install
   npm run dev   # dev-сервер на http://localhost:3000
   # или production-сборка:
   npm run build # статика в frontend/dist
   ```

7) (Опционально) Настройте системный Nginx для раздачи статики и прокси на API.
   Воспользуйтесь примером `deploy/nginx-system.conf`.

Альтернатива: один скрипт установки (root, Ubuntu)
```bash
sudo bash scripts/install_nodocker.sh
```

Полезные URL:
- API Docs: http://localhost:8000/api/docs
- Health: http://localhost:8000/health
- TOML конфиг: http://localhost:8000/config/dynamic_strategy.toml
- Realtime WS: ws://localhost:8000/api/realtime/ws

## 🏗️ Архитектура

- **Backend:** FastAPI + Python 3.11
- **Database:** PostgreSQL (оптимизировано под 2 ГБ RAM)
- **Cache:** Redis
- **Frontend:** React + TypeScript + Tailwind CSS (с админ-панелью)
- **Background Jobs:** Celery + Redis (оптимизированно под 2 ГБ RAM)
- **WebSocket:** PumpPortal.fun интеграция
- **Scoring Engine:** Модульная система с EWMA сглаживанием
- **Lifecycle Manager:** Автоматический мониторинг статусов токенов
- **TOML Export:** Автоматическая генерация конфигурации для NotArb бота
- **Real-time Updates:** WebSocket + Redis Pub/Sub для UI обновлений
- **Celery Monitoring:** Мониторинг workers и производительности
- **Web Server:** Nginx (с кешированием TOML и SSL ready)
- **Orchestration:** без Docker (системные сервисы / systemd)

## 📁 Структура проекта

```
ToTheMoon2/
├── backend/           # FastAPI приложение
├── frontend/          # React приложение  
├── deploy/           # Примеры системной конфигурации (nginx)
├── doc/              # Документация
├── scripts/          # Утилиты деплоя
├── logs/             # Логи приложения
└── .env
```

## 🔧 Разработка

### Полезные команды

```bash
# Backend API (из папки backend)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Celery
python3 scripts/start_celery.py worker
python3 scripts/start_celery.py beat

# Тестирование API endpoints
python3 scripts/test_api_requests.py

# WebSocket интеграция
python3 scripts/test_websocket.py --mode simple

# Birdeye API интеграция
python3 scripts/test_birdeye.py --mode quick

# Scoring Engine тестирование
python3 scripts/test_scoring.py --mode quick

# Lifecycle System тестирование
python3 scripts/test_lifecycle.py --mode quick

# TOML Export тестирование
python3 scripts/test_toml_export.py --mode quick

# Тест TOML endpoint (с работающим сервером)
curl http://localhost:8000/config/dynamic_strategy.toml

# Управление Celery workers
python3 scripts/celery_manager.py status
python3 scripts/celery_manager.py production
python3 scripts/celery_manager.py development

# Мониторинг Celery производительности
curl http://localhost:8000/api/celery/status
curl http://localhost:8000/api/celery/performance

# Health check Celery системы
curl -X POST http://localhost:8000/api/celery/health-check
curl -X POST http://localhost:8000/api/celery/stress-test

# Проверка использования памяти (локально)
ps aux | grep celery
free -h

# E2E тестирование всех сценариев
python3 scripts/test_e2e_all_scenarios.py --mode full

# Оптимизация производительности
python3 scripts/optimize_performance.py --mode all
```

## 🚀 Production деплой (без Docker)

Кратко:
- Настройте `.env` (DATABASE_URL, REDIS_URL, ключи API и SECRET_KEY)
- Примените миграции `python3 scripts/migrate.py`
- Запустите Uvicorn, Celery worker и Celery beat как systemd-сервисы
- (Опционально) Настройте Nginx, используя `deploy/nginx-system.conf`

### CI/CD через GitHub Actions

1. **Настройте GitHub Secrets:**
   - `VPS_SSH_KEY` - SSH ключ для VPS
   - `VPS_HOST` - адрес VPS (tothemoon.sh1z01d.ru)
   - `VPS_USER` - пользователь VPS (root)
   - `VPS_PROJECT_PATH` - путь проекта (/opt/tothemoon2)
   - `DATABASE_PASSWORD` - пароль БД
   - `SECRET_KEY` - секретный ключ приложения
   - `BIRDEYE_API_KEY` - ключ Birdeye API
   - `TELEGRAM_BOT_TOKEN` - токен Telegram бота (для уведомлений)
   - `TELEGRAM_CHAT_ID` - ID чата для уведомлений

2. **Push в main ветку** автоматически запустит деплой

### Production URLs

```
Main: https://tothemoon.sh1z01d.ru
API Docs: https://tothemoon.sh1z01d.ru/api/docs
Bot Config: https://tothemoon.sh1z01d.ru/config/dynamic_strategy.toml
Health Check: https://tothemoon.sh1z01d.ru/health
Real-time WS: wss://tothemoon.sh1z01d.ru/api/realtime/ws
```

### Мониторинг

- **Логи приложения:** `./logs/`
- **Health check:** `/health`
- **API документация:** `/api/docs`

## 📚 Документация

- [Техническое видение](./doc/vision.md)
- [Соглашения разработки](./doc/conventions.md)
- [План разработки](./doc/tasklist.md)
- [Функциональное задание](./doc/functional_task.md)
- [Интеграция с NotArb ботом](./doc/bot_integration.md)

## ✅ Завершенные итерации

1. ✅ Базовая инфраструктура (PostgreSQL, Redis)
2. ✅ Модели данных и миграции (SQLAlchemy, Alembic)
3. ✅ FastAPI базовый сервер (CRUD, API endpoints)
4. ✅ React фронтенд (MVP) (TypeScript, Tailwind CSS)
5. ✅ WebSocket интеграция (PumpPortal.fun)
6. ✅ Birdeye API интеграция (метрики токенов)
7. ✅ Scoring Engine (Hybrid Momentum v1)
8. ✅ Админ-панель + Lifecycle (управление параметрами)
9. ✅ TOML экспорт для бота (NotArb интеграция)
10. ✅ Celery workers (оптимизация производительности)
11. ✅ Финальная интеграция (production ready)

## 🤝 Принципы разработки

- **KISS** - Keep It Simple, Stupid
- **Никакого оверинжиниринга**
- **Модульность** - особенно для scoring engine
- **Простота превыше всего**

## 📞 Поддержка

При возникновении проблем:
1. Проверьте что Postgres/Redis активны: `systemctl status postgresql redis-server`
2. Убедитесь, что `.env` корректен (DATABASE_URL, REDIS_URL)
3. Проверьте логи backend/Celery и Nginx (если используется)
