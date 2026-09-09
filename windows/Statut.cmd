@echo off
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$t=Get-ScheduledTask -TaskName 'Astrub Companion' -ErrorAction SilentlyContinue; if($t){Write-Host ('Astrub Companion : '+$t.State); Get-Content (Join-Path $env:ProgramData 'Astrub Companion\companion.log') -Encoding UTF8 -Tail 20 -ErrorAction SilentlyContinue}else{Write-Host 'Astrub Companion n''est pas installé.'}"
pause
