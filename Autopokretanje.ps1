$root = $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\pythonw.exe'
if (!(Test-Path $python)) { throw 'Prvo pokreni Instaliraj.bat.' }
$startup = [Environment]::GetFolderPath('Startup')
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut((Join-Path $startup 'BudgetingHomeSystem.lnk'))
$link.TargetPath = $python
$link.Arguments = '"' + (Join-Path $root 'server.py') + '"'
$link.WorkingDirectory = $root
$link.Save()
Write-Host 'Servis se pokrece nakon prijave u Windows. Uklanjanje: obrisi BudgetingHomeSystem.lnk iz shell:startup.'
