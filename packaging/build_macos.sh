#!/usr/bin/env bash
# Build Duck Trap into DuckTrap.app (run on a Mac).
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller packaging/DuckTrap.spec --noconfirm

echo
echo "==============================================="
echo " Done! App is at: dist/DuckTrap.app"
echo " Double-click to run. On first launch macOS asks for Camera -> Allow."
echo "==============================================="
