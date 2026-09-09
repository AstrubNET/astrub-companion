$ErrorActionPreference = 'Stop'

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $PSCommandPath + '"'))
    exit
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Show-Error([string]$Message) {
    [System.Windows.Forms.MessageBox]::Show($Message, 'Astrub Companion', 'OK', 'Error') | Out-Null
}

$npcap = Join-Path $env:WINDIR 'System32\Npcap\wpcap.dll'
if (-not (Test-Path $npcap)) {
    $choice = [System.Windows.Forms.MessageBox]::Show(
        "Astrub Companion a besoin de Npcap pour l'écoute passive.`r`n`r`nL'installateur officiel va être téléchargé directement depuis npcap.com. Son assistant restera visible car l'édition gratuite ne permet pas une installation silencieuse.",
        'Installation de Npcap',
        'OKCancel',
        'Information'
    )
    if ($choice -ne 'OK') { exit }
    $npcapInstaller = Join-Path $env:TEMP 'astrub-npcap-installer.exe'
    try {
        $downloadPage = Invoke-WebRequest -Uri 'https://npcap.com/' -UseBasicParsing -TimeoutSec 20
        $match = [regex]::Match($downloadPage.Content, 'href=["''](?<url>[^"'']*/dist/npcap-[0-9.]+\.exe)["'']', 'IgnoreCase')
        if (-not $match.Success) { throw "Lien officiel Npcap introuvable." }
        $downloadUri = [Uri]::new([Uri]'https://npcap.com/', $match.Groups['url'].Value)
        if ($downloadUri.Scheme -ne 'https' -or $downloadUri.Host -ne 'npcap.com') { throw "Adresse Npcap non fiable." }
        Invoke-WebRequest -Uri $downloadUri.AbsoluteUri -OutFile $npcapInstaller -UseBasicParsing -TimeoutSec 120
        $signature = Get-AuthenticodeSignature -FilePath $npcapInstaller
        if ($signature.Status -ne 'Valid') { throw "La signature numérique de Npcap n'est pas valide." }
        $process = Start-Process -FilePath $npcapInstaller -Wait -PassThru
        if ($process.ExitCode -ne 0 -or -not (Test-Path $npcap)) { throw "L'installation de Npcap n'a pas été terminée." }
    } catch {
        Show-Error "Npcap n'a pas pu être installé.`r`n$($_.Exception.Message)"
        exit 1
    } finally {
        Remove-Item -LiteralPath $npcapInstaller -Force -ErrorAction SilentlyContinue
    }
}

try {
    $response = Invoke-RestMethod -Uri 'https://www.astrub.net/api/companion/servers.php' -TimeoutSec 15
    $servers = @($response.servers)
} catch {
    Show-Error "Impossible de télécharger la liste des serveurs Astrub.net.`n$($_.Exception.Message)"
    exit 1
}
if ($servers.Count -eq 0) { Show-Error 'Aucun serveur actif disponible.'; exit 1 }

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Installation — Astrub Companion'
$form.Size = New-Object System.Drawing.Size(570,330)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false

$intro = New-Object System.Windows.Forms.Label
$intro.Location = New-Object System.Drawing.Point(25,20)
$intro.Size = New-Object System.Drawing.Size(510,105)
$intro.Text = "Astrub Companion écoute passivement le trafic local de Dofus pour reconnaître les prix HDV consultés, achetés ou mis en vente.`r`n`r`nAucun clic, aucune injection, aucun identifiant Ankama et aucun fichier PCAP. Seules les données de prix décrites dans PRIVACY.md sont envoyées à Astrub.net."
$form.Controls.Add($intro)

$label = New-Object System.Windows.Forms.Label
$label.Location = New-Object System.Drawing.Point(25,140)
$label.Size = New-Object System.Drawing.Size(510,22)
$label.Text = 'Choisis ton serveur Dofus :'
$form.Controls.Add($label)

$combo = New-Object System.Windows.Forms.ComboBox
$combo.Location = New-Object System.Drawing.Point(25,165)
$combo.Size = New-Object System.Drawing.Size(510,28)
$combo.DropDownStyle = 'DropDownList'
foreach ($server in $servers) { [void]$combo.Items.Add(('{0} — {1}' -f [int]$server.id, [string]$server.name)) }
$combo.SelectedIndex = 0
$form.Controls.Add($combo)

$cancel = New-Object System.Windows.Forms.Button
$cancel.Location = New-Object System.Drawing.Point(345,225)
$cancel.Size = New-Object System.Drawing.Size(90,32)
$cancel.Text = 'Annuler'
$cancel.DialogResult = 'Cancel'
$form.Controls.Add($cancel)
$form.CancelButton = $cancel

$install = New-Object System.Windows.Forms.Button
$install.Location = New-Object System.Drawing.Point(445,225)
$install.Size = New-Object System.Drawing.Size(90,32)
$install.Text = "J'accepte"
$install.DialogResult = 'OK'
$form.Controls.Add($install)
$form.AcceptButton = $install

if ($form.ShowDialog() -ne 'OK') { exit }
$selected = $servers[$combo.SelectedIndex]

$installDir = Join-Path $env:ProgramData 'Astrub Companion'
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'astrub_companion.py') (Join-Path $installDir 'astrub_companion.py') -Force

$sourceExe = Join-Path $PSScriptRoot 'AstrubCompanion.exe'
$targetExe = Join-Path $installDir 'AstrubCompanion.exe'
$usingExe = Test-Path $sourceExe
if ($usingExe) { Copy-Item $sourceExe $targetExe -Force }

$configPath = Join-Path $installDir 'config.json'
$deviceId = [guid]::NewGuid().ToString()
if (Test-Path $configPath) {
    try {
        $old = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($old.device_id) { $deviceId = [string]$old.device_id }
    } catch {}
}
$config = [ordered]@{
    api_url = 'https://www.astrub.net/api/companion/prices.php'
    server_id = [int]$selected.id
    server_name = [string]$selected.name
    device_id = $deviceId
    selection_ttl_seconds = 120
    purchase_ttl_seconds = 20
    market_view_ttl_seconds = 20
    market_view_dedupe_seconds = 300
}
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($configPath, ($config | ConvertTo-Json), $utf8NoBom)

if ($usingExe) {
    $action = New-ScheduledTaskAction -Execute $targetExe -Argument ('--config "' + $configPath + '"')
} else {
    $python = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if (-not $python) { $python = Get-Command python.exe -ErrorAction SilentlyContinue }
    if (-not $python) {
        Show-Error "Python 3 est requis lorsque l'exécutable précompilé n'est pas présent. Installe Python depuis python.org en cochant Add Python to PATH."
        exit 1
    }
    $action = New-ScheduledTaskAction -Execute $python.Source -Argument ('"' + (Join-Path $installDir 'astrub_companion.py') + '" --config "' + $configPath + '"')
}
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable
Register-ScheduledTask -TaskName 'Astrub Companion' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName 'Astrub Companion'

[System.Windows.Forms.MessageBox]::Show("Installation terminée pour $($selected.name) (ID $($selected.id)).`n`nAstrub Companion fonctionne maintenant en arrière-plan.", 'Astrub Companion', 'OK', 'Information') | Out-Null
