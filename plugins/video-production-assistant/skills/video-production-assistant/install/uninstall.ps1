<#
.SYNOPSIS
  Removes the tools that install.ps1 installed, and nothing else.

.DESCRIPTION
  It reads %LOCALAPPDATA%\video-production-assistant\installed.txt, which install.ps1 writes.
  Tools you had before are never on that list, so they are never touched. At the end it lists
  the other things the video production assistant can leave on the computer, for you to remove
  by hand if you want.

.EXAMPLE
  .\uninstall.ps1 -DryRun
  .\uninstall.ps1
  .\uninstall.ps1 -Yes
#>
param(
  [switch]$DryRun,
  [switch]$Yes
)

$ErrorActionPreference = 'Stop'
$stateRoot = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME '.local/state' }
$manifest = Join-Path (Join-Path $stateRoot 'video-production-assistant') 'installed.txt'
$skill = Split-Path $PSScriptRoot -Parent
$interactive = -not [Console]::IsInputRedirected

function Say([string]$tag, [string]$text) { Write-Host ('{0,-15} {1}' -f $tag, $text) }

function Confirm-Step([string]$question) {
  if ($Yes) { return $true }
  if (-not $interactive) { return $false }
  return ((Read-Host "$question [y/N]") -match '^(y|yes)$')
}

function Remove-Record([string]$key) {
  $keep = @(Get-Content $manifest | Where-Object { $_ -notmatch "^$key`t" })
  Set-Content -Path $manifest -Value $keep -Encoding UTF8
}

$entries = @()
if (Test-Path $manifest) { $entries = @(Get-Content $manifest | Where-Object { $_ -and $_ -notmatch '^#' }) }
if ($entries.Count -eq 0) {
  Say '[nothing]' 'install.ps1 has not installed anything here, so there is nothing to remove.'
}
foreach ($line in $entries) {
  $key, $method, $id = $line -split "`t"
  if ($method -ne 'winget') { Say '[skip]' "$($key): unknown method '$method'"; continue }
  # The id goes into a command line, so accept only the characters real winget ids use.
  if ("$id" -notmatch '^[A-Za-z0-9._+-]+$') { Say '[skip]' "$($key): its line in $manifest looks damaged, so nothing was done for it."; continue }
  winget list --id $id -e --disable-interactivity --accept-source-agreements 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Say '[gone]' "$key is no longer installed."
    if (-not $DryRun) { Remove-Record $key }
    continue
  }
  $cmd = "winget uninstall --id $id -e"
  if ($DryRun) { Say '[would remove]' "$($key): $cmd"; continue }
  if (Confirm-Step "Remove $key ($cmd)?") {
    winget uninstall --id $id -e --disable-interactivity
    if ($LASTEXITCODE -eq 0) { Say '[removed]' $key; Remove-Record $key }
    else { Say '[warn]' "$key was not removed (winget exit code $LASTEXITCODE). It stays on the list." }
  } else { Say '[kept]' $key }
}

Write-Host ''
Write-Host 'Not removed automatically. Remove these yourself if you want no trace:'
Write-Host '  - In each video library: _tools\venv (local Whisper) and _tools\models (its speech'
Write-Host '    models), or the whole _tools folder. Your videos and notes are elsewhere in the library.'
$hf = Join-Path $HOME '.cache\huggingface\hub'
if (Get-ChildItem -Path $hf -Filter 'models--Systran--faster-whisper-*' -Directory -ErrorAction SilentlyContinue) {
  Write-Host "  - Whisper models downloaded by older versions of this skill: $hf\models--Systran--faster-whisper-*"
}
Write-Host '  - Connector entries added to an MCP config file:'
Write-Host ('    python "{0}" --remove all --target <that file>' -f (Join-Path $skill 'connectors\setup_connectors.py'))
Write-Host '    (a <file>.bak copy sits next to it; delete it once you are happy)'
if (Get-Command uv -ErrorAction SilentlyContinue) { Write-Host "  - uv's copy of the ElevenLabs connector:   uv cache clean elevenlabs-mcp" }
$npx = if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'npm-cache\_npx' } else { $null }
if ($npx -and (Test-Path $npx)) { Write-Host "  - npx's copies of HyperFrames and Desktop Commander: $npx (npx downloads again if needed)" }
Write-Host "  - This skill's own folder, once you no longer want the skill: $skill"
if ($DryRun) { Write-Host ''; Write-Host 'Dry run: nothing was removed or changed.' }
