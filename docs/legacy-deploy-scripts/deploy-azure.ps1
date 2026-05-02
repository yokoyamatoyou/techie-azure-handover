<#
.SYNOPSIS
    TECHIE SaaS - Azure Deployment Script (Phases 2-4)
    Region: Japan West | Resource Group: TECHIE
    ACR: techiereg2026 (4 images already pushed)

.DESCRIPTION
    Phase 1: DONE - Images pushed to ACR
    Phase 2: PostgreSQL Flexible Server
    Phase 3: Container Apps Environment + 4 services
    Phase 4: Domain mapping prep for techie.app

.NOTES
    Run from D:\azure with proxy env vars already set.
    Requires: az CLI logged in, subscription selected.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ================================================================
# VARIABLES - edit these before running
# ================================================================
$RG           = 'TECHIE'
$LOCATION     = 'japanwest'
$ACR_NAME     = 'techiereg2026'
$ACR_LOGIN    = "$ACR_NAME.azurecr.io"

# PostgreSQL
$PG_SERVER    = 'techie-pg-server'
$PG_DB        = 'techie'
$PG_ADMIN     = 'techieadmin'
$PG_PASSWORD  = 'Techie#2026!Deploy'   # CHANGE THIS for production

# Container Apps
$ENV_NAME     = 'techie-cae'
$LOG_WS       = 'techie-logs'

Write-Host '============================================' -ForegroundColor Cyan
Write-Host ' TECHIE Azure Deployment - Phases 2-4'       -ForegroundColor Cyan
Write-Host ' Region: Japan West | RG: TECHIE'            -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan

# ================================================================
# PHASE 2: PostgreSQL Flexible Server
# ================================================================
Write-Host "`n===== PHASE 2: PostgreSQL =====" -ForegroundColor Yellow

# 2.1 Create the PostgreSQL Flexible Server
Write-Host '[2.1] Creating PostgreSQL Flexible Server...' -ForegroundColor Cyan
az postgres flexible-server create `
    --resource-group $RG `
    --name $PG_SERVER `
    --location $LOCATION `
    --admin-user $PG_ADMIN `
    --admin-password $PG_PASSWORD `
    --sku-name Standard_B1ms `
    --tier Burstable `
    --version 16 `
    --storage-size 32 `
    --yes `
    --public-access 0.0.0.0 `
    --output table
# --public-access 0.0.0.0 allows Azure services (Container Apps) to connect

Write-Host '[2.1] PostgreSQL server created.' -ForegroundColor Green

# 2.2 Create the database
Write-Host '[2.2] Creating database...' -ForegroundColor Cyan
az postgres flexible-server db create `
    --resource-group $RG `
    --server-name $PG_SERVER `
    --database-name $PG_DB `
    --output table

Write-Host '[2.2] Database created.' -ForegroundColor Green

# 2.3 Allow Azure services through firewall
Write-Host '[2.3] Adding firewall rule for Azure services...' -ForegroundColor Cyan
az postgres flexible-server firewall-rule create `
    --resource-group $RG `
    --name $PG_SERVER `
    --rule-name AllowAzureServices `
    --start-ip-address 0.0.0.0 `
    --end-ip-address 0.0.0.0 `
    --output table

Write-Host '[2.3] Firewall rule added.' -ForegroundColor Green

# 2.4 Initialize schema
# psql is not installed locally - run init.sql manually via Azure Portal:
#   1. Go to: portal.azure.com > TECHIE > techie-pg-server > Databases > techie
#   2. Click "Connect" at the top (or use the Query editor preview)
#   3. Paste the contents of infra\init.sql and execute
$PG_HOST = "$PG_SERVER.postgres.database.azure.com"
Write-Host '[2.4] MANUAL STEP: Run infra\init.sql via Azure Portal Query Editor' -ForegroundColor Yellow
Write-Host "       Server: $PG_HOST" -ForegroundColor Gray
Write-Host "       DB: $PG_DB | User: $PG_ADMIN" -ForegroundColor Gray
Write-Host '       Portal > TECHIE > techie-pg-server > Databases > techie > Connect' -ForegroundColor Gray
Write-Host '       Paste contents of infra\init.sql and execute.' -ForegroundColor Gray
Write-Host ''
Read-Host '       Press ENTER after you have run init.sql in the Portal'

# Build the connection string for Container Apps
$DATABASE_URL = "postgresql://${PG_ADMIN}:${PG_PASSWORD}@${PG_HOST}:5432/${PG_DB}?sslmode=require"
Write-Host "DATABASE_URL = $DATABASE_URL" -ForegroundColor DarkGray

Write-Host "`n===== PHASE 2 COMPLETE =====" -ForegroundColor Green

# ================================================================
# PHASE 3: Container Apps Environment + Deploy Services
# ================================================================
Write-Host "`n===== PHASE 3: Container Apps =====" -ForegroundColor Yellow

# 3.1 Create Log Analytics workspace
Write-Host '[3.1] Creating Log Analytics workspace...' -ForegroundColor Cyan
az monitor log-analytics workspace create `
    --resource-group $RG `
    --workspace-name $LOG_WS `
    --location $LOCATION `
    --output table

$LOG_ID = az monitor log-analytics workspace show `
    --resource-group $RG `
    --workspace-name $LOG_WS `
    --query customerId -o tsv

$LOG_KEY = az monitor log-analytics workspace get-shared-keys `
    --resource-group $RG `
    --workspace-name $LOG_WS `
    --query primarySharedKey -o tsv

Write-Host '[3.1] Log Analytics ready.' -ForegroundColor Green

# 3.2 Create Container Apps Environment
Write-Host '[3.2] Creating Container Apps Environment...' -ForegroundColor Cyan
az containerapp env create `
    --resource-group $RG `
    --name $ENV_NAME `
    --location $LOCATION `
    --logs-workspace-id $LOG_ID `
    --logs-workspace-key $LOG_KEY `
    --output table

Write-Host '[3.2] Environment created.' -ForegroundColor Green

# 3.3 Get ACR credentials for Container Apps
$ACR_USER = az acr credential show --name $ACR_NAME --query username -o tsv
$ACR_PASS = az acr credential show --name $ACR_NAME --query 'passwords[0].value' -o tsv

# 3.4 Deploy TECHIE HUB (nginx - no DB needed)
Write-Host '[3.4] Deploying techie-hub...' -ForegroundColor Cyan
az containerapp create `
    --resource-group $RG `
    --name techie-hub `
    --environment $ENV_NAME `
    --image "${ACR_LOGIN}/techie-hub:latest" `
    --registry-server $ACR_LOGIN `
    --registry-username $ACR_USER `
    --registry-password $ACR_PASS `
    --target-port 8090 `
    --ingress external `
    --min-replicas 1 `
    --max-replicas 3 `
    --cpu 0.25 `
    --memory 0.5Gi `
    --output table

Write-Host '[3.4] techie-hub deployed.' -ForegroundColor Green

# 3.5 Deploy kotomigaki (aio2-main - needs DB + Playwright)
Write-Host '[3.5] Deploying kotomigaki...' -ForegroundColor Cyan
az containerapp create `
    --resource-group $RG `
    --name kotomigaki `
    --environment $ENV_NAME `
    --image "${ACR_LOGIN}/kotomigaki:latest" `
    --registry-server $ACR_LOGIN `
    --registry-username $ACR_USER `
    --registry-password $ACR_PASS `
    --target-port 8081 `
    --ingress external `
    --min-replicas 1 `
    --max-replicas 5 `
    --cpu 1.0 `
    --memory 2.0Gi `
    --env-vars `
        PORT=8081 `
        HEADLESS=1 `
        CONTAINER_ENV=1 `
        DATABASE_URL="$DATABASE_URL" `
        PLAYWRIGHT_BROWSERS_PATH=/ms-playwright `
    --output table

Write-Host '[3.5] kotomigaki deployed.' -ForegroundColor Green

# 3.6 Deploy kotomake (notecode)
Write-Host '[3.6] Deploying kotomake...' -ForegroundColor Cyan
az containerapp create `
    --resource-group $RG `
    --name kotomake `
    --environment $ENV_NAME `
    --image "${ACR_LOGIN}/kotomake:latest" `
    --registry-server $ACR_LOGIN `
    --registry-username $ACR_USER `
    --registry-password $ACR_PASS `
    --target-port 8080 `
    --ingress external `
    --min-replicas 1 `
    --max-replicas 3 `
    --cpu 0.5 `
    --memory 1.0Gi `
    --env-vars `
        PORT=8080 `
        HEADLESS=1 `
        CONTAINER_ENV=1 `
    --output table

Write-Host '[3.6] kotomake deployed.' -ForegroundColor Green

# 3.7 Deploy kotomusubi (doorknock)
Write-Host '[3.7] Deploying kotomusubi...' -ForegroundColor Cyan
az containerapp create `
    --resource-group $RG `
    --name kotomusubi `
    --environment $ENV_NAME `
    --image "${ACR_LOGIN}/kotomusubi:latest" `
    --registry-server $ACR_LOGIN `
    --registry-username $ACR_USER `
    --registry-password $ACR_PASS `
    --target-port 8082 `
    --ingress external `
    --min-replicas 1 `
    --max-replicas 3 `
    --cpu 1.0 `
    --memory 2.0Gi `
    --env-vars `
        PORT=8082 `
        HEADLESS=1 `
        CONTAINER_ENV=1 `
        PYTHONPATH=/app:/app/aio2-main `
    --output table

Write-Host '[3.7] kotomusubi deployed.' -ForegroundColor Green

# 3.8 Show all FQDNs
Write-Host "`n[3.8] Service URLs:" -ForegroundColor Cyan
$services = @('techie-hub', 'kotomigaki', 'kotomake', 'kotomusubi')
foreach ($svc in $services) {
    $fqdn = az containerapp show `
        --resource-group $RG `
        --name $svc `
        --query 'properties.configuration.ingress.fqdn' -o tsv
    Write-Host "  $svc : https://$fqdn" -ForegroundColor White
}

Write-Host "`n===== PHASE 3 COMPLETE =====" -ForegroundColor Green

# ================================================================
# PHASE 4: Domain Mapping Prep (techie.app)
# ================================================================
Write-Host "`n===== PHASE 4: Domain Prep =====" -ForegroundColor Yellow

# 4.1 Get the environment's default domain and static IP
Write-Host '[4.1] Getting environment details for DNS...' -ForegroundColor Cyan
$ENV_DOMAIN = az containerapp env show `
    --resource-group $RG `
    --name $ENV_NAME `
    --query 'properties.defaultDomain' -o tsv

$ENV_IP = az containerapp env show `
    --resource-group $RG `
    --name $ENV_NAME `
    --query 'properties.staticIp' -o tsv

Write-Host ''
Write-Host '============================================' -ForegroundColor Yellow
Write-Host ' DNS RECORDS NEEDED for techie.app'           -ForegroundColor Yellow
Write-Host '============================================' -ForegroundColor Yellow
Write-Host ''
Write-Host "  Step 1: Add a TXT record for domain verification:" -ForegroundColor White
Write-Host "    Host:  asuid.techie.app"                         -ForegroundColor Gray
Write-Host "    Value: (get via 'az containerapp hostname show')" -ForegroundColor Gray
Write-Host ''
Write-Host "  Step 2: Add an A record:" -ForegroundColor White
Write-Host "    Host:  @"                                         -ForegroundColor Gray
Write-Host "    Value: $ENV_IP"                                   -ForegroundColor Gray
Write-Host ''
Write-Host "  Step 3: Add a CNAME record (for www):" -ForegroundColor White
Write-Host "    Host:  www"                                       -ForegroundColor Gray
Write-Host "    Value: techie-hub.$ENV_DOMAIN"                    -ForegroundColor Gray
Write-Host ''
Write-Host "  After DNS propagates, bind the domain:" -ForegroundColor White
Write-Host "    az containerapp hostname add --resource-group $RG --name techie-hub --hostname techie.app" -ForegroundColor Gray
Write-Host ''
Write-Host "  Then enable managed certificate:" -ForegroundColor White
Write-Host "    az containerapp hostname bind --resource-group $RG --name techie-hub --hostname techie.app --environment $ENV_NAME --validation-method CNAME" -ForegroundColor Gray
Write-Host ''

Write-Host '===== PHASE 4 COMPLETE =====' -ForegroundColor Green
Write-Host ''
Write-Host '============================================' -ForegroundColor Green
Write-Host ' DEPLOYMENT COMPLETE!'                        -ForegroundColor Green
Write-Host ' Next: Configure DNS and bind techie.app'     -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Green
