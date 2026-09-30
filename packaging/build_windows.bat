@echo off
REM Build Duck Trap into DuckTrap.exe (run on a Windows machine).
REM Requires Python 3.10+ installed. Double-click this file or run it in cmd.

cd /d "%~dp0\.."

python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller packaging\DuckTrap.spec --noconfirm

echo.
echo ===============================================
echo  Done! File is at: dist\DuckTrap.exe
echo  Copy DuckTrap.exe (and an optional trap.png) to use it.
echo ===============================================
pause
