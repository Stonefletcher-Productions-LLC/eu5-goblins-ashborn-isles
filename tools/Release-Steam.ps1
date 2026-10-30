# Goblins Steam Workshop release for the version in data/island.json.
# 1. clean export of HEAD, installer PrepareOnly and isolated install, compared with the packaged zip
# 2. active install into the EU5 profile (previous copy backed up by the installer)
# 3. Workshop description + change notes, upload to item 3814944518
# Requires a committed, repackaged version (verify_prepared_bundle.py passes), EU5 closed,
# Steam running and signed in as the Workshop owner, and build/release-<ver>/<ver>.bbcode change notes.
# Resumable: a step whose receipt exists is skipped.
param([switch]$NoPause)
$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$Game = 'E:\SteamLibrary\steamapps\common\Europa Universalis V\game'
$User = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Paradox Interactive\Europa Universalis V'
$Uploader = 'C:\Users\alexa\.local\share\pdx-workshop-manager'
$WorkshopId = '3814944518'
$Version = (Get-Content -LiteralPath (Join-Path $Repo 'data\island.json') -Raw | ConvertFrom-Json).version
$Tag = $Version.Replace('.', '')
$Gate = "E:\CodexScratch\goblins-$Tag-gate"
$LogDir = Join-Path $Repo "build\release-$Tag"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Status = Join-Path $LogDir 'steam-status.txt'
Set-Content -LiteralPath $Status -Value 'RUNNING'
Start-Transcript -LiteralPath (Join-Path $LogDir 'steam-release.log') -Force | Out-Null
function Step($name) { Write-Host "`n=== $name ===" }
function RunGit { & git.exe -c "safe.directory=$($Repo.Replace('\','/'))" -C $Repo @args; if ($LASTEXITCODE) { throw "git $args failed ($LASTEXITCODE)" } }
$CodexPy = 'C:\Users\alexa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $CodexPy) { $PyExe = $CodexPy; $PyPre = @() } elseif (Get-Command py.exe -ErrorAction SilentlyContinue) { $PyExe = 'py.exe'; $PyPre = @('-3') } else { $PyExe = 'python.exe'; $PyPre = @() }
function RunPy { $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'; try { & $PyExe @PyPre @args 2>&1 | ForEach-Object { Write-Host "$_" }; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $eap }; if ($code) { throw "python $args failed ($code)" } }
try {
    Set-Location -LiteralPath $Repo
    Step "Preconditions for $Version"
    if (@(RunGit status --porcelain=v1 --untracked-files=no).Count) { throw 'Worktree has uncommitted changes; commit the release first.' }
    $commit = RunGit rev-parse HEAD
    Write-Host "Release commit $commit"
    $notes = Join-Path $LogDir "$Version.bbcode"
    if (-not (Test-Path -LiteralPath $notes)) { throw "Missing Workshop change notes: $notes" }
    if (Get-Process -Name eu5 -ErrorAction SilentlyContinue) { throw 'Close Europa Universalis V first.' }
    if (-not (Get-Process -Name steam -ErrorAction SilentlyContinue)) { throw 'Start Steam (signed in as the Workshop owner) first.' }
    # The Workshop title comes from the uploader config; keep it identical to the mod name (e.g. "[1.4] - ...").
    $modName = (Get-Content -LiteralPath (Join-Path $Repo 'mod\.metadata\metadata.json') -Raw | ConvertFrom-Json).name
    $steamName = (Get-Content -LiteralPath (Join-Path $Uploader 'goblins-config.json') -Raw | ConvertFrom-Json).mods[0].names.english
    if ($steamName -ne $modName) { throw "Workshop title '$steamName' differs from mod name '$modName'; update $Uploader\goblins-config.json." }
    if (-not ([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes((Join-Path $Repo 'STEAM_DESCRIPTION.txt')))).StartsWith("[h1]$modName[/h1]")) { throw "STEAM_DESCRIPTION.txt heading differs from mod name '$modName'." }
    RunPy tools/verify_prepared_bundle.py
    if (-not (Test-Path -LiteralPath (Join-Path $Repo "dist\Goblins_Ashborn_Isles_$Version.zip"))) { throw "dist zip missing; run tools/refresh_overlay_bundle.py first." }

    $receipt = Join-Path $LogDir 'isolated-install.json'
    if (Test-Path -LiteralPath $receipt) { Write-Host 'Isolated install already verified; skipping gate.' } else {
        Step 'Clean export of the committed tree'
        if ((Test-Path -LiteralPath $Gate) -and @(Get-ChildItem -LiteralPath $Gate -Force).Count) { throw "Gate folder not empty: $Gate" }
        New-Item -ItemType Directory -Force -Path "$Gate\src","$Gate\user" | Out-Null
        RunGit archive --format=zip -o "$Gate\source.zip" HEAD
        Expand-Archive -LiteralPath "$Gate\source.zip" -DestinationPath "$Gate\src"
        Remove-Item -LiteralPath "$Gate\source.zip"
        Step 'Installer: prepare only'
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$Gate\src\Install-Goblins.ps1" -PrepareOnly -GamePath $Game
        if ($LASTEXITCODE) { throw 'PrepareOnly failed' }
        Step 'Installer: isolated install'
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$Gate\src\Install-Goblins.ps1" -GamePath $Game -UserDataPath "$Gate\user"
        if ($LASTEXITCODE) { throw 'Isolated install failed' }
        Step 'Compare isolated install with the packaged archive'
        RunPy tools/compare_install.py $Repo $Gate $receipt
    }

    $upload = Join-Path $LogDir 'steam-upload.log'
    if ((Test-Path -LiteralPath $upload) -and ((Get-Content -LiteralPath $upload -Raw) -match 'Upload successful')) {
        Write-Host "Steam upload of $Version already succeeded."
    } else {
        Step "Install $Version into the active EU5 profile"
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$Gate\src\Install-Goblins.ps1" -GamePath $Game
        if ($LASTEXITCODE) { throw 'Active install failed' }
        RunPy -c "import sys,hashlib; from pathlib import Path; a=Path(sys.argv[1]); b=Path(sys.argv[2]); f=lambda r:{p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}; x=f(a); y=f(b); d=sorted(k for k in x.keys()|y.keys() if x.get(k)!=y.get(k)); print(len(y),'files; differences:',d[:20]); sys.exit(1 if d else 0)" "$Gate\user\mod\goblins_ashborn_isles" "$User\mod\goblins_ashborn_isles"

        Step 'Workshop description and change notes'
        $desc = [IO.File]::ReadAllBytes((Join-Path $Repo 'STEAM_DESCRIPTION.txt'))
        if ($desc.Length -ge 8000 -or ([Text.Encoding]::UTF8.GetString($desc)).Contains("`r")) { throw "Description must be LF and under 8000 bytes (is $($desc.Length))." }
        Copy-Item -LiteralPath (Join-Path $Uploader 'description.bbcode') -Destination (Join-Path $LogDir 'description-previous.bbcode') -Force
        [IO.File]::WriteAllBytes((Join-Path $Uploader 'description.bbcode'), $desc)
        Copy-Item -LiteralPath $notes -Destination (Join-Path $Uploader "change-notes\$Version.bbcode") -Force
        Write-Host "Description $($desc.Length) bytes"

        Step "Upload to Steam Workshop item $WorkshopId"
        Push-Location -LiteralPath $Uploader
        $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'  # uploader logs to stderr
        try { $out = & .\pdx-workshop-manager.exe -config .\goblins-config.json -mod $WorkshopId 2>&1 | Out-String } finally { $ErrorActionPreference = $prev; Pop-Location }
        Write-Host $out
        $out | Set-Content -LiteralPath $upload
        if ($out -notmatch 'Upload successful') { throw 'Uploader did not report "Upload successful".' }
    }
    Set-Content -LiteralPath $Status -Value "PASSED $commit"
    Write-Host "`nSTEAM RELEASE PASSED. $Version installed and uploaded to Workshop item $WorkshopId."
} catch {
    Set-Content -LiteralPath $Status -Value "FAILED: $($_.Exception.Message)"
    Write-Host "`nSTEAM RELEASE FAILED: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Stop-Transcript | Out-Null
}
if (-not $NoPause) { Read-Host 'Press Enter to close' }
