param(
    [string]$PythonLauncher = "py",
    [string]$PythonVersion = "-3.11",
    [string]$VenvPath = ".venv",
    [switch]$Recreate,
    [switch]$NoDev,
    [switch]$SkipAudit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $repoRoot

$venvFullPath = Join-Path $repoRoot $VenvPath
$requirementsFile = if ($NoDev) { "requirements.txt" } else { "requirements-dev.txt" }
$constraintsFile = "constraints.lock.txt"

if (-not (Test-Path $constraintsFile)) {
    throw "Missing $constraintsFile"
}
if (-not (Test-Path $requirementsFile)) {
    throw "Missing $requirementsFile"
}

if ($Recreate -and (Test-Path $venvFullPath)) {
    $resolvedVenv = Resolve-Path $venvFullPath
    if (-not ($resolvedVenv.Path.StartsWith($repoRoot.Path)) -or (Split-Path -Leaf $resolvedVenv.Path) -ne ".venv") {
        throw "Refusing to remove unexpected venv path: $($resolvedVenv.Path)"
    }
    Remove-Item -LiteralPath $resolvedVenv.Path -Recurse -Force
}

if (-not (Test-Path $venvFullPath)) {
    & $PythonLauncher $PythonVersion -m venv $venvFullPath
    if ($LASTEXITCODE -ne 0) {
        throw "venv creation failed"
    }
}

$venvPython = Join-Path $venvFullPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Missing venv python: $venvPython"
}

& $venvPython -m pip install --upgrade "pip==26.1.2"
if ($LASTEXITCODE -ne 0) {
    throw "pip bootstrap failed"
}

& $venvPython -m pip install -r $requirementsFile -c $constraintsFile
if ($LASTEXITCODE -ne 0) {
    throw "dependency install failed"
}

& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) {
    throw "pip check failed"
}

if (-not $SkipAudit -and -not $NoDev) {
    & $venvPython -m pip_audit
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "pip-audit reported findings. As of 2026-06-07, diskcache==5.6.3 / CVE-2025-69872 has no fixed version and is tracked as residual risk."
    }
}

Write-Host "Rebuild complete: $venvFullPath"
Write-Host "Recommended verification:"
Write-Host "  $venvPython -m pytest tests -q"
Write-Host "  `$env:HEADLESS='1'; `$env:PORT='8092'; $venvPython nicegui_app.py"
