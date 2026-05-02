<#
.SYNOPSIS
    TECHIE SaaS - Local dev full build and start script

.DESCRIPTION
    Run from the project root (d:\azure).
    1. Check .env file exists
    2. Start PostgreSQL first (wait for healthcheck)
    3. Build and start all services in detached mode
    4. Verify health

.EXAMPLE
    cd d:\azure
    .\start-local.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -- 0. Verify working directory --
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($PWD.Path -ne $root) {
    Write-Host '[*] Changing to project root: ' $root -ForegroundColor Cyan
    Set-Location $root
}

if (-not (Test-Path 'docker-compose.yml')) {
    Write-Error 'docker-compose.yml not found. Run this script from the project root.'
    exit 1
}

# -- 1. Ensure .env exists --
if (-not (Test-Path '.env')) {
    Write-Host '[!] .env not found - copying from .env.example' -ForegroundColor Yellow
    Copy-Item '.env.example' '.env'
    Write-Host '    Edit .env to set OPENAI_API_KEY if needed.' -ForegroundColor Yellow
}

# -- 2. Stop old containers --
Write-Host "`n[1/4] Stopping any existing containers..." -ForegroundColor Cyan
docker compose down --remove-orphans

# -- 3. Start PostgreSQL first --
Write-Host "`n[2/4] Starting PostgreSQL and waiting for healthcheck..." -ForegroundColor Cyan
docker compose up -d postgres
Write-Host '       Waiting for PostgreSQL to be ready...'

$maxRetries = 30
$retry = 0
do {
    Start-Sleep -Seconds 2
    $retry++
    $result = docker compose exec postgres pg_isready -U techie 2>&1
} while ($LASTEXITCODE -ne 0 -and $retry -lt $maxRetries)

if ($LASTEXITCODE -ne 0) {
    Write-Error "PostgreSQL failed to start after $maxRetries retries."
    exit 1
}
Write-Host '       PostgreSQL is ready.' -ForegroundColor Green

# -- 4. Build and start all services --
Write-Host "`n[3/4] Building and starting all services (detached)..." -ForegroundColor Cyan
docker compose up --build --force-recreate -d

# -- 5. Verify --
Write-Host "`n[4/4] Verifying services..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
docker compose ps

Write-Host "`n========================================" -ForegroundColor Green
Write-Host ' All services started!' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
Write-Host ' TECHIE HUB   : http://localhost:8090'
Write-Host ' kotomake      : http://localhost:8080'
Write-Host ' kotomigaki    : http://localhost:8081'
Write-Host ' kotomusubi    : http://localhost:8082'
Write-Host ' PostgreSQL    : localhost:5432'
Write-Host ''
Write-Host ' Useful commands:' -ForegroundColor Yellow
Write-Host '   docker compose logs -f kotomigaki   # aio2-main logs'
Write-Host '   docker compose logs -f hub          # TECHIE HUB logs'
Write-Host '   docker compose logs -f              # all logs'
Write-Host '   docker compose down                 # stop everything'
Write-Host ''
