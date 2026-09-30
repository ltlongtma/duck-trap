#!/usr/bin/env bash
# Cài đặt (lần đầu) + chạy Duck Trap. Dùng trên máy Mac của mày.
set -euo pipefail

cd "$(dirname "$0")"

# Duck Trap cần tkinter (GUI). Một số bản Python (vd Homebrew python@3.14)
# KHÔNG kèm tkinter, nên ta đi tìm bản Python nào có sẵn tkinter.
has_tk() {
  "$1" -c "import tkinter" >/dev/null 2>&1
}

find_python() {
  # Cho phép chỉ định tay: DUCKTRAP_PYTHON=/path/to/python ./run.sh
  if [ -n "${DUCKTRAP_PYTHON:-}" ] && has_tk "${DUCKTRAP_PYTHON}"; then
    echo "${DUCKTRAP_PYTHON}"; return 0
  fi
  for cand in \
    python3.12 python3.11 python3.13 python3.10 \
    /usr/bin/python3 \
    /opt/homebrew/bin/python3 /usr/local/bin/python3 \
    python3; do
    if command -v "$cand" >/dev/null 2>&1 && has_tk "$cand"; then
      command -v "$cand"; return 0
    fi
  done
  return 1
}

PY="$(find_python || true)"

if [ -z "${PY:-}" ]; then
  cat >&2 <<'EOF'
[Duck Trap] Không tìm thấy bản Python 3 nào có sẵn tkinter (GUI).

Cách sửa (chọn 1):
  • Nếu dùng Homebrew Python:  brew install python-tk
    (theo đúng phiên bản, vd:   brew install python-tk@3.14)
  • Hoặc dùng Python của macOS:  DUCKTRAP_PYTHON=/usr/bin/python3 ./run.sh
  • Hoặc cài Python có Tk:       brew install python-tk python@3.12

Sau đó chạy lại ./run.sh
EOF
  exit 1
fi

echo "[Duck Trap] Dùng Python: $PY"

# Nếu .venv cũ được tạo bằng Python KHÔNG có tkinter (vd python@3.14),
# thì bỏ đi dựng lại bằng bản Python tốt vừa tìm được.
if [ -d ".venv" ] && ! has_tk "./.venv/bin/python"; then
  echo "[Duck Trap] .venv cũ thiếu tkinter -> dựng lại…"
  rm -rf .venv
fi

if [ ! -d ".venv" ]; then
  echo "[Duck Trap] Tạo virtualenv lần đầu…"
  "$PY" -m venv .venv
  ./.venv/bin/pip install --upgrade pip >/dev/null
  ./.venv/bin/pip install -r requirements.txt
fi

# venv kế thừa tkinter từ bản Python đã chọn, nên chạy trực tiếp.
exec ./.venv/bin/python -m duck_trap "$@"
