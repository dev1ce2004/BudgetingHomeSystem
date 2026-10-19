@echo off
cd /d "%~dp0"
if not exist data\admin-access.txt (
 echo Prvo pokreni Pokreni.bat.
 pause
 exit /b 1
)
set /p BHS_URL=<data\admin-access.txt
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
 start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --app="%BHS_URL%"
) else (
 start "" "%BHS_URL%"
)
