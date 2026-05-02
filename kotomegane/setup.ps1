Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$envFile = Join-Path $PSScriptRoot ".env"
$exampleEnvFile = Join-Path $PSScriptRoot ".env.example"

if (-not (Test-Path -LiteralPath $venvPython)) {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        throw "Python launcher 'py' was not found. Install Python 3.11 and rerun .\setup.ps1."
    }
    py -3.11 -m venv (Join-Path $PSScriptRoot ".venv")
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment creation failed. Confirm that Python 3.11 is installed."
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")

if (-not (Test-Path -LiteralPath $envFile)) {
    Copy-Item -LiteralPath $exampleEnvFile -Destination $envFile
}

$envFileValues = @{
    OPENAI_API_KEY = ""
    GEMINI_API_KEY = ""
    ANTHROPIC_API_KEY = ""
}
if (Test-Path -LiteralPath $envFile) {
    foreach ($line in Get-Content -LiteralPath $envFile) {
        foreach ($envVar in $envFileValues.Keys) {
            if ($line -match ("^\s*" + [regex]::Escape($envVar) + "\s*=\s*(.+?)\s*$")) {
                $envFileValues[$envVar] = $Matches[1].Trim()
            }
        }
    }
}

$shellValues = @{
    OPENAI_API_KEY = $env:OPENAI_API_KEY
    GEMINI_API_KEY = $env:GEMINI_API_KEY
    ANTHROPIC_API_KEY = $env:ANTHROPIC_API_KEY
}
$availableKeys = @(
    $envFileValues.Keys | Where-Object { -not [string]::IsNullOrWhiteSpace($envFileValues[$_]) }
)
if ($availableKeys.Count -eq 0) {
    $availableKeys = @(
        $shellValues.Keys | Where-Object { -not [string]::IsNullOrWhiteSpace($shellValues[$_]) }
    )
}

Write-Host "Setup complete."
if ($availableKeys.Count -gt 0) {
    Write-Host ("Available provider keys: " + ($availableKeys -join ", "))
} else {
    Write-Host "Set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY in .env or in your environment before running."
}
Write-Host "run.ps1 will validate which source is used at startup."
