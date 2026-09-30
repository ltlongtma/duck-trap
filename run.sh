#!/usr/bin/env bash
# Install (first run) and launch Duck Trap. For use on your Mac.
set -euo pipefail

cd "$(dirname "$0")"

# Duck Trap needs tkinter (GUI) with Tk >= 8.6.
#  - Homebrew python@3.14 ships WITHOUT tkinter -> rejected.
#  - macOS system Python 3.9 uses the OLD Tk 8.5 (fullscreen broken) -> rejected.
# So we look for a Python that has tkinter and Tk >= 8.6.
has_tk() {
  "$1" - >/dev/null 2>&1 <<'PY'
import sys, tkinter
r = tkinter.Tk(); r.withdraw()
v = r.tk.call("info", "patchlevel")
r.destroy()
major, minor = (int(x) for x in v.split(".")[:2])
sys.exit(0 if (major, minor) >= (8, 6) else 1)
PY
}

find_python() {
  # Allow manual override: DUCKTRAP_PYTHON=/path/to/python ./run.sh
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
[Duck Trap] No Python 3 with a working tkinter (Tk >= 8.6) was found.

Fix (pick one):
  - Homebrew Python:      brew install python-tk
    (matching version:    brew install python-tk@3.14)
  - macOS system Python:  DUCKTRAP_PYTHON=/usr/bin/python3 ./run.sh
  - Install Python + Tk:  brew install python-tk python@3.12

Then run ./run.sh again.
EOF
  exit 1
fi

echo "[Duck Trap] Using Python: $PY"

# If the existing .venv was built with a Python without tkinter (or old Tk),
# discard it and rebuild with the good Python found above.
if [ -d ".venv" ] && ! has_tk "./.venv/bin/python"; then
  echo "[Duck Trap] Existing .venv lacks a usable tkinter -> rebuilding..."
  rm -rf .venv
fi

if [ ! -d ".venv" ]; then
  echo "[Duck Trap] Creating virtualenv (first run)..."
  "$PY" -m venv .venv
  ./.venv/bin/pip install --upgrade pip >/dev/null
  ./.venv/bin/pip install -r requirements.txt
fi

# The venv inherits tkinter from the chosen Python, so run it directly.
exec ./.venv/bin/python -m duck_trap "$@"
