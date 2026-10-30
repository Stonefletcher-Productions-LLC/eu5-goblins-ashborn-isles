[CmdletBinding()]
param([string]$GamePath, [switch]$PrepareOnly, [string]$UserDataPath)
$ErrorActionPreference = 'Stop'
$modSlug = 'goblins_ashborn_isles'
$modId = 'alex.goblins_ashborn_isles'
$acceptedIds = @($modId, 'alex.cindermaw_demo')
if (-not $PrepareOnly -and (Get-Process -Name eu5 -ErrorAction SilentlyContinue)) { throw 'Close Europa Universalis V before installing.' }
$modSource = Join-Path $PSScriptRoot $modSlug
if (-not (Test-Path -LiteralPath $modSource)) { $modSource = Join-Path $PSScriptRoot "build\$modSlug" }
if (-not (Test-Path -LiteralPath (Join-Path $modSource '.metadata\metadata.json'))) {
    $releaseRoot = Join-Path $PSScriptRoot '.release'
    $releaseManifest = Join-Path $releaseRoot 'manifest.json'
    if (-not (Test-Path -LiteralPath $releaseManifest)) {
        throw 'This source checkout has no built mod. Use a prepared install archive for this version, or build the mod first.'
    }
    $release = Get-Content -LiteralPath $releaseManifest -Raw | ConvertFrom-Json
    if ($release.version -notmatch '^\d+(\.\d+){2,3}$') { throw 'Invalid release version.' }
    $configPath = Join-Path $PSScriptRoot 'data\island.json'
    if (Test-Path -LiteralPath $configPath) {
        $configText = [IO.File]::ReadAllText($configPath).Replace("`r`n", "`n")
        $config = $configText | ConvertFrom-Json
        if ($config.version -ne $release.version) { throw 'Bundled release version differs from source. Download an updated complete main archive.' }
        $hasher = [Security.Cryptography.SHA256]::Create()
        try { $configHash = [BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($configText))).Replace('-', '').ToLowerInvariant() }
        finally { $hasher.Dispose() }
        if (-not $release.source_config_sha256 -or $configHash -ne $release.source_config_sha256) { throw 'Bundled terrain configuration is stale. Download an updated complete main archive.' }
    }

    $assetName = "Goblins_Ashborn_Isles_$($release.version).zip"
    $assets = @($release.assets | Where-Object { $_.name -eq $assetName })
    if ($assets.Count -ne 1) { throw 'Missing prepared install archive in release manifest.' }
    $asset = $assets[0]
    $preparedRoot = Join-Path $PSScriptRoot ".prepared-release-$($release.version)"
    New-Item -ItemType Directory -Path $preparedRoot -Force | Out-Null
    $archivePath = Join-Path $preparedRoot $assetName
    Write-Host "Preparing the bundled $($release.version) release..."
    $archiveStream = [IO.File]::Open($archivePath, [IO.FileMode]::Create, [IO.FileAccess]::Write)
    try {
        foreach ($chunk in $asset.chunks) {
            if ($chunk -notmatch '^assets/[A-Za-z0-9_.-]+$') { throw 'Invalid archive chunk path.' }
            $bytes = [Convert]::FromBase64String([IO.File]::ReadAllText((Join-Path $releaseRoot $chunk)))
            $archiveStream.Write($bytes, 0, $bytes.Length)
        }
    } finally { $archiveStream.Dispose() }
    if ((Get-Item -LiteralPath $archivePath).Length -ne $asset.size -or (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash -ne $asset.sha256) {
        throw 'Bundled release archive failed its size/checksum check. Download the release again.'
    }
    Expand-Archive -LiteralPath $archivePath -DestinationPath $preparedRoot -Force
    $overlayManifestPath = Join-Path $PSScriptRoot 'data\main_overlay.json'
    if (Test-Path -LiteralPath $overlayManifestPath) {
        $overlay = Get-Content -LiteralPath $overlayManifestPath -Raw | ConvertFrom-Json
        if ($overlay.base_release -ne $release.version) { throw 'Main development files do not match the bundled release.' }
        $preparedMod = Join-Path $preparedRoot $modSlug
        foreach ($item in $overlay.files) {
            if ($item.path -notmatch '^[A-Za-z0-9_./-]+$' -or $item.path.StartsWith('/') -or $item.path.Split('/') -contains '..') { throw 'Invalid development file path.' }
            $authoredFile = Join-Path (Join-Path $PSScriptRoot 'mod') $item.path
            if ((Get-FileHash -LiteralPath $authoredFile -Algorithm SHA256).Hash -ne $item.sha256) { throw "Development file checksum mismatch: $($item.path)" }
            $preparedFile = Join-Path $preparedMod $item.path
            New-Item -ItemType Directory -Path (Split-Path -Parent $preparedFile) -Force | Out-Null
            Copy-Item -LiteralPath $authoredFile -Destination $preparedFile -Force
        }
        Write-Host 'Included main development updates: Ashborn culture names, infantry assets and culture-based goblin portraits.'
    }
    & (Join-Path $preparedRoot 'Install-Goblins.ps1') @PSBoundParameters
    return
}
$metadata = Get-Content -LiteralPath (Join-Path $modSource '.metadata\metadata.json') -Raw | ConvertFrom-Json
if ($metadata.id -ne $modId) { throw 'Unexpected source mod identity.' }
# EU5 1.4 terrain is a self-contained decal in the mod; no game files are patched.
if (Test-Path -LiteralPath (Join-Path $modSource 'in_game\gfx\terrain2\terrain_cache\heightmap.bin')) { throw 'This build carries the pre-1.4 terrain cache. Download an updated release.' }
foreach ($file in @('10_countries.txt','06_pops.txt','07_cities_and_buildings.txt','03_markets.txt')) {
    if (-not (Test-Path -LiteralPath (Join-Path $modSource "main_menu\setup\1337\$file"))) { throw "Incomplete build: $file" }
}
foreach ($file in @('ga_ashborn_isles\ga_ashborn_isles_height.info','ga_ashborn_isles\ga_ashborn_isles_height.bin','ga_ashborn_isles\ga_ashborn_isles_materials.info','ga_ashborn_isles\ga_ashborn_isles_materials.bin','decal_definitions.txt')) {
    if (-not (Test-Path -LiteralPath (Join-Path $modSource "in_game\gfx\terrain2\decals\$file"))) { throw "Incomplete build: island terrain $file" }
}
$musicManifestPath = Join-Path $modSource 'loading_screen\sound\goblins_music_manifest.json'
if (Test-Path -LiteralPath $musicManifestPath) {
    $candidates = [Collections.Generic.List[string]]::new()
    if ($GamePath) { $candidates.Add($GamePath) }
    $steam = (Get-ItemProperty -LiteralPath 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamPath
    if ($steam) {
        $candidates.Add((Join-Path $steam 'steamapps\common\Europa Universalis V\game'))
        $vdf = Join-Path $steam 'steamapps\libraryfolders.vdf'
        if (Test-Path -LiteralPath $vdf) {
            foreach ($match in [regex]::Matches((Get-Content -LiteralPath $vdf -Raw), '"path"\s+"([^"]+)"')) {
                $candidates.Add((Join-Path $match.Groups[1].Value.Replace('\\','\') 'steamapps\common\Europa Universalis V\game'))
            }
        }
    }
    $game = $candidates | Where-Object { Test-Path -LiteralPath (Join-Path $_ 'loading_screen\sound\banks\windows\sb_music_logic.bnk') } | Select-Object -First 1
    if (-not $game) { throw 'EU5 not found. Supply -GamePath pointing to its game directory.' }
    $musicManifest = Get-Content -LiteralPath $musicManifestPath -Raw | ConvertFrom-Json
    $nativeMusicBank = Join-Path $game 'loading_screen\sound\banks\windows\sb_music_logic.bnk'
    if ((Get-FileHash -LiteralPath $nativeMusicBank -Algorithm SHA256).Hash -ne $musicManifest.base_sha256) {
        throw 'EU5 music-bank version mismatch. This Goblins music build must be updated for your installed game.'
    }
    foreach ($dependency in @(
        @{ path = 'loading_screen\sound\banks\windows\Init.bnk'; hash = $musicManifest.init_base_sha256 },
        @{ path = 'in_game\gui\ingame_topbar.gui'; hash = $musicManifest.topbar_base_sha256 }
    )) {
        if (-not $dependency.hash -or (Get-FileHash -LiteralPath (Join-Path $game $dependency.path) -Algorithm SHA256).Hash -ne $dependency.hash) {
            throw "EU5 music dependency version mismatch: $($dependency.path). Update this Goblins build for your installed game."
        }
    }
}
if ($PrepareOnly) { Write-Host "Prepared Goblins of the Ashborn Isles $($metadata.version) at $modSource"; return }
if (-not $UserDataPath) { $UserDataPath = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Paradox Interactive\Europa Universalis V' }
$userRoot = [IO.Path]::GetFullPath($UserDataPath)
$modRoot = [IO.Path]::GetFullPath((Join-Path $userRoot 'mod'))
$target = [IO.Path]::GetFullPath((Join-Path $modRoot $modSlug))
$backupRoot = [IO.Path]::GetFullPath((Join-Path $userRoot 'goblins_backups'))
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$stage = [IO.Path]::GetFullPath((Join-Path $userRoot "goblins_staging_$stamp"))
if ([IO.Path]::GetDirectoryName($target) -ne $modRoot -or [IO.Path]::GetDirectoryName($stage) -ne $userRoot) { throw 'Invalid install paths.' }
foreach ($p in @($userRoot,$modRoot,$backupRoot,$target)) {
    if ((Test-Path -LiteralPath $p) -and ((Get-Item -LiteralPath $p).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Installation path is a link: $p" }
}
$previous = @()
foreach ($slug in @($modSlug,'cindermaw_demo')) {
    $old = [IO.Path]::GetFullPath((Join-Path $modRoot $slug))
    if (Test-Path -LiteralPath $old) {
        if ([IO.Path]::GetDirectoryName($old) -ne $modRoot -or ((Get-Item -LiteralPath $old).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Unsafe legacy install path.' }
        $oldMeta = Get-Content -LiteralPath (Join-Path $old '.metadata\metadata.json') -Raw | ConvertFrom-Json
        if ($oldMeta.id -notin $acceptedIds) { throw "Another mod occupies $old" }
        $previous += $old
    }
}
New-Item -ItemType Directory -Path $modRoot -Force | Out-Null
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
Copy-Item -LiteralPath $modSource -Destination $stage -Recurse
foreach ($file in Get-ChildItem -LiteralPath $modSource -File -Recurse -Force) {
    $relative = $file.FullName.Substring([IO.Path]::GetFullPath($modSource).TrimEnd('\').Length + 1)
    if ((Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath (Join-Path $stage $relative)).Hash) { throw "Staged install checksum mismatch: $relative" }
}
foreach ($old in $previous) {
    $backup = [IO.Path]::GetFullPath((Join-Path $backupRoot ((Split-Path $old -Leaf) + '_' + $stamp)))
    if ([IO.Path]::GetDirectoryName($backup) -ne $backupRoot) { throw 'Invalid backup path.' }
    Move-Item -LiteralPath $old -Destination $backup
    Write-Host "Previous mod preserved at $backup"
}
Move-Item -LiteralPath $stage -Destination $target
$playsetsPath = Join-Path $userRoot 'playsets.json'
if (Test-Path -LiteralPath $playsetsPath) {
    $playsets = Get-Content -LiteralPath $playsetsPath -Raw | ConvertFrom-Json
    $changed = $false
    foreach ($playset in $playsets.playsets) {
        foreach ($mod in $playset.orderedListMods) {
            $normalized = $mod.path.Replace('/', '\').TrimEnd('\')
            if ($normalized -eq (Join-Path $modRoot 'cindermaw_demo')) { $mod.path = $target.Replace('\','/') + '/'; $changed = $true }
        }
    }
    if ($changed) {
        Copy-Item -LiteralPath $playsetsPath -Destination (Join-Path $backupRoot "playsets_$stamp.json")
        $utf8 = New-Object System.Text.UTF8Encoding($false)
        [IO.File]::WriteAllText($playsetsPath, ($playsets | ConvertTo-Json -Depth 40), $utf8)
    }
}
Write-Host "Installed Goblins of the Ashborn Isles $($metadata.version) at $target"
Write-Host 'Restart EU5, enable only Goblins of the Ashborn Isles, and start a NEW 1337 campaign.'
