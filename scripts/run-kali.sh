#!/usr/bin/env bash
# Run AI Project Management app from WSL Kali Linux
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "[*] TaskPilot — WSL Kali launcher"
echo "[*] Project: $PROJECT_DIR"

if [ ! -d "venv" ]; then
  echo "[*] Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "[*] Created .env from .env.example"
fi

export FLASK_HOST="${FLASK_HOST:-0.0.0.0}"
export FLASK_PORT="${FLASK_PORT:-5000}"

echo ""
echo "  Login:  http://127.0.0.1:${FLASK_PORT}/login/"
echo "  App:    http://127.0.0.1:${FLASK_PORT}/"
echo "  (Use any email/password, or set DEMO_EMAIL / DEMO_PASSWORD in .env)"
echo ""

python run.py
