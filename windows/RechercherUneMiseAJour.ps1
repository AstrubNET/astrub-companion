$ErrorActionPreference = 'Stop'

$installDir = Join-Path $env:ProgramData 'Astrub Companion'
$versionFile = Join-Path $installDir 'version'
$currentVersion = [version]'1.1.3'
if (Test-Path $versionFile) {
    try { $currentVersion = [version](Get-Content $versionFile -Raw).Trim().TrimStart('v') } catch {}
}

try {
    $headers = @{ Accept = 'application/vnd.github+json'; 'User-Agent' = 'Astrub-Companion-Updater/1.1.3' }
    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/AstrubNET/astrub-companion/releases/latest' -Headers $headers -TimeoutSec 15
    if ($release.draft -or $release.prerelease) { exit }
    $latestVersion = [version]([string]$release.tag_name).TrimStart('v')
    if ($latestVersion -le $currentVersion) { exit }
} catch { exit }

Add-Type -AssemblyName System.Windows.Forms
$choice = [System.Windows.Forms.MessageBox]::Show(
    "Astrub Companion $latestVersion est disponible.`r`n`r`nTélécharger la mise à jour depuis la release GitHub officielle ?",
    'Mise à jour Astrub Companion',
    'YesNo',
    'Information'
)
if ($choice -eq 'Yes') { Start-Process ([string]$release.html_url) }
