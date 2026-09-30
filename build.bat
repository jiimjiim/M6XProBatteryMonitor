@echo off
setlocal
chcp 65001 >nul
echo Building M6X Battery Monitor...
python generate_app_icon.py
if errorlevel 1 goto failed
python -m PyInstaller --noconsole --onefile --clean --exclude-module numpy --add-data "app_icon.ico;." --icon=app_icon.ico --name=M6X_Battery_Monitor main.py
if errorlevel 1 goto failed
taskkill /f /im M6X_Battery_Monitor.exe >nul 2>nul
copy /y "dist\M6X_Battery_Monitor.exe" "%USERPROFILE%\Desktop\M6X_Battery_Monitor.exe" >nul
if errorlevel 1 goto failed
echo Build complete: %USERPROFILE%\Desktop\M6X_Battery_Monitor.exe
exit /b 0

:failed
echo Build failed. Check Python, Pillow, hid, pystray, and PyInstaller installation.
exit /b 1
