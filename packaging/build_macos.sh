#!/usr/bin/env bash
# Đóng gói Duck Trap thành DuckTrap.app (chạy trên máy Mac).
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller packaging/DuckTrap.spec --noconfirm

echo
echo "==============================================="
echo " Xong! App nằm ở: dist/DuckTrap.app"
echo " Double-click để chạy. Lần đầu macOS hỏi quyền Camera -> Allow."
echo "==============================================="
