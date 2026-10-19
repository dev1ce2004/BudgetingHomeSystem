@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Prvo pokreni Instaliraj.bat.
 pause
 exit /b 1
)
.venv\Scripts\python.exe server.py --ip 192.168.0.31 %*
pause
