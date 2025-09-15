# ⚡ ToTheMoon2 — Быстрый старт (без Docker)

## 🎯 От чистой Ubuntu до работающей системы

```bash
# 1) Подготовка
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip build-essential \
    postgresql postgresql-contrib redis-server \
    nodejs npm git curl

# 2) Клонирование проекта
sudo mkdir -p /opt/tothemoon2 && cd /opt/tothemoon2
git clone https://github.com/super-sh1z01d/ToTheMoon2.git .

# 3) Настройка окружения
cp environment.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 4) Миграции БД (убедитесь, что .env содержит корректный DATABASE_URL)
python3 scripts/migrate.py

# 5) Запуск сервисов
# Терминал 1 — Backend API
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Терминал 2 — Celery worker
python3 scripts/start_celery.py worker

# Терминал 3 — Celery beat
python3 scripts/start_celery.py beat

# 6) Frontend
cd frontend
npm ci || npm install
npm run dev   # или npm run build (статическая сборка)
```

---

## 🌐 После установки доступны:

### Основные URL:
- **🏠 API Docs:** http://YOUR_VPS_IP:8000/api/docs
- **🤖 Bot Config:** http://YOUR_VPS_IP:8000/config/dynamic_strategy.toml  
- **💚 Health:** http://YOUR_VPS_IP:8000/health
- **📊 Stats:** http://YOUR_VPS_IP:8000/api/system/stats

### NotArb бот интеграция:
```python
import requests
import toml

# Получаем конфигурацию каждые 5 минут
response = requests.get("http://YOUR_VPS_IP:8000/config/dynamic_strategy.toml")
config = toml.loads(response.text)
active_tokens = config.get("tokens", [])
```

---

## 🔧 Управление системой (локально)

- Backend логи: в консоли uvicorn
- Celery логи: в консолях worker/beat
- Проверка API: `python3 scripts/test_api_requests.py`

---

## 📊 Технические характеристики:

- **🎯 Оптимизация:** 2GB RAM VPS
- **📊 Потребление:** ~800MB RAM
- **⚡ Производительность:** Обработка до 1000 токенов
- **🔄 Автоматизация:** Celery workers для background задач
- **🤖 API:** 15+ endpoints для управления
- **📡 Real-time:** WebSocket обновления

---

## 🚨 Устранение проблем:

**Система не запускается:**
```bash
systemctl status postgresql redis-server
python3 scripts/test_api_requests.py
```

**Высокое потребление памяти:**
```bash
python3 scripts/optimize_performance.py --mode analyze
free -h
```

**Проблемы с API:**
```bash
curl http://localhost:8000/health
python3 scripts/test_api_requests.py
```

---

## 🎉 Готово!

**ToTheMoon2 автоматически:**
- ✅ Обнаруживает токены через WebSocket
- ✅ Получает метрики от Birdeye API  
- ✅ Рассчитывает скоры по алгоритму Hybrid Momentum
- ✅ Управляет lifecycle токенов (Initial→Active→Archived)
- ✅ Экспортирует TOML конфигурацию для NotArb бота
- ✅ Мониторит производительность и здоровье системы

**Система готова к интеграции с арбитражными ботами! 🚀**
