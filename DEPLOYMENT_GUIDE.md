# 🚀 Руководство по деплою ToTheMoon2 (без Docker)

Это краткое руководство по развертыванию ToTheMoon2 на Ubuntu 20.04+ без контейнеров.

## 1) Предварительные требования

- VPS: 2GB RAM, Ubuntu 20.04+
- Домены/HTTPS (опционально): Nginx + certbot
- Ключи API: Birdeye

Установка системных зависимостей:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  python3 python3-venv python3-pip build-essential \
  postgresql postgresql-contrib redis-server \
  nginx certbot python3-certbot-nginx git curl nodejs npm
sudo systemctl enable --now postgresql redis-server nginx
```

## 2) Клонирование и конфигурация

```bash
sudo mkdir -p /opt/tothemoon2 && cd /opt/tothemoon2
git clone https://github.com/super-sh1z01d/ToTheMoon2.git .
cp environment.example .env

# Обязательно проверьте .env:
# - DATABASE_URL=postgresql://user:pass@localhost:5432/tothemoon
# - REDIS_URL=redis://localhost:6379/0
# - CELERY_BROKER_URL=redis://localhost:6379/1
# - CELERY_RESULT_BACKEND=redis://localhost:6379/2
# - SECRET_KEY=<случайная_строка>
```

Создание Python окружения и миграции БД:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python3 scripts/migrate.py
```

## 3) Запуск сервисов

Ручной запуск:
```bash
# Backend API
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

# Отдельные терминалы:
python3 scripts/start_celery.py worker
python3 scripts/start_celery.py beat
```

Опционально: Systemd юниты (пример)
```ini
# /etc/systemd/system/tothemoon2-backend.service
[Unit]
Description=ToTheMoon2 Backend API
After=network.target postgresql.service redis-server.service

[Service]
WorkingDirectory=/opt/tothemoon2/backend
EnvironmentFile=/opt/tothemoon2/.env
ExecStart=/opt/tothemoon2/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always

[Install]
WantedBy=multi-user.target
```

Аналогично создайте юниты для celery worker/beat (см. README).

Альтернатива: однострочная установка (root)
```bash
sudo bash scripts/install_nodocker.sh
```

## 4) Frontend

```bash
cd /opt/tothemoon2/frontend
npm ci || npm install
npm run build   # сборка в dist/
```

## 5) Nginx (опционально)

Используйте пример `deploy/nginx-system.conf` для проксирования `http://127.0.0.1:8000` и раздачи `frontend/dist`.
```bash
sudo cp deploy/nginx-system.conf /etc/nginx/sites-available/tothemoon2
sudo ln -s /etc/nginx/sites-available/tothemoon2 /etc/nginx/sites-enabled/tothemoon2
sudo nginx -t && sudo systemctl reload nginx

# HTTPS через certbot
sudo certbot --nginx -d your.domain --agree-tos -m admin@your.domain
```

## 6) Проверка

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/system/stats
curl http://localhost:8000/config/dynamic_strategy.toml
```

Готово! Система работает без Docker.
