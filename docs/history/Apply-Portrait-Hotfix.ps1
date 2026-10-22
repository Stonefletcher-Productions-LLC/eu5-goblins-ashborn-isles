[CmdletBinding()]
param([string]$UserDataPath = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Paradox Interactive\Europa Universalis V'))
$ErrorActionPreference = 'Stop'
if (Get-Process -Name eu5 -ErrorAction SilentlyContinue) { throw 'Close Europa Universalis V, then run this hotfix again.' }
$target = Join-Path $UserDataPath 'mod\goblins_ashborn_isles'
$metadata = Get-Content -LiteralPath (Join-Path $target '.metadata\metadata.json') -Raw | ConvertFrom-Json
if ($metadata.id -ne 'alex.goblins_ashborn_isles' -or $metadata.version -ne '0.5.2') { throw 'This hotfix is only for the installed Goblins 0.5.2 mod.' }
$paths = @('in_game/common/genes/zz_ashborn_portraits.txt', 'in_game/common/ethnicities/ashborn.txt')
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'data\main_overlay.json') -Raw | ConvertFrom-Json
foreach ($relative in $paths) {
    $source = Join-Path (Join-Path $PSScriptRoot 'mod') $relative
    $entry = @($manifest.files | Where-Object { $_.path -eq $relative })
    if ($entry.Count -ne 1 -or (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $entry[0].sha256) { throw "Hotfix source checksum mismatch: $relative" }
    if (-not (Test-Path -LiteralPath (Join-Path $target $relative))) { throw "Missing installed file: $relative" }
}
$backup = Join-Path $UserDataPath ('goblins_backups\portrait-hotfix-0.5.2-' + (Get-Date -Format 'yyyyMMdd-HHmmss-ffff'))
foreach ($relative in $paths) {
    $saved = Join-Path $backup $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $saved) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $target $relative) -Destination $saved
    if ((Get-FileHash -LiteralPath $saved).Hash -ne (Get-FileHash -LiteralPath (Join-Path $target $relative)).Hash) { throw "Backup verification failed: $relative" }
}
try {
    foreach ($relative in $paths) {
        $source = Join-Path (Join-Path $PSScriptRoot 'mod') $relative
        $installed = Join-Path $target $relative
        Copy-Item -LiteralPath $source -Destination $installed -Force
        if ((Get-FileHash -LiteralPath $source).Hash -ne (Get-FileHash -LiteralPath $installed).Hash) { throw "Installed checksum mismatch: $relative" }
    }
} catch {
    foreach ($relative in $paths) { Copy-Item -LiteralPath (Join-Path $backup $relative) -Destination (Join-Path $target $relative) -Force }
    throw
}
Write-Host 'Portrait hotfix installed. Restart EU5 and check a human ruler and all five goblin cultures. In-game appearance remains unverified.'
Write-Host "Original files backed up to $backup"
