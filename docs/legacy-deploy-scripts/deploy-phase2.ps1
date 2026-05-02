<#
.SYNOPSIS
  TECHIE Phase 2 deployment script.

.DESCRIPTION
  This script deploys the revised Phase 2 foundation by:
  1) Deploying Azure infra via infra/main.bicep
  2) Applying Stripe/reseller/runtime settings to the existing Container Apps
  3) Initializing PostgreSQL schema from infra/init.sql

.NOTES
  Existing Azure resource names are preserved from the Bicep template:
  - PostgreSQL server: techie-pg-server
  - Container Apps: kotomake, kotomigaki, kotomusubi, techie-hub
#>

[CmdletBinding()]
param(
  [ValidateSet('dev','staging','prod')]
  [string]$Environment = 'prod',

  [string]$DeploymentLabel = 'Phase 2',

  [string]$Location = 'japanwest',

  [string]$SubscriptionId = '',

  [string]$ResourceGroupName = 'TECHIE',

  [string]$ExternalTenantDomain = 'kyotokyotechie.onmicrosoft.com',

  [string]$ExternalTenantName = 'kyotokyotechie',

  [string]$ExternalTenantId = '198ccc88-e870-405e-bb50-5aac609976db',

  [string]$ExternalClientId = 'bbef0e62-048c-49b7-850b-e49c229482d1',

  [string]$ExternalDiscoveryUrl = 'https://kyotokogyotechie.ciamlogin.com/198ccc88-e870-405e-bb50-5aac609976db/v2.0/.well-known/openid-configuration',

  [string]$ExternalIssuerUrl = '',

  [string]$ExternalLoginMethod = 'email_otp',

  [string]$PlatformAdminEmails = '',

  [string]$ServiceBaseUrl = '',

  [string]$HubBaseUrl = '',

  [string]$ExternalIdPolicy = 'default',

  [ValidateSet('express')]
  [string]$StripeConnectAccountType = 'express',

  [ValidateSet('single_step')]
  [string]$CouponApprovalMode = 'single_step',

  [ValidateSet('ledger_on_invoice_paid')]
  [string]$PayoutLedgerMode = 'ledger_on_invoice_paid',

  [ValidateSet('manual_review_then_transfer')]
  [string]$PayoutExecutionMode = 'manual_review_then_transfer',

  [int]$PayoutRetryMaxAttempts = 5,

  [switch]$SkipDatabaseInit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Step([string]$Message) {
  Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Require-Command([string]$Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing command: $Name"
  }
}

function Read-Secret([string]$Prompt, [string]$EnvName, [switch]$Optional) {
  $existing = [Environment]::GetEnvironmentVariable($EnvName)
  if (-not [string]::IsNullOrWhiteSpace($existing)) { return $existing }

  $secure = Read-Host $Prompt -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if (-not $Optional -and [string]::IsNullOrWhiteSpace($value)) {
      throw "$EnvName is required."
    }
    return $value
  }
  finally {
    if ($bstr -ne [IntPtr]::Zero) {
      [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
  }
}

function Read-Required([string]$Prompt, [string]$EnvName) {
  $existing = [Environment]::GetEnvironmentVariable($EnvName)
  if (-not [string]::IsNullOrWhiteSpace($existing)) { return $existing }

  $value = Read-Host $Prompt
  if ([string]::IsNullOrWhiteSpace($value)) {
    throw "$EnvName is required."
  }
  return $value
}

function Ensure-AzLogin {
  $null = az account show --output none 2>$null
  if ($LASTEXITCODE -ne 0) {
    throw 'Azure CLI is not logged in. Run: az login'
  }
}

function Ensure-PostgresExecuteCommand {
  $null = az config set extension.dynamic_install_allow_preview=true 2>$null
  $null = az extension add --name rdbms-connect --allow-preview true --upgrade --yes 2>$null
}

function UrlEncode([string]$Value) {
  return [System.Uri]::EscapeDataString($Value)
}

function Get-OutputValue($Outputs, [string]$Name) {
  if (-not $Outputs.PSObject.Properties.Name.Contains($Name)) {
    throw "Missing deployment output: $Name"
  }
  return $Outputs.$Name.value
}

function Invoke-AzCommandWithRetry {
  param(
    [scriptblock]$Command,
    [string]$FailureMessage,
    [int]$MaxAttempts = 4,
    [int]$DelaySeconds = 5
  )

  $lastError = $null
  for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    try {
      & $Command
      if ($LASTEXITCODE -eq 0) {
        return
      }
      $lastError = "$FailureMessage (exit code $LASTEXITCODE)"
    }
    catch {
      $lastError = $_
    }

    if ($attempt -lt $MaxAttempts) {
      Write-Warning "$FailureMessage. Retrying in $DelaySeconds seconds (attempt $attempt of $MaxAttempts)."
      Start-Sleep -Seconds $DelaySeconds
    }
  }

  if ($lastError -is [System.Management.Automation.ErrorRecord]) {
    throw $lastError
  }

  throw "$FailureMessage. Last error: $lastError"
}

function Update-ContainerAppConfig {
  param(
    [string]$ResourceGroup,
    [string]$AppName,
    [string[]]$EnvPairs
  )

  $imageRef = az containerapp show `
    --resource-group $ResourceGroup `
    --name $AppName `
    --query properties.template.containers[0].image `
    -o tsv 2>$null

  if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($imageRef)) {
    $registryServer = (($imageRef -split '/')[0]).Trim()
    if ($registryServer -like '*.azurecr.io') {
      $registryName = ($registryServer -split '\.')[0]
      $acrCredsJson = az acr credential show --name $registryName -o json 2>$null
      if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($acrCredsJson)) {
        $acrCreds = $acrCredsJson | ConvertFrom-Json
        $acrUsername = $acrCreds.username
        $acrPassword = $acrCreds.passwords[0].value
        if (-not [string]::IsNullOrWhiteSpace($acrUsername) -and -not [string]::IsNullOrWhiteSpace($acrPassword)) {
          Invoke-AzCommandWithRetry `
            -FailureMessage "Failed to refresh registry credentials for Container App: $AppName" `
            -Command {
              az containerapp registry set `
                --resource-group $ResourceGroup `
                --name $AppName `
                --server $registryServer `
                --username $acrUsername `
                --password $acrPassword `
                --output none
            }
        }
      }
    }
  }

  Invoke-AzCommandWithRetry `
    -FailureMessage "Failed to update Container App: $AppName" `
    -Command {
      az containerapp update `
        --resource-group $ResourceGroup `
        --name $AppName `
        --set-env-vars $EnvPairs `
        --output none
    }
}

function Get-ContainerAppFqdn {
  param(
    [string]$ResourceGroup,
    [string]$AppName
  )

  $fqdn = az containerapp show `
    --resource-group $ResourceGroup `
    --name $AppName `
    --query properties.configuration.ingress.fqdn `
    -o tsv 2>$null

  if ($LASTEXITCODE -ne 0) {
    return ''
  }

  return $fqdn
}

function Get-UrlOrFallback {
  param(
    [string]$Preferred,
    [string]$FallbackFqdn
  )

  if (-not [string]::IsNullOrWhiteSpace($Preferred)) {
    return $Preferred.TrimEnd('/')
  }

  if ([string]::IsNullOrWhiteSpace($FallbackFqdn)) {
    return ''
  }

  return "https://$FallbackFqdn"
}

function Get-RedirectUri {
  param(
    [string]$BaseUrl,
    [string]$Path
  )

  if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    return ''
  }

  return ('{0}/{1}' -f $BaseUrl.TrimEnd('/'), $Path.TrimStart('/'))
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

Write-Step 'Reading required secrets'
$postgresAdminPassword = Read-Secret 'PostgreSQL admin password' 'POSTGRES_ADMIN_PASSWORD'
$openaiApiKey = Read-Secret 'OpenAI API key' 'OPENAI_API_KEY'
$stripeSecretKey = Read-Secret 'Stripe secret key' 'STRIPE_SECRET_KEY'
$stripeWebhookSecret = Read-Secret 'Stripe webhook secret' 'STRIPE_WEBHOOK_SECRET' -Optional
$stripePublishableKey = Read-Secret 'Stripe publishable key' 'STRIPE_PUBLISHABLE_KEY' -Optional

Write-Step 'Deploying infrastructure (Bicep)'
$deploymentName = "techie-phase2-$Environment-$(Get-Date -Format 'yyyyMMddHHmmss')"

$deploymentArgs = @(
  'deployment', 'group', 'create',
  '--name', $deploymentName,
  '--resource-group', $ResourceGroupName,
  '--template-file', $templateFile,
  '--parameters',
  "environment=$Environment",
  "postgresAdminPassword=$postgresAdminPassword",
  "openaiApiKey=$openaiApiKey",
  "stripeSecretKey=$stripeSecretKey",
  "stripeWebhookSecret=$(if ([string]::IsNullOrWhiteSpace($stripeWebhookSecret)) { 'pending-webhook-secret' } else { $stripeWebhookSecret })",
  "b2cTenantName=$ExternalTenantName",
  "b2cClientId=$ExternalClientId",
  "b2cPolicy=$ExternalIdPolicy"
)

if (-not [string]::IsNullOrWhiteSpace($stripePublishableKey)) {
  $deploymentArgs += "stripePublishableKey=$stripePublishableKey"
}

$deploymentArgs += @(
  '--query', 'properties.outputs',
  '-o', 'json'
)

$outputsJson = az @deploymentArgs
if ($LASTEXITCODE -ne 0) {
  throw 'Bicep deployment failed.'
}

$outputs = $outputsJson | ConvertFrom-Json
$resourceGroupName = Get-OutputValue $outputs 'resourceGroupName'
$postgresHost = Get-OutputValue $outputs 'postgresHost'
$postgresServerName = Get-OutputValue $outputs 'postgresServerName'
$kotomakeApp = Get-OutputValue $outputs 'kotomakeAppName'
$kotomakeFqdn = Get-OutputValue $outputs 'kotomakeFqdn'
$kotomigakiApp = Get-OutputValue $outputs 'kotomigakiAppName'
$kotomigakiFqdn = Get-OutputValue $outputs 'kotomigakiFqdn'
$kotomusubiApp = Get-OutputValue $outputs 'kotomusubiAppName'
$hubApp = Get-OutputValue $outputs 'hubAppName'
$hubFqdn = Get-OutputValue $outputs 'hubFqdn'
$storageAccountName = Get-OutputValue $outputs 'storageAccountName'
$stripeWebhookQueue = Get-OutputValue $outputs 'stripeWebhookQueueName'
$stripeWebhookDeadLetterQueue = Get-OutputValue $outputs 'stripeWebhookDeadLetterQueueName'
$resellerPayoutQueue = Get-OutputValue $outputs 'resellerPayoutQueueName'
$resellerPayoutDeadLetterQueue = Get-OutputValue $outputs 'resellerPayoutDeadLetterQueueName'
$couponQueue = Get-OutputValue $outputs 'couponQueueName'
$couponDeadLetterQueue = Get-OutputValue $outputs 'couponDeadLetterQueueName'
$appInsightsName = Get-OutputValue $outputs 'appInsightsName'

if ([string]::IsNullOrWhiteSpace($kotomakeFqdn)) {
  $kotomakeFqdn = Get-ContainerAppFqdn -ResourceGroup $resourceGroupName -AppName $kotomakeApp
}
if ([string]::IsNullOrWhiteSpace($kotomigakiFqdn)) {
  $kotomigakiFqdn = Get-ContainerAppFqdn -ResourceGroup $resourceGroupName -AppName $kotomigakiApp
}
if ([string]::IsNullOrWhiteSpace($hubFqdn)) {
  $hubFqdn = Get-ContainerAppFqdn -ResourceGroup $resourceGroupName -AppName $hubApp
}

$hubUrl = Get-UrlOrFallback -Preferred $HubBaseUrl -FallbackFqdn $hubFqdn
$serviceRoot = Get-UrlOrFallback -Preferred $ServiceBaseUrl -FallbackFqdn $kotomakeFqdn
$kotomakeUrl = "https://$kotomakeFqdn"
$kotomigakiUrl = "https://$kotomigakiFqdn"
$kotomusubiUrl = if ([string]::IsNullOrWhiteSpace($ServiceBaseUrl)) { '' } else { Get-RedirectUri -BaseUrl $serviceRoot -Path '/api/kotomusubi' }
$stripeWebhookUrl = if ([string]::IsNullOrWhiteSpace($serviceRoot)) { '' } else { Get-RedirectUri -BaseUrl $serviceRoot -Path '/webhook/stripe' }
$externalRedirectUri = if ([string]::IsNullOrWhiteSpace($hubUrl)) { '' } else { Get-RedirectUri -BaseUrl $hubUrl -Path '/auth/callback' }
$externalPostLogoutRedirectUri = if ([string]::IsNullOrWhiteSpace($hubUrl)) { '' } else { Get-RedirectUri -BaseUrl $hubUrl -Path '/signed-out' }

$resolvedIssuerUrl = $ExternalIssuerUrl
if ([string]::IsNullOrWhiteSpace($resolvedIssuerUrl) -and -not [string]::IsNullOrWhiteSpace($ExternalDiscoveryUrl)) {
  try {
    $discovery = Invoke-RestMethod -Uri $ExternalDiscoveryUrl -Method Get -TimeoutSec 20
    $resolvedIssuerUrl = $discovery.issuer
  }
  catch {
    Write-Warning "Could not resolve issuer from discovery URL. Set -ExternalIssuerUrl manually if token validation fails."
  }
}

$encodedPgPassword = UrlEncode $postgresAdminPassword
$databaseUrl = "postgresql://techieadmin:$encodedPgPassword@$postgresHost:5432/techie?sslmode=require"
$authDevMode = if ($Environment -eq 'dev') { '1' } else { '0' }

$commonEnv = @(
  "AUTH_DEV_MODE=$authDevMode",
  "AUTH_IDENTITY_MODE=entra_external_id",
  "ENTRA_EXTERNAL_ID_TENANT_NAME=$ExternalTenantName",
  "ENTRA_EXTERNAL_ID_TENANT_DOMAIN=$ExternalTenantDomain",
  "ENTRA_EXTERNAL_ID_TENANT_ID=$ExternalTenantId",
  "ENTRA_EXTERNAL_ID_CLIENT_ID=$ExternalClientId",
  "ENTRA_EXTERNAL_ID_POLICY=$ExternalIdPolicy",
  "ENTRA_EXTERNAL_ID_DISCOVERY_URL=$ExternalDiscoveryUrl",
  "ENTRA_EXTERNAL_ID_LOGIN_METHOD=$ExternalLoginMethod",
  "AZURE_B2C_TENANT_NAME=$ExternalTenantName",
  "AZURE_B2C_CLIENT_ID=$ExternalClientId",
  "AZURE_B2C_POLICY=$ExternalIdPolicy",
  "STRIPE_SECRET_KEY=$stripeSecretKey",
  "STRIPE_PLATFORM_MODE=separate_charges_and_transfers",
  "STRIPE_CONNECT_ACCOUNT_TYPE=$StripeConnectAccountType",
  "STRIPE_BILLING_OWNER=platform",
  "STRIPE_QUEUE_PROVIDER=azure_storage_queue",
  "AZURE_STORAGE_ACCOUNT_NAME=$storageAccountName",
  "STRIPE_WEBHOOK_QUEUE=$stripeWebhookQueue",
  "STRIPE_WEBHOOK_DEADLETTER_QUEUE=$stripeWebhookDeadLetterQueue",
  "RESELLER_PAYOUT_QUEUE=$resellerPayoutQueue",
  "RESELLER_PAYOUT_DEADLETTER_QUEUE=$resellerPayoutDeadLetterQueue",
  "COUPON_QUEUE=$couponQueue",
  "COUPON_DEADLETTER_QUEUE=$couponDeadLetterQueue",
  "COUPON_APPROVAL_MODE=$CouponApprovalMode",
  "PAYOUT_LEDGER_MODE=$PayoutLedgerMode",
  "PAYOUT_EXECUTION_MODE=$PayoutExecutionMode",
  "PAYOUT_RETRY_MAX_ATTEMPTS=$PayoutRetryMaxAttempts",
  "APPINSIGHTS_COMPONENT_NAME=$appInsightsName",
  "CONTRACT_CARDINALITY=multi_contract_per_tenant",
  "SERVICE_LEDGER_MODE=per_service_contract"
)

if (-not [string]::IsNullOrWhiteSpace($resolvedIssuerUrl)) {
  $commonEnv += "ENTRA_EXTERNAL_ID_ISSUER=$resolvedIssuerUrl"
  $commonEnv += "AZURE_B2C_ISSUER=$resolvedIssuerUrl"
}

if (-not [string]::IsNullOrWhiteSpace($stripePublishableKey)) {
  $commonEnv += "STRIPE_PUBLISHABLE_KEY=$stripePublishableKey"
}

if (-not [string]::IsNullOrWhiteSpace($stripeWebhookSecret)) {
  $commonEnv += "STRIPE_WEBHOOK_SECRET=$stripeWebhookSecret"
}

if (-not [string]::IsNullOrWhiteSpace($PlatformAdminEmails)) {
  $commonEnv += "PLATFORM_ADMIN_EMAILS=$PlatformAdminEmails"
}

if (-not [string]::IsNullOrWhiteSpace($stripeWebhookUrl)) {
  $commonEnv += "STRIPE_WEBHOOK_URL=$stripeWebhookUrl"
}

if (-not [string]::IsNullOrWhiteSpace($externalRedirectUri)) {
  $commonEnv += "ENTRA_EXTERNAL_ID_REDIRECT_URI=$externalRedirectUri"
}

if (-not [string]::IsNullOrWhiteSpace($externalPostLogoutRedirectUri)) {
  $commonEnv += "ENTRA_EXTERNAL_ID_POST_LOGOUT_REDIRECT_URI=$externalPostLogoutRedirectUri"
}

Write-Step "Applying $DeploymentLabel runtime config to Container Apps"
Update-ContainerAppConfig `
  -ResourceGroup $resourceGroupName `
  -AppName $kotomakeApp `
  -EnvPairs ($commonEnv + @(
    "DATABASE_URL=$databaseUrl"
  ))

Update-ContainerAppConfig `
  -ResourceGroup $resourceGroupName `
  -AppName $kotomigakiApp `
  -EnvPairs ($commonEnv + @(
    "DATABASE_URL=$databaseUrl"
  ))

Update-ContainerAppConfig `
  -ResourceGroup $resourceGroupName `
  -AppName $kotomusubiApp `
  -EnvPairs ($commonEnv + @(
    "KOTOMUSUBI_URL=$kotomusubiUrl"
  ))

Write-Step 'Updating hub endpoints and shared auth/runtime config'
Update-ContainerAppConfig `
  -ResourceGroup $resourceGroupName `
  -AppName $hubApp `
  -EnvPairs ($commonEnv + @(
    "DATABASE_URL=$databaseUrl",
    "KOTOMAKE_URL=$kotomakeUrl",
    "KOTOMIGAKI_URL=$kotomigakiUrl",
    "KOTOMUSUBI_URL=$kotomusubiUrl",
    "HUB_URL=$hubUrl"
  ))

if (-not $SkipDatabaseInit) {
  Write-Step 'Initializing PostgreSQL schema (infra/init.sql)'
  Ensure-PostgresExecuteCommand
  az postgres flexible-server execute `
    --name $postgresServerName `
    --admin-user techieadmin `
    --admin-password $postgresAdminPassword `
    --database-name techie `
    --file-path $initSqlFile `
    --output none

  if ($LASTEXITCODE -ne 0) {
    Write-Warning 'Database initialization command failed. If the PostgreSQL server is private-only, run init.sql from a host inside the VNet.'
  }
}

Write-Step 'Deployment summary'
Write-Host "Resource Group                    : $resourceGroupName" -ForegroundColor Green
Write-Host "PostgreSQL Server                 : $postgresServerName" -ForegroundColor Green
Write-Host "PostgreSQL Host                   : $postgresHost" -ForegroundColor Green
Write-Host "Container App - kotomake          : $kotomakeApp" -ForegroundColor Green
Write-Host "Container App - kotomigaki        : $kotomigakiApp" -ForegroundColor Green
Write-Host "Container App - kotomusubi        : $kotomusubiApp" -ForegroundColor Green
Write-Host "Container App - techie-hub        : $hubApp" -ForegroundColor Green
Write-Host "Storage Account                   : $storageAccountName" -ForegroundColor Green
Write-Host "Webhook Queue                     : $stripeWebhookQueue" -ForegroundColor Green
Write-Host "Payout Queue                      : $resellerPayoutQueue" -ForegroundColor Green
Write-Host "Coupon Queue                      : $couponQueue" -ForegroundColor Green
Write-Host "Application Insights              : $appInsightsName" -ForegroundColor Green
Write-Host "Hub URL                           : $hubUrl" -ForegroundColor Green
Write-Host "Kotomake URL                      : $kotomakeUrl" -ForegroundColor Green
Write-Host "Kotomigaki URL                    : $kotomigakiUrl" -ForegroundColor Green
Write-Host "Stripe Webhook URL                : $stripeWebhookUrl" -ForegroundColor Green
Write-Host "External ID Redirect URI          : $externalRedirectUri" -ForegroundColor Green
Write-Host "External ID Post-logout Redirect  : $externalPostLogoutRedirectUri" -ForegroundColor Green

Write-Host "`n$DeploymentLabel deployment script finished." -ForegroundColor Yellow
Write-Host 'Client follow-up items:' -ForegroundColor Yellow
Write-Host '  1) Register the Redirect URI and Post-logout Redirect URI shown above in Entra External ID.' -ForegroundColor Yellow
if ([string]::IsNullOrWhiteSpace($stripeWebhookSecret)) {
  Write-Host '  2) Register the Stripe webhook URL shown above in Stripe and then rerun with STRIPE_WEBHOOK_SECRET set.' -ForegroundColor Yellow
}
else {
  Write-Host '  2) Verify Stripe webhook delivery against the URL shown above.' -ForegroundColor Yellow
}
Write-Host '  3) If a custom domain will replace the Azure hostname, rerun with -ServiceBaseUrl and -HubBaseUrl set to the final HTTPS URLs.' -ForegroundColor Yellow
