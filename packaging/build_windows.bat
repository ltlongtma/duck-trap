@echo off
REM Đóng gói Duck Trap thành DuckTrap.exe (chạy trên máy Windows).
REM Cần Python 3.10+ đã cài. Double-click file này hoặc chạy trong cmd.

cd /d "%~dp0\.."

python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller packaging\DuckTrap.spec --noconfirm

echo.
echo ===============================================
echo  Xong! File nam o: dist\DuckTrap.exe
echo  Copy DuckTrap.exe (va anh trap.png neu muon) di dung.
echo ===============================================
pause
