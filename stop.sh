#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIBRECHAT_DIR="/Users/renau001/Documents/projects/ai/SRA/LibreChat"
LANGCHAIN_UI_DIR="./app"

echo "=== Stopping services ==="

# 1. Stop gunicorn
if [ -f "$LANGCHAIN_UI_DIR/gunicorn.pid" ]; then
    echo "[1/3] Stopping Flask app..."
    kill "$(cat "$LANGCHAIN_UI_DIR/gunicorn.pid")" 2>/dev/null || true
    rm -f "$LANGCHAIN_UI_DIR/gunicorn.pid"
    echo "[+] Flask app stopped"
else
    echo "[1/3] Flask app not running (no PID file)"
fi

# 2. Stop LibreChat
echo "[2/3] Stopping LibreChat..."
cd "$LIBRECHAT_DIR"
docker compose down
echo "[+] LibreChat stopped"

echo ""
echo "=== All services stopped ==="
