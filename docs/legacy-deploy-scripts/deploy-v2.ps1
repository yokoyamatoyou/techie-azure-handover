<#
.SYNOPSIS
    TECHIE SaaS - v2 Hotfix Deployment
    Fixes: kotomigaki localhost binding, techie-hub FQDNs, kotomake OPENAI_API_KEY

.NOTES
    Run from D:\azure with proxy env vars already set.
    Requires: az CLI logged in, Docker running.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ================================================================
# VARIABLES
# ================================================================
$RG        = 'TECHIE'
$ACR_NAME  = 'techiereg2026'
$ACR_LOGIN = "$ACR_NAME.azurecr.io"
$TAG       = 'v2'

# PostgreSQL connection (must match Phase 2 deploy)
$PG_SERVER   = 'techie-pg-server'
$PG_DB       = 'techie'
$PG_ADMIN    = 'techieadmin'
$PG_PASSWORD = 'Techie#2026!Deploy'
$PG_HOST     = "$PG_SERVER.postgres.database.azure.com"
$DATABASE_URL = "postgresql://${PG_ADMIN}:${PG_PASSWORD}@${PG_HOST}:5432/${PG_DB}?sslmode=require"

# OPENAI_API_KEY - set this before running!
if (-not $env:OPENAI_API_KEY) {
    Write-Host '[!] OPENAI_API_KEY not set. Set it with:' -ForegroundColor Red
    Write-Host '    $env:OPENAI_API_KEY = "sk-..."' -ForegroundColor Yellow
    Read-Host 'Press ENTER to continue without it, or Ctrl+C to abort'
}
$OPENAI_KEY = $env:OPENAI_API_KEY

Write-Host '============================================' -ForegroundColor Cyan
Write-Host " TECHIE v2 Hotfix Deployment"                 -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan

# ================================================================
# STEP 1: Log into ACR
# ================================================================
Write-Host "`n[1/7] Logging into ACR..." -ForegroundColor Cyan
az acr login --name $ACR_NAME

# ================================================================
# STEP 2: Rebuild kotomigaki with v2 tag
# ================================================================
Write-Host "`n[2/7] Building kotomigaki:$TAG ..." -ForegroundColor Cyan
docker build -t "${ACR_LOGIN}/kotomigaki:${TAG}" -f aio2-main/Dockerfile .
Write-Host '       Build complete.' -ForegroundColor Green

# ================================================================
# STEP 3: Rebuild techie-hub with v2 tag (updated config.js + FQDNs)
# ================================================================
Write-Host "`n[3/7] Building techie-hub:$TAG ..." -ForegroundColor Cyan
docker build -t "${ACR_LOGIN}/techie-hub:${TAG}" -f techie-hub/Dockerfile techie-hub/
Write-Host '       Build complete.' -ForegroundColor Green

# ================================================================
# STEP 4: Push both images to ACR
# ================================================================
Write-Host "`n[4/7] Pushing images to ACR..." -ForegroundColor Cyan
docker push "${ACR_LOGIN}/kotomigaki:${TAG}"
docker push "${ACR_LOGIN}/techie-hub:${TAG}"
Write-Host '       Push complete.' -ForegroundColor Green

# ================================================================
# STEP 5: Update kotomake (no rebuild - just inject OPENAI_API_KEY)
# ================================================================
Write-Host "`n[5/7] Updating kotomake env vars (no rebuild)..." -ForegroundColor Cyan
az containerapp update `
    --resource-group $RG `
    --name kotomake `
    --set-env-vars `
        PORT=8080 `
        HEADLESS=1 `
        CONTAINER_ENV=1 `
        OPENAI_API_KEY="$OPENAI_KEY" `
    --output table

Write-Host '       kotomake updated.' -ForegroundColor Green

# ================================================================
# STEP 6: Update kotomigaki to v2 image + env vars
# ================================================================
Write-Host "`n[6/7] Updating kotomigaki to $TAG image..." -ForegroundColor Cyan
az containerapp update `
    --resource-group $RG `
    --name kotomigaki `
    --image "${ACR_LOGIN}/kotomigaki:${TAG}" `
    --set-env-vars `
        PORT=8081 `
        HOST=0.0.0.0 `
        HEADLESS=1 `
        CONTAINER_ENV=1 `
        DATABASE_URL="$DATABASE_URL" `
        PLAYWRIGHT_BROWSERS_PATH=/ms-playwright `
    --output table

Write-Host '       kotomigaki updated.' -ForegroundColor Green

# ================================================================
# STEP 7: Update techie-hub to v2 image
# ================================================================
Write-Host "`n[7/7] Updating techie-hub to $TAG image..." -ForegroundColor Cyan
az containerapp update `
    --resource-group $RG `
    --name techie-hub `
    --image "${ACR_LOGIN}/techie-hub:${TAG}" `
    --output table

Write-Host '       techie-hub updated.' -ForegroundColor Green

# ================================================================
# VERIFY
# ================================================================
Write-Host "`n===== VERIFICATION =====" -ForegroundColor Yellow
$services = @('techie-hub', 'kotomigaki', 'kotomake', 'kotomusubi')
foreach ($svc in $services) {
    $fqdn = az containerapp show `
        --resource-group $RG `
        --name $svc `
        --query 'properties.configuration.ingress.fqdn' -o tsv
    $running = az containerapp show `
        --resource-group $RG `
        --name $svc `
        --query 'properties.runningStatus' -o tsv
    Write-Host "  $svc : https://$fqdn [$running]" -ForegroundColor White
}

Write-Host "`n============================================" -ForegroundColor Green
Write-Host ' v2 DEPLOYMENT COMPLETE!'                       -ForegroundColor Green
Write-Host ' Changes applied:'                              -ForegroundColor Green
Write-Host '   - kotomigaki: 0.0.0.0 binding + CONTAINER_ENV' -ForegroundColor White
Write-Host '   - kotomake:   OPENAI_API_KEY injected'          -ForegroundColor White
Write-Host '   - techie-hub: Azure FQDN links in config.js'   -ForegroundColor White
Write-Host '============================================'     -ForegroundColor Green
