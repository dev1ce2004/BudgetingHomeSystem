@echo off
cd /d "%~dp0"
py -3 --version >nul 2>&1
if errorlevel 1 (
 echo Instaliraj Python 3.10 ili noviji s python.org pa pokreni ponovno.
 pause
 exit /b 1
)
py -3 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Instalacija zavrsena. Pokreni Pokreni.bat.
pause
exit /b 0
:fail
echo Instalacija nije uspjela. Provjeri internet i poruku iznad.
pause
exit /b 1
