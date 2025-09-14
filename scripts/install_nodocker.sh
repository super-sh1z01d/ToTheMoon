#!/usr/bin/env bash
set -euo pipefail

# One‑shot installer for ToTheMoon2 without Docker
# Installs system deps (optional), Python venv, requirements, applies DB migrations,
# and installs systemd services for backend + Celery.

PROJECT_DIR="/opt/tothemoon2"
PYTHON_BIN="python3"

echo "=== ToTheMoon2 Non-Docker Installer ==="

if [[ $EUID -ne 0 ]]; then
  echo "[i] Not running as root. System packages and systemd steps may fail."
  echo "[i] Re-run with sudo for full installation if needed."
fi

read -r -p "Install system packages (postgresql, redis, nginx, python, node)? [Y/n] " ans
ans=${ans:-Y}
if [[ "$ans" =~ ^[Yy]$ ]]; then
  apt update && apt install -y \
    python3 python3-venv python3-pip build-essential \
    postgresql postgresql-contrib redis-server \
    nginx certbot python3-certbot-nginx \
    nodejs npm git curl || true
  systemctl enable --now postgresql redis-server nginx || true
fi

mkdir -p "$PROJECT_DIR"
if [[ ! -d "$PROJECT_DIR/.git" ]]; then
  echo "[i] Copy project into $PROJECT_DIR (expecting current repo checkout)..."
  # If the script is run from repo root, copy it.
  SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
  rsync -a --exclude .venv --exclude node_modules --exclude logs "$SRC_DIR"/ "$PROJECT_DIR"/
fi

cd "$PROJECT_DIR"

if [[ ! -f ".env" ]]; then
  echo "[i] Creating .env from environment.example"
  cp environment.example .env
  echo "[!] Edit $PROJECT_DIR/.env before starting services (DATABASE_URL, REDIS_URL, SECRET_KEY, API keys)"
fi

if [[ ! -d ".venv" ]]; then
  echo "[i] Creating Python virtualenv"
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "[i] Applying DB migrations"
"$PYTHON_BIN" scripts/migrate.py || true

echo "[i] Installing systemd services"
install -m 0644 deploy/systemd/tothemoon2-backend.service /etc/systemd/system/tothemoon2-backend.service || true
install -m 0644 deploy/systemd/tothemoon2-celery-worker.service /etc/systemd/system/tothemoon2-celery-worker.service || true
install -m 0644 deploy/systemd/tothemoon2-celery-beat.service /etc/systemd/system/tothemoon2-celery-beat.service || true

systemctl daemon-reload || true
systemctl enable --now tothemoon2-backend tothemoon2-celery-worker tothemoon2-celery-beat || true

echo "=== Done ==="
echo "- Backend: http://localhost:8000/api/docs"
echo "- Health:  http://localhost:8000/health"
echo "- TOML:    http://localhost:8000/config/dynamic_strategy.toml"

