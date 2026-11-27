<#
.SYNOPSIS
  Installs the free tools the video production assistant uses, on Windows, with winget.

.DESCRIPTION
  Essentials (always): FFmpeg, Python.
  Options (-With): node (HyperFrames graphics), uv (ElevenLabs connector),
                   blender (3D diagrams), ytdlp (licensed outside clips), git.
  Minimum versions are in scripts\min_versions.txt.

  Safety rules this script keeps:
  - scripts\doctor.py decides what is ready, too old or missing. A tool found by any method
    (PATH, nvm-windows, fnm, Volta, conda, scoop, the usual install folders or winget) is never
    installed again, upgraded or replaced.
  - Nothing is installed without a yes, typed at the prompt or given as -Yes.
  - Each tool it installs is listed in %LOCALAPPDATA%\video-production-assistant\installed.txt
    (outside the skill folder, so updating the skill keeps the list); uninstall.ps1 removes
    only those.
  - -DryRun only reads. Running the script twice changes nothing the second time.
  - Exits 1 if an essential tool is still not ready.

.EXAMPLE
  .\install.ps1 -DryRun
  .\install.ps1
  .\install.ps1 -With node,uv
  .\install.ps1 -All
  .\install.ps1 -Yes
#>
param(
  [string[]]$With = @(),
  [switch]$All,
  [switch]$DryRun,
  [switch]$Yes
)

$ErrorActionPreference = 'Stop'
$AllOpts = @('ffmpeg', 'python', 'node', 'uv', 'blender', 'ytdlp', 'git')
$scripts = Join-Path (Split-Path $PSScriptRoot -Parent) 'scripts'
$doctor = Join-Path $scripts 'doctor.py'
# The list of what this script installed lives in the user's own folder, not the skill folder:
# a skill update replaces the skill folder, and it may be read-only.
$stateRoot = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME '.local/state' }
$manifest = Join-Path (Join-Path $stateRoot 'video-production-assistant') 'installed.txt'

# Check every name before anything is looked at or installed.
$wanted = @('ffmpeg', 'python')
if ($All) { $wanted = $AllOpts }
else {
  foreach ($w in ($With -split ',' | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })) {
    if ($AllOpts -notcontains $w) { [Console]::Error.WriteLine("Unknown option '$w'. Choose from: $($AllOpts -join ', ')"); exit 2 }
    if ($wanted -notcontains $w) { $wanted += $w }
  }
}

$pyMin = [version]'3.9'
$minFile = Join-Path $scripts 'min_versions.txt'
if (Test-Path $minFile) {
  foreach ($line in Get-Content $minFile) { if ($line -match '^\s*PYTHON_MIN\s*=\s*([\d.]+)') { $pyMin = [version]$Matches[1] } }
}

$haveWinget = [bool](Get-Command winget -ErrorAction SilentlyContinue)
$interactive = -not [Console]::IsInputRedirected
$attention = New-Object System.Collections.Generic.List[string]
$script:essentialBad = $false

function Say([string]$tag, [string]$text) { Write-Host ('{0,-15} {1}' -f $tag, $text) }

function Confirm-Step([string]$question) {
  if ($Yes) { return $true }
  if (-not $interactive) { return $false }
  return ((Read-Host "$question [y/N]") -match '^(y|yes)$')
}

function Add-Record([string]$key, [string]$id) {
  try {
    New-Item -ItemType Directory -Force -Path (Split-Path $manifest -Parent) | Out-Null
    if (-not (Test-Path $manifest)) { Set-Content -Path $manifest -Value '# Tools install.ps1 installed. uninstall.ps1 removes only these.' -Encoding UTF8 }
    if (-not (Select-String -Path $manifest -Pattern "^$key`t" -Quiet)) { Add-Content -Path $manifest -Value "$key`twinget`t$id" -Encoding UTF8 }
  } catch {
    Say '[warn]' "Could not write $manifest, so uninstall.ps1 will not know about $key."
    Say '' 'To remove it later, do it by hand.'
  }
}

function Install-Tool([string]$key, [string]$id, [bool]$isEssential) {
  $cmd = "winget install --id $id -e --accept-source-agreements --accept-package-agreements"
  if ($DryRun) { Say '[would install]' "$($key): $cmd"; return }
  if (-not $haveWinget) {
    Say '[manual]' "$key - winget was not found. Install 'App Installer' from the Microsoft Store, or see references\tools-setup.md."
    if ($isEssential) { $script:essentialBad = $true }
    return
  }
  Say '[missing]' "$key can be installed with: $cmd"
  if (-not (Confirm-Step "Install $key now?")) {
    if (-not $Yes -and -not $interactive) { Say '[skipped]' "$($key): no one at the prompt to ask. Run this in a terminal, or add -Yes." }
    else { Say '[skipped]' "$key was not installed." }
    if ($isEssential) { $script:essentialBad = $true }
    return
  }
  winget install --id $id -e --accept-source-agreements --accept-package-agreements
  if ($LASTEXITCODE -eq 0) { Say '[installed]' $key; Add-Record $key $id }
  else {
    Say '[warn]' "$key did not install (winget exit code $LASTEXITCODE). Carrying on."
    if ($isEssential) { $script:essentialBad = $true }
  }
}

# Finds a Python new enough to run doctor.py. Never runs the Microsoft Store placeholder.
function Find-Python {
  $candidates = @()
  foreach ($name in @('python', 'python3', 'py')) {
    foreach ($c in @(Get-Command $name -CommandType Application -All -ErrorAction SilentlyContinue)) {
      $pre = @(); if ($name -eq 'py') { $pre = @('-3') }
      $candidates += , @($c.Source, $pre)
    }
  }
  $extra = @()
  if ($env:LOCALAPPDATA) {
    $extra = @(Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python3*\python.exe') -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | ForEach-Object { $_.FullName })
  }
  foreach ($conda in @('miniconda3', 'anaconda3', 'miniforge3')) { $extra += Join-Path $HOME "$conda\python.exe" }
  foreach ($p in $extra) { if (Test-Path $p) { $candidates += , @($p, @()) } }
  $old = $null
  foreach ($cand in $candidates) {
    $exe = $cand[0]; $pre = $cand[1]
    if ($exe -like '*\WindowsApps\python*') { continue }
    try { $v = (& $exe @pre -c "import sys; print('%d.%d.%d' % sys.version_info[:3])" 2>$null | Select-Object -First 1) } catch { continue }
    if ("$v" -notmatch '^\d+\.\d+\.\d+') { continue }
    if ([version]"$v" -ge $pyMin) { return @{ Exe = $exe; Pre = $pre; Old = $null } }
    if (-not $old) { $old = "$exe is Python $v" }
  }
  return @{ Exe = $null; Pre = @(); Old = $old }
}

# 1. Python runs doctor.py, so find (or install) it first.
$py = Find-Python
if (-not $py.Exe) {
  if ($py.Old) {
    Say '[too old]' "$($py.Old); the scripts need $pyMin or newer"
    Say '' 'Upgrade Python the way you installed it. A second Python was not installed, to avoid clashes. Then run this script again.'
    exit 1
  }
  Install-Tool 'python' 'Python.Python.3.12' $true
  if ($DryRun) { Write-Host ''; Write-Host 'The other tools are checked once Python is installed.'; Write-Host 'Dry run: nothing was installed or changed.'; exit 0 }
  # winget does not update PATH in this window, so look in the install folders too.
  $py = Find-Python
  if (-not $py.Exe) { Write-Host 'Python is not available in this window. Open a NEW terminal and run this script again.'; exit 1 }
}

# 2. Ask doctor.py about every tool wanted, then act on its answers.
$plan = & $py.Exe @($py.Pre) $doctor --plan @wanted
if ($LASTEXITCODE -ne 0) { Write-Error 'doctor.py could not check the tools.'; exit 1 }

foreach ($line in $plan) {
  $f = "$line" -split "`t"
  if ($f.Count -lt 6) { continue }
  $key, $state, $isEssential, $install, $detail, $advice = $f
  $isEssential = ($isEssential -eq '1')
  switch ($state) {
    'ok' {
      Say '[ok]' $detail
      if ($advice -ne '-') { $attention.Add("$($key): $advice") }
    }
    'missing' {
      $method, $rest = $install -split ' ', 2
      if ($method -eq 'winget') { Install-Tool $key $rest $isEssential }
      else {
        if ($method -ne 'manual') { $rest = "this is not Windows; use install/install.sh here ($method $rest)." }
        Say '[manual]' "$($key): $rest"
        if ($isEssential) { $script:essentialBad = $true }
      }
    }
    default {
      $label = @{ too_old = '[too old]'; incomplete = '[incomplete]'; not_on_path = '[not on PATH]' }[$state]
      Say $label $detail
      Say '' $advice
      $attention.Add("$($key): $detail. Nothing was changed; see the advice above.")
      if ($isEssential) { $script:essentialBad = $true }
    }
  }
}

Write-Host ''
if ($attention.Count -gt 0) {
  Write-Host 'Needs your attention (nothing was changed for these):'
  foreach ($a in $attention) { Write-Host "  - $a" }
  Write-Host ''
}
if ($DryRun) { Write-Host 'Dry run: nothing was installed or changed.' }
else { Write-Host 'Open a NEW terminal so newly installed tools are found.' }
Write-Host ('Check any time with:   python "{0}"' -f $doctor)
Write-Host ('Remove what this installed:   "{0}"' -f (Join-Path $PSScriptRoot 'uninstall.ps1'))
Write-Host 'Local Whisper is optional and is set up per video library (it asks first):'
Write-Host ('  python "{0}" "C:\path\to\Video Library" --venv' -f (Join-Path $scripts 'init_library.py'))
if (-not $DryRun -and $script:essentialBad) { exit 1 }
