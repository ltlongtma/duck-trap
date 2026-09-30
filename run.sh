#!/usr/bin/env bash
# Cài đặt (lần đầu) + chạy Duck Trap. Dùng trên máy Mac của mày.
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "[Duck Trap] Tạo virtualenv lần đầu…"
  python3 -m venv .venv
  ./.venv/bin/pip install --upgrade pip >/dev/null
  ./.venv/bin/pip install -r requirements.txt
fi

exec ./.venv/bin/python -m duck_trap "$@"
