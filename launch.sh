#!/usr/bin/env zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIBRECHAT_DIR="/Users/renau001/Documents/projects/ai/SRA/LibreChat"
LANGCHAIN_UI_DIR="./app"

echo "=== Starting services ==="

# 1. Launch gunicorn for the Flask app
echo "[1/3] Launching Flask app with gunicorn on port 8000..."
cd "$LANGCHAIN_UI_DIR"
gunicorn --worker-class gevent --workers 1 --bind 0.0.0:8000 app_stream:app \
    --daemon \
    --pid gunicorn.pid \
    --access-logfile - \
    --error-logfile -

echo "[+] Flask app running on http://localhost:8000"

# 2. Launch LibreChat
echo "[2/3] Launching LibreChat..."
cd "$LIBRECHAT_DIR"
docker compose up -d

echo "[+] LibreChat running on http://localhost:3080"

# 3. Open LibreChat in browser
echo "[3/3] Opening LibreChat in browser..."
open http://localhost:3080

echo ""
echo "=== All services started ==="
echo "  Flask app:  http://localhost:8000"
echo "  LibreChat:  http://localhost:3080"
