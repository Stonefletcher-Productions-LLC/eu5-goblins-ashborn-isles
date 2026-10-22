[CmdletBinding()]
param([switch]$PrepareOnly, [string]$UserDataPath, [string]$OutputPath)
$ErrorActionPreference = 'Stop'
$slug = 'goblins_055_prototype'
$id = 'alex.goblins_055_prototype'
if (-not $UserDataPath) {
    $UserDataPath = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Paradox Interactive\Europa Universalis V'
}
$userRoot = [IO.Path]::GetFullPath($UserDataPath)
$modRoot = [IO.Path]::GetFullPath((Join-Path $userRoot 'mod'))
$baseRoot = Join-Path $modRoot 'goblins_ashborn_isles'
$baseMetadata = Join-Path $baseRoot '.metadata\metadata.json'
if (-not (Test-Path -LiteralPath $baseMetadata)) { throw 'Install Goblins 0.5.4 before preparing this add-on.' }
$base = Get-Content -LiteralPath $baseMetadata -Raw | ConvertFrom-Json
if ($base.id -ne 'alex.goblins_ashborn_isles' -or $base.version -ne '0.5.4') {
    throw 'This prototype add-on requires the installed Goblins of the Ashborn Isles 0.5.4. Do not enable it with a full 0.5.5 build.'
}
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'data\prototype_055_files.json') -Raw | ConvertFrom-Json
$definitions = [IO.File]::ReadAllText((Join-Path $baseRoot 'in_game\map_data\definitions.txt'))
foreach ($location in $manifest.homeland_locations) {
    if ($definitions -notmatch ('\b' + [regex]::Escape($location) + '\b')) { throw "Missing 0.5.4 homeland district: $location" }
}
if (-not $OutputPath) { $OutputPath = Join-Path $PSScriptRoot "build\$slug" }
$prepared = [IO.Path]::GetFullPath($OutputPath)
$source = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'mod'))
if ($prepared -eq $baseRoot -or $prepared -eq $modRoot -or $prepared -eq $userRoot -or $prepared -eq $source) { throw 'Invalid output directory.' }
if ((Test-Path -LiteralPath $prepared) -and @(Get-ChildItem -LiteralPath $prepared -Force).Count -gt 0) {
    $existingMetadata = Join-Path $prepared '.metadata\metadata.json'
    if (-not (Test-Path -LiteralPath $existingMetadata)) { throw 'Output directory contains unrelated files.' }
    $existing = Get-Content -LiteralPath $existingMetadata -Raw | ConvertFrom-Json
    if ($existing.id -ne $id) { throw 'Output directory contains another mod.' }
}
New-Item -ItemType Directory -Path $prepared -Force | Out-Null
if ((Get-Item -LiteralPath $prepared).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Output directory must not be a link.' }
foreach ($entry in $manifest.files) {
    if ($entry.path -notmatch '^[A-Za-z0-9_./-]+$' -or $entry.path.Split('/') -contains '..' -or $entry.path.StartsWith('/')) { throw 'Unsafe manifest path.' }
    $origin = Join-Path $source $entry.path
    if ((Get-FileHash -LiteralPath $origin -Algorithm SHA256).Hash -ne $entry.sha256) { throw "Prototype source checksum mismatch: $($entry.path)" }
    $destination = [IO.Path]::GetFullPath((Join-Path $prepared $entry.path))
    if (-not $destination.StartsWith($prepared.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe output file.' }
    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $origin -Destination $destination -Force
}
# Build the population override from the installed base, preserving all existing
# native and goblin entries. Only add rows inside the known homeland blocks.
$popRelative = 'main_menu\setup\start\06_pops.txt'
$popBytes = [IO.File]::ReadAllBytes((Join-Path $baseRoot $popRelative))
$hasBom = $popBytes.Length -ge 3 -and $popBytes[0] -eq 239 -and $popBytes[1] -eq 187 -and $popBytes[2] -eq 191
$pops = [Text.Encoding]::UTF8.GetString($popBytes).TrimStart([char]0xFEFF)
foreach ($addition in $manifest.population_additions.PSObject.Properties) {
    $matches = [regex]::Matches($pops, ('(?m)^\s*' + [regex]::Escape($addition.Name) + '\s*=\s*\{'))
    if ($matches.Count -ne 1) { throw "Expected one base population block: $($addition.Name)" }
    $cursor = $matches[0].Index + $matches[0].Length
    $depth = 1
    while ($depth -gt 0 -and $cursor -lt $pops.Length) {
        if ($pops[$cursor] -eq '{') { $depth++ }
        if ($pops[$cursor] -eq '}') { $depth-- }
        $cursor++
    }
    if ($depth -ne 0) { throw 'Unclosed base population block.' }
    $pops = $pops.Insert($cursor - 1, ($addition.Value.Replace("`n", "`r`n") + "`r`n"))
}
$popOutput = Join-Path $prepared $popRelative
New-Item -ItemType Directory -Path (Split-Path $popOutput -Parent) -Force | Out-Null
[IO.File]::WriteAllText($popOutput, $pops, [Text.UTF8Encoding]::new($hasBom))
$populationHash = (Get-FileHash -LiteralPath $popOutput -Algorithm SHA256).Hash
# Derive two overrides from the installed base; never distribute its native setup.
# Patch the four authored identities, preserving every other entry.
$derivedHashes = @{}
$charRel = 'main_menu/setup/start/05_characters.txt'
$chars = [IO.File]::ReadAllText((Join-Path $baseRoot $charRel))
$locRel = 'main_menu/localization/english/goblins_ashborn_isles_l_english.yml'
$loc = [IO.File]::ReadAllText((Join-Path $baseRoot $locRel))
$expected = @{
    CDM = @{path='data/cindermaw.json'; name='drogg'; culture='cm_cinderkin'; nickname='cm_stone_fletcher'}
    QBR = @{path='data/brackmaw.json'; name='murgash'; culture='cm_brinekin'}
    RHK = @{path='data/reefhook.json'; name='skrezz'; culture='cm_reefkin'}
    SWK = @{path='data/sootwake.json'; name='snikh'; culture='cm_sootkin'}
}
if (@($manifest.identities).Count -ne $expected.Count -or @($manifest.identities.tag | Sort-Object -Unique).Count -ne $expected.Count) { throw 'Expected four unique clan identities.' }
foreach ($entry in $manifest.identities) {
    $identity = $expected[$entry.tag]
    if (-not $identity -or $entry.path -ne $identity.path) { throw 'Unexpected clan identity source.' }
    $identityPath = Join-Path $PSScriptRoot $entry.path
    if ((Get-FileHash -LiteralPath $identityPath -Algorithm SHA256).Hash -ne $entry.sha256) { throw 'Clan identity source checksum mismatch.' }
    $profile = Get-Content -LiteralPath $identityPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $rulerPattern = '(?m)^cm_' + $entry.tag.ToLowerInvariant() + '_ruler = \{[^\r\n]*\}'
    $matchesFound = [regex]::Matches($chars, $rulerPattern)
    if ($matchesFound.Count -ne 1) { throw "Expected exactly one authored ruler for $($entry.tag)." }
    $ruler = $matchesFound[0].Value
    $namePattern = 'first_name = \{ name = cm_ash_name_' + $identity.name + ' \}'
    if ($ruler -notmatch $namePattern) { throw 'Unexpected ruler setup; use the matching 0.5.4 base.' }
    $nicknames = [regex]::Matches($ruler, '\bnickname\s*=\s*\{\s*name\s*=\s*(\w+)\s*\}')
    if ($identity.nickname) {
        if ($nicknames.Count -ne 1 -or $nicknames[0].Groups[1].Value -ne $identity.nickname -or $profile.nickname_key -ne $identity.nickname) { throw 'Unexpected existing ruler nickname.' }
    } elseif ($ruler -match '\bnickname\s*=') { throw 'Unexpected ruler nickname in the base.' }
    foreach ($stat in @('adm', 'dip', 'mil')) {
        $pattern = '\b' + $stat + ' = \d+'
        if ([regex]::Matches($ruler, $pattern).Count -ne 1) { throw "Missing ruler stat: $stat" }
        $ruler = [regex]::Replace($ruler, $pattern, ($stat + ' = ' + $profile.$stat))
    }
    if (-not $identity.nickname) { $ruler = $ruler.Substring(0, $ruler.Length - 1) + 'nickname = { name = ' + $profile.nickname_key + ' } }' }
    $chars = $chars.Remove($matchesFound[0].Index, $matchesFound[0].Length).Insert($matchesFound[0].Index, $ruler)
    $culturePattern = '(?m)^ ' + $identity.culture + '_desc:.*$'
    if ([regex]::Matches($loc, $culturePattern).Count -ne 1) { throw 'Unexpected clan localization in the base.' }
    $cultureLine = ' ' + $identity.culture + '_desc: "' + $profile.culture_description.Replace('"', '\"') + '"'
    $loc = [regex]::Replace($loc, $culturePattern, $cultureLine)
    $nicknamePattern = '(?m)^ ' + [regex]::Escape($profile.nickname_key) + ':\s*"([^"\r\n]*)"'
    $nicknameLabels = [regex]::Matches($loc, $nicknamePattern)
    if ($identity.nickname) {
        if ($nicknameLabels.Count -ne 1 -or $nicknameLabels[0].Groups[1].Value -ne $profile.nickname) { throw 'Unexpected existing nickname localization.' }
    } else {
        if ($nicknameLabels.Count -ne 0) { throw 'Duplicate nickname localization.' }
        $loc = $loc.TrimEnd() + "`r`n " + $profile.nickname_key + ': "' + $profile.nickname + '"' + "`r`n"
    }
}
foreach ($derived in @(@{path=$charRel; text=$chars; bom=$false}, @{path=$locRel; text=$loc; bom=$true})) {
    $destination = Join-Path $prepared $derived.path
    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    [IO.File]::WriteAllText($destination, $derived.text, [Text.UTF8Encoding]::new($derived.bom))
    $derivedHashes[$derived.path] = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
}
$metadata = @{
    name = 'Goblins 0.5.5 - Gathering Prototype (requires 0.5.4)'
    id = $id
    version = '0.5.5'
    game_id = 'eu5'
    supported_game_version = '1.3.11'
    short_description = 'Test add-on: enable WITH Goblins 0.5.4. Two situations, clan diplomacy and eastern conquest incentives. New campaign recommended.'
    tags = @('Alternative history', 'Gameplay')
    relationships = @()
    game_custom_data = @{}
}
$metaDir = Join-Path $prepared '.metadata'
New-Item -ItemType Directory -Path $metaDir -Force | Out-Null
[IO.File]::WriteAllText((Join-Path $metaDir 'metadata.json'), ($metadata | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
$thumbnail = Join-Path $baseRoot '.metadata\thumbnail.png'
if (Test-Path -LiteralPath $thumbnail) { Copy-Item -LiteralPath $thumbnail -Destination (Join-Path $metaDir 'thumbnail.png') -Force }
if ($PrepareOnly) { Write-Host "Prepared $slug at $prepared"; return }
if (Get-Process -Name eu5 -ErrorAction SilentlyContinue) { throw 'Close Europa Universalis V before installing the prototype.' }
$target = [IO.Path]::GetFullPath((Join-Path $modRoot $slug))
if ([IO.Path]::GetDirectoryName($target) -ne $modRoot) { throw 'Invalid prototype install path.' }
foreach ($path in @($userRoot, $modRoot, $target)) {
    if ((Test-Path -LiteralPath $path) -and ((Get-Item -LiteralPath $path).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Install path is a link: $path" }
}
if (Test-Path -LiteralPath $target) {
    $oldMeta = Get-Content -LiteralPath (Join-Path $target '.metadata\metadata.json') -Raw | ConvertFrom-Json
    if ($oldMeta.id -ne $id) { throw 'Another mod occupies the prototype destination.' }
    $backupRoot = [IO.Path]::GetFullPath((Join-Path $userRoot 'goblins_prototype_backups'))
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    if ((Get-Item -LiteralPath $backupRoot).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Backup directory is a link.' }
    $backup = [IO.Path]::GetFullPath((Join-Path $backupRoot ($slug + '_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))))
    if ([IO.Path]::GetDirectoryName($backup) -ne $backupRoot) { throw 'Invalid backup target.' }
    Move-Item -LiteralPath $target -Destination $backup
}
Copy-Item -LiteralPath $prepared -Destination $target -Recurse
foreach ($entry in $manifest.files) {
    if ((Get-FileHash -LiteralPath (Join-Path $target $entry.path) -Algorithm SHA256).Hash -ne $entry.sha256) { throw 'Installed prototype checksum mismatch.' }
}
if ((Get-FileHash -LiteralPath (Join-Path $target $popRelative) -Algorithm SHA256).Hash -ne $populationHash) { throw 'Installed population checksum mismatch.' }
foreach ($relative in $derivedHashes.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $target $relative) -Algorithm SHA256).Hash -ne $derivedHashes[$relative]) { throw 'Installed clan override checksum mismatch.' }
}
Write-Host "Installed separate prototype at $target"
Write-Host 'Enable BOTH Goblins 0.5.4 and this prototype. Start a NEW 1337 campaign for testing.'
Write-Host 'The base mod and playsets were not modified. Disable the prototype to return to the base mod.'
