<#
.SYNOPSIS
  TECHIE Phase 2 one-shot deployment script.

.DESCRIPTION
  This script completes Phase 2 by:
  1) Deploying Azure infra via infra/main.bicep
  2) Applying auth/multi-tenant/Stripe runtime settings to Container Apps
  3) Initializing PostgreSQL schema from infra/init.sql (RLS + tenant tables)

.NOTES
  - Run from any location; script resolves paths relative to itself.
  - Requires Azure CLI login and sufficient permissions.
  - Uses secure prompts if env vars are missing.
#>

[CmdletBinding()]
param(
  [ValidateSet('dev','staging','prod')]
  [string]$Environment = 'prod',

  [string]$Location = 'japanwest',

  [string]$SubscriptionId = '',

  [string]$B2CPolicy = 'B2C_1_signup_signin',

  [switch]$SkipDatabaseInit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Step([string]$msg) {
  Write-Host "`n=== $msg ===" -ForegroundColor Cyan
}

function Require-Command([string]$name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Missing command: $name"
  }
}

function Read-Secret([string]$prompt, [string]$envName) {
  $existing = [Environment]::GetEnvironmentVariable($envName)
  if ($existing) { return $existing }

  $secure = Read-Host "$prompt" -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  }
  finally {
    if ($bstr -ne [IntPtr]::Zero) {
      [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
  }
}

function Read-Required([string]$prompt, [string]$envName) {
  $existing = [Environment]::GetEnvironmentVariable($envName)
  if ($existing) { return $existing }

  $value = Read-Host $prompt
  if ([string]::IsNullOrWhiteSpace($value)) {
    throw "$envName is required."
  }
  return $value
}

function Ensure-AzLogin {
  $null = az account show --output none 2>$null
  if ($LASTEXITCODE -ne 0) {
    throw "Azure CLI is not logged in. Run: az login"
  }
}

function UrlEncode([string]$value) {
  return [System.Uri]::EscapeDataString($value)
}

function Update-ContainerAppPhase2Config {
  param(
    [string]$ResourceGroup,
    [string]$AppName,
    [string]$B2CTenantName,
    [string]$B2CClientId,
    [string]$B2CPolicyName,
    [string]$DatabaseUrl,
    [string]$StripeSecret,
    [string]$StripeWebhookSecret,
    [bool]$SetDb
  )

  $envPairs = @(
    "AUTH_DEV_MODE=0",
    "AZURE_B2C_TENANT_NAME=$B2CTenantName",
    "AZURE_B2C_CLIENT_ID=$B2CClientId",
    "AZURE_B2C_POLICY=$B2CPolicyName",
    "STRIPE_SECRET_KEY=$StripeSecret",
    "STRIPE_WEBHOOK_SECRET=$StripeWebhookSecret"
  )

  if ($SetDb) {
    $envPairs += "DATABASE_URL=$DatabaseUrl"
  }

  az containerapp update `
    --resource-group $ResourceGroup `
    --name $AppName `
    --set-env-vars $envPairs `
    --output none

  if ($LASTEXITCODE -ne 0) {
    throw "Failed to update Container App: $AppName"
  }
}

Write-Step 'Preflight checks'
Require-Command 'az'
Ensure-AzLogin

if (-not [string]::IsNullOrWhiteSpace($SubscriptionId)) {
  az account set --subscription $SubscriptionId
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$templateFile = Join-Path $scriptRoot 'infra\main.bicep'
$initSqlFile = Join-Path $scriptRoot 'infra\init.sql'

if (-not (Test-Path $templateFile)) {
  throw "Template not found: $templateFile"
}
if (-not (Test-Path $initSqlFile)) {
  throw "SQL file not found: $initSqlFile"
}

Write-Step 'Reading required secrets and config'
$postgresAdminPassword = Read-Secret 'PostgreSQL admin password' 'POSTGRES_ADMIN_PASSWORD'
$openaiApiKey = Read-Secret 'OpenAI API key' 'OPENAI_API_KEY'
$stripeSecretKey = Read-Secret 'Stripe secret key' 'STRIPE_SECRET_KEY'
$stripeWebhookSecret = Read-Secret 'Stripe webhook secret' 'STRIPE_WEBHOOK_SECRET'
$b2cTenantName = Read-Required 'Azure AD B2C tenant name (without domain)' 'AZURE_B2C_TENANT_NAME'
$b2cClientId = Read-Required 'Azure AD B2C client ID' 'AZURE_B2C_CLIENT_ID'

Write-Step 'Deploying infrastructure (Bicep)'
$deploymentName = "techie-phase2-$Environment-$(Get-Date -Format 'yyyyMMddHHmmss')"

$outputsJson = az deployment sub create `
  --name $deploymentName `
  --location $Location `
  --template-file $templateFile `
  --parameters environment=$Environment `
              postgresAdminPassword=$postgresAdminPassword `
              openaiApiKey=$openaiApiKey `
              stripeSecretKey=$stripeSecretKey `
              stripeWebhookSecret=$stripeWebhookSecret `
              b2cTenantName=$b2cTenantName `
              b2cClientId=$b2cClientId `
  --query properties.outputs `
  -o json

if ($LASTEXITCODE -ne 0) {
  throw 'Bicep deployment failed.'
}

$outputs = $outputsJson | ConvertFrom-Json
$resourceGroupName = $outputs.resourceGroupName.value
$postgresHost = $outputs.postgresHost.value
$kotomakeFqdn = $outputs.kotomakeFqdn.value
$kotomigakiFqdn = $outputs.kotomigakiFqdn.value
$hubFqdn = $outputs.hubFqdn.value

if ([string]::IsNullOrWhiteSpace($resourceGroupName)) {
  throw 'Could not resolve resource group from deployment outputs.'
}

$encodedPgPassword = UrlEncode $postgresAdminPassword
$databaseUrl = "postgresql://techieadmin:$encodedPgPassword@$postgresHost:5432/techie?sslmode=require"

Write-Step 'Applying Phase 2 runtime config to Container Apps'
$kotomakeApp = "kotomake"
$kotomigakiApp = "kotomigaki"
$kotomusubiApp = "kotomusubi"
$hubApp = "techie-hub"

Update-ContainerAppPhase2Config `
  -ResourceGroup $resourceGroupName `
  -AppName $kotomakeApp `
  -B2CTenantName $b2cTenantName `
  -B2CClientId $b2cClientId `
  -B2CPolicyName $B2CPolicy `
  -DatabaseUrl $databaseUrl `
  -StripeSecret $stripeSecretKey `
  -StripeWebhookSecret $stripeWebhookSecret `
  -SetDb $true

Update-ContainerAppPhase2Config `
  -ResourceGroup $resourceGroupName `
  -AppName $kotomigakiApp `
  -B2CTenantName $b2cTenantName `
  -B2CClientId $b2cClientId `
  -B2CPolicyName $B2CPolicy `
  -DatabaseUrl $databaseUrl `
  -StripeSecret $stripeSecretKey `
  -StripeWebhookSecret $stripeWebhookSecret `
  -SetDb $true

Update-ContainerAppPhase2Config `
  -ResourceGroup $resourceGroupName `
  -AppName $kotomusubiApp `
  -B2CTenantName $b2cTenantName `
  -B2CClientId $b2cClientId `
  -B2CPolicyName $B2CPolicy `
  -DatabaseUrl $databaseUrl `
  -StripeSecret $stripeSecretKey `
  -StripeWebhookSecret $stripeWebhookSecret `
  -SetDb $false

Write-Step 'Updating hub endpoints'
az containerapp update `
  --resource-group $resourceGroupName `
  --name $hubApp `
  --set-env-vars `
    "KOTOMAKE_URL=https://$kotomakeFqdn" `
    "KOTOMIGAKI_URL=https://$kotomigakiFqdn" `
    "HUB_URL=https://$hubFqdn" `
    "AZURE_B2C_TENANT_NAME=$b2cTenantName" `
    "AZURE_B2C_CLIENT_ID=$b2cClientId" `
    "AZURE_B2C_POLICY=$B2CPolicy" `
  --output none

if ($LASTEXITCODE -ne 0) {
  throw "Failed to update Container App: $hubApp"
}

if (-not $SkipDatabaseInit) {
  Write-Step 'Initializing PostgreSQL schema (infra/init.sql)'
  $sqlText = Get-Content -Raw -Path $initSqlFile
  $pgServerName = "techie-pg-server"

  az postgres flexible-server execute `
    --name $pgServerName `
    --admin-user techieadmin `
    --admin-password $postgresAdminPassword `
    --database-name techie `
    --querytext $sqlText `
    --output none

  if ($LASTEXITCODE -ne 0) {
    Write-Warning 'Database initialization command failed. If server is private-only, run init.sql from a host inside the VNet.'
  }
}

Write-Step 'Deployment summary'
Write-Host "Resource Group : $resourceGroupName" -ForegroundColor Green
Write-Host "Hub URL        : https://$hubFqdn" -ForegroundColor Green
Write-Host "Kotomake URL   : https://$kotomakeFqdn" -ForegroundColor Green
Write-Host "Kotomigaki URL : https://$kotomigakiFqdn" -ForegroundColor Green
Write-Host "PostgreSQL Host: $postgresHost" -ForegroundColor Green

Write-Host "`nPhase 2 deployment script finished." -ForegroundColor Yellow
Write-Host 'Next checks:' -ForegroundColor Yellow
Write-Host '  1) Validate SSO login flow (Google/Microsoft/Email in B2C)' -ForegroundColor Yellow
Write-Host '  2) Validate Stripe webhook endpoint wiring in your app routers' -ForegroundColor Yellow
Write-Host '  3) Run cross-tenant isolation test (A data not visible to B)' -ForegroundColor Yellow
