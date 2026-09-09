param([ValidateSet('pause','resume')][string]$Action)
$ErrorActionPreference = 'Stop'
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $PSCommandPath + '"'),'-Action',$Action)
    exit
}
if ($Action -eq 'pause') {
    Stop-ScheduledTask -TaskName 'Astrub Companion' -ErrorAction SilentlyContinue
    Disable-ScheduledTask -TaskName 'Astrub Companion' | Out-Null
} else {
    Enable-ScheduledTask -TaskName 'Astrub Companion' | Out-Null
    Start-ScheduledTask -TaskName 'Astrub Companion'
}
