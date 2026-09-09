$ErrorActionPreference = 'SilentlyContinue'
Stop-ScheduledTask -TaskName 'Astrub Companion'
Unregister-ScheduledTask -TaskName 'Astrub Companion' -Confirm:$false
$path = Join-Path $env:ProgramData 'Astrub Companion'
Remove-Item -LiteralPath $path -Recurse -Force
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show('Astrub Companion a été entièrement désinstallé. Npcap a été conservé car il peut être utilisé par Wireshark ou d’autres logiciels.', 'Astrub Companion') | Out-Null
