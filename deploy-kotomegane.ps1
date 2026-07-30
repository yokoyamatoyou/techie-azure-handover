[CmdletBinding()]
param(
  [ValidateSet('dev','staging','prod')]
  [string]$Environment = 'prod',

  [string]$Location = 'japanwest',

  [string]$SubscriptionId = '',

  [string]$ResourceGroupName = 'TECHIE',

  [string]$ManagedEnvironmentName = 'techie-cae',

  [string]$ContainerAppName = 'kotomegane',

  [string]$AcrName = 'techiereg2026',

  [string]$PostgresServerName = 'techie-pg-server',

  [string]$PostgresDatabaseName = 'techie',

  [string]$PostgresAdminUser = 'techieadmin',

  [string]$ExternalTenantDomain = 'kyotokyotechie.onmicrosoft.com',

  [string]$ExternalTenantName = 'kyotokyotechie',

  [string]$ExternalTenantId = '198ccc88-e870-405e-bb50-5aac609976db',

  [string]$ExternalClientId = 'bbef0e62-048c-49b7-850b-e49c229482d1',

  [string]$ExternalDiscoveryUrl = 'https://kyotokogyotechie.ciamlogin.com/198ccc88-e870-405e-bb50-5aac609976db/v2.0/.well-known/openid-configuration',

  [string]$ExternalIssuerUrl = '',

  [string]$ExternalLoginMethod = 'email_otp',

  [string]$ExternalIdPolicy = 'default',

  [string]$PlatformAdminEmails = '',

  [string]$ServiceBaseUrl = 'https://api.techie.jp',

  [string]$HubBaseUrl = 'https://app.techie.jp',

  [double]$Cpu = 1.0,

  [string]$Memory = '2Gi',

  [switch]$SkipBuild
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

  if ($Optional) {
    return ''
  }

  $secure = Read-Host $Prompt -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if ([string]::IsNullOrWhiteSpace($value)) {
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

function Ensure-AzLogin {
  $null = az account show --output none 2>$null
  if ($LASTEXITCODE -ne 0) {
    throw 'Azure CLI is not logged in. Run: az login'
  }
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

function UrlEncode([string]$Value) {
  return [System.Uri]::EscapeDataString($Value)
}

function Get-ContainerAppExists {
  param(
    [string]$ResourceGroup,
    [string]$AppName
  )

  $result = az containerapp list `
    --resource-group $ResourceGroup `
    --query "[?name=='$AppName'] | length(@)" `
    -o tsv 2>$null

  if ($LASTEXITCODE -ne 0) {
    return $false
  }

  return ([string]::Equals(($result | Out-String).Trim(), '1', [System.StringComparison]::Ordinal))
}

Write-Step 'Preflight checks'
Require-Command 'az'
Ensure-AzLogin

if (-not [string]::IsNullOrWhiteSpace($SubscriptionId)) {
  az account set --subscription $SubscriptionId
}

$repoRoot = $PSScriptRoot
$dockerFile = Join-Path $repoRoot 'kotomegane\Dockerfile'
if (-not (Test-Path $dockerFile)) {
  throw "Kotomegane Dockerfile not found: $dockerFile"
}

Write-Step 'Reading required secrets'
$postgresAdminPassword = Read-Secret 'PostgreSQL admin password' 'POSTGRES_ADMIN_PASSWORD'
$openaiApiKey = Read-Secret 'OpenAI API key' 'OPENAI_API_KEY'
$geminiApiKey = Read-Secret 'Gemini API key (optional)' 'GEMINI_API_KEY' -Optional
$anthropicApiKey = Read-Secret 'Anthropic API key (optional)' 'ANTHROPIC_API_KEY' -Optional

$providerKeys = [System.Collections.Generic.List[string]]::new()
$providerKeys.Add('openai')
if (-not [string]::IsNullOrWhiteSpace($geminiApiKey)) {
  $providerKeys.Add('gemini')
}
if (-not [string]::IsNullOrWhiteSpace($anthropicApiKey)) {
  $providerKeys.Add('claude')
}
$enabledProvidersValue = ($providerKeys | Select-Object -Unique) -join ','

$resolvedIssuerUrl = $ExternalIssuerUrl
if ([string]::IsNullOrWhiteSpace($resolvedIssuerUrl) -and -not [string]::IsNullOrWhiteSpace($ExternalDiscoveryUrl)) {
  try {
    $discovery = Invoke-RestMethod -Uri $ExternalDiscoveryUrl -Method Get -TimeoutSec 20
    $resolvedIssuerUrl = $discovery.issuer
  }
  catch {
    Write-Warning 'Could not resolve issuer from discovery URL. Continuing with the provided value only.'
  }
}

$resolvedServiceBaseUrl = $ServiceBaseUrl.TrimEnd('/')
$resolvedHubBaseUrl = $HubBaseUrl.TrimEnd('/')
$externalRedirectUri = if ([string]::IsNullOrWhiteSpace($resolvedHubBaseUrl)) { '' } else { "$resolvedHubBaseUrl/auth/callback" }
$externalPostLogoutRedirectUri = if ([string]::IsNullOrWhiteSpace($resolvedHubBaseUrl)) { '' } else { "$resolvedHubBaseUrl/signed-out" }
$stripeWebhookUrl = if ([string]::IsNullOrWhiteSpace($resolvedServiceBaseUrl)) { '' } else { "$resolvedServiceBaseUrl/webhook/stripe" }

$postgresHost = "$PostgresServerName.postgres.database.azure.com"
$encodedPgPassword = UrlEncode $postgresAdminPassword
$databaseUrl = "postgresql://${PostgresAdminUser}:${encodedPgPassword}@${postgresHost}:5432/${PostgresDatabaseName}?sslmode=require"

$tag = if ($SkipBuild) { 'latest' } else { Get-Date -Format 'yyyyMMdd-HHmmss' }
$imageRef = "$AcrName.azurecr.io/${ContainerAppName}:$tag"

if (-not $SkipBuild) {
  Write-Step 'Building Kotomegane image in ACR'
  Invoke-AzCommandWithRetry `
    -FailureMessage 'Kotomegane ACR build failed' `
    -Command {
      az acr build `
        --registry $AcrName `
        --image "${ContainerAppName}:$tag" `
        --image "$ContainerAppName`:latest" `
        --file $dockerFile `
        $repoRoot `
        --no-logs
    }
}

Write-Step 'Reading ACR credentials'
$acrCredsJson = az acr credential show --name $AcrName -o json
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($acrCredsJson)) {
  throw "Failed to read ACR credentials for $AcrName"
}
$acrCreds = $acrCredsJson | ConvertFrom-Json
$acrServer = "$AcrName.azurecr.io"
$acrUsername = $acrCreds.username
$acrPassword = $acrCreds.passwords[0].value

$envPairs = [System.Collections.Generic.List[string]]::new()
$envPairs.Add("HOST=0.0.0.0")
$envPairs.Add("PORT=8083")
$envPairs.Add("PYTHONPATH=/app")
$envPairs.Add("DATABASE_URL=$databaseUrl")
$envPairs.Add("OPENAI_API_KEY=$openaiApiKey")
$envPairs.Add("KOTOMEGANE_ENABLED_PROVIDERS=$enabledProvidersValue")
$envPairs.Add("ENVIRONMENT=$Environment")
$envPairs.Add("CONTAINER_ENV=$Environment")
$envPairs.Add("AUTH_DEV_MODE=$(if ($Environment -eq 'dev') { '1' } else { '0' })")
$envPairs.Add("AUTH_IDENTITY_MODE=entra_external_id")
$envPairs.Add("AUTH_ENFORCE_SERVICES=1")
$envPairs.Add("NICEGUI_STORAGE_SECRET=techie-prod-nicegui-storage-v1")
$envPairs.Add("REQUIRE_ACTIVE_ENTITLEMENT=1")
$envPairs.Add("AUTH_REDIRECT_TO_PLANS_ON_NO_ENTITLEMENT=0")
$envPairs.Add("AUTH_ALLOW_UNSAFE_PAGE_ENTITLEMENT_REDIRECT=0")
$envPairs.Add("TECHIE_SERVICE_KEY=kotomegane")
$envPairs.Add("HUB_LOGIN_URL=$resolvedHubBaseUrl/login")
$envPairs.Add("HUB_BASE_URL=$resolvedHubBaseUrl")
$envPairs.Add("HUB_URL=$resolvedHubBaseUrl")
$envPairs.Add("SERVICE_BASE_URL=$resolvedServiceBaseUrl")
$envPairs.Add("API_BASE_URL=$resolvedServiceBaseUrl")
$envPairs.Add("ENTRA_EXTERNAL_ID_TENANT_NAME=$ExternalTenantName")
$envPairs.Add("ENTRA_EXTERNAL_ID_TENANT_DOMAIN=$ExternalTenantDomain")
$envPairs.Add("ENTRA_EXTERNAL_ID_TENANT_ID=$ExternalTenantId")
$envPairs.Add("ENTRA_EXTERNAL_ID_CLIENT_ID=$ExternalClientId")
$envPairs.Add("ENTRA_EXTERNAL_ID_POLICY=$ExternalIdPolicy")
$envPairs.Add("ENTRA_EXTERNAL_ID_DISCOVERY_URL=$ExternalDiscoveryUrl")
$envPairs.Add("ENTRA_EXTERNAL_ID_LOGIN_METHOD=$ExternalLoginMethod")
$envPairs.Add("AZURE_B2C_TENANT_NAME=$ExternalTenantName")
$envPairs.Add("AZURE_B2C_CLIENT_ID=$ExternalClientId")
$envPairs.Add("AZURE_B2C_POLICY=$ExternalIdPolicy")
$envPairs.Add("SERVICE_LEDGER_MODE=per_service_contract")
$envPairs.Add("CONTRACT_CARDINALITY=multi_contract_per_tenant")

if (-not [string]::IsNullOrWhiteSpace($resolvedIssuerUrl)) {
  $envPairs.Add("ENTRA_EXTERNAL_ID_ISSUER=$resolvedIssuerUrl")
  $envPairs.Add("AZURE_B2C_ISSUER=$resolvedIssuerUrl")
}
if (-not [string]::IsNullOrWhiteSpace($externalRedirectUri)) {
  $envPairs.Add("ENTRA_EXTERNAL_ID_REDIRECT_URI=$externalRedirectUri")
}
if (-not [string]::IsNullOrWhiteSpace($externalPostLogoutRedirectUri)) {
  $envPairs.Add("ENTRA_EXTERNAL_ID_POST_LOGOUT_REDIRECT_URI=$externalPostLogoutRedirectUri")
}
if (-not [string]::IsNullOrWhiteSpace($stripeWebhookUrl)) {
  $envPairs.Add("STRIPE_WEBHOOK_URL=$stripeWebhookUrl")
}
if (-not [string]::IsNullOrWhiteSpace($PlatformAdminEmails)) {
  $envPairs.Add("PLATFORM_ADMIN_EMAILS=$PlatformAdminEmails")
}
if (-not [string]::IsNullOrWhiteSpace($geminiApiKey)) {
  $envPairs.Add("GEMINI_API_KEY=$geminiApiKey")
}
if (-not [string]::IsNullOrWhiteSpace($anthropicApiKey)) {
  $envPairs.Add("ANTHROPIC_API_KEY=$anthropicApiKey")
}

$appExists = Get-ContainerAppExists -ResourceGroup $ResourceGroupName -AppName $ContainerAppName

if ($appExists) {
  Write-Step 'Updating existing Kotomegane Container App'
  Invoke-AzCommandWithRetry `
    -FailureMessage 'Failed to refresh Kotomegane registry credentials' `
    -Command {
      az containerapp registry set `
        --resource-group $ResourceGroupName `
        --name $ContainerAppName `
        --server $acrServer `
        --username $acrUsername `
        --password $acrPassword `
        --output none
    }

  Invoke-AzCommandWithRetry `
    -FailureMessage 'Failed to update Kotomegane Container App' `
    -Command {
      az containerapp update `
        --resource-group $ResourceGroupName `
        --name $ContainerAppName `
        --image $imageRef `
        --set-env-vars $envPairs `
        --output none
    }
}
else {
  Write-Step 'Creating new Kotomegane Container App'
  Invoke-AzCommandWithRetry `
    -FailureMessage 'Failed to create Kotomegane Container App' `
    -Command {
      az containerapp create `
        --resource-group $ResourceGroupName `
        --name $ContainerAppName `
        --environment $ManagedEnvironmentName `
        --image $imageRef `
        --registry-server $acrServer `
        --registry-username $acrUsername `
        --registry-password $acrPassword `
        --ingress external `
        --target-port 8083 `
        --cpu $Cpu `
        --memory $Memory `
        --env-vars $envPairs `
        --output none
    }
}

Write-Step 'Kotomegane deployment summary'
$appJson = az containerapp show --resource-group $ResourceGroupName --name $ContainerAppName -o json
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($appJson)) {
  throw "Failed to read Container App details for $ContainerAppName"
}
$app = $appJson | ConvertFrom-Json
$fqdn = $app.properties.configuration.ingress.fqdn
$latestRevision = $app.properties.latestRevisionName
$runningStatus = $app.properties.runningStatus

Write-Host "Container App                     : $ContainerAppName" -ForegroundColor Green
Write-Host "Image                             : $imageRef" -ForegroundColor Green
Write-Host "FQDN                              : $fqdn" -ForegroundColor Green
Write-Host "URL                               : https://$fqdn" -ForegroundColor Green
Write-Host "Latest Revision                   : $latestRevision" -ForegroundColor Green
Write-Host "Running Status                    : $runningStatus" -ForegroundColor Green
Write-Host "Enabled Providers                 : $enabledProvidersValue" -ForegroundColor Green
Write-Host "Hub URL                           : $resolvedHubBaseUrl" -ForegroundColor Green
Write-Host "Usage Summary API                 : $resolvedServiceBaseUrl/api/usage/summary?service_key=kotomegane" -ForegroundColor Green
Write-Host "Usage Consume API                 : $resolvedServiceBaseUrl/api/usage/consume" -ForegroundColor Green

Write-Host "`nNext checks:" -ForegroundColor Yellow
Write-Host '  1) Open the Kotomegane URL shown above.' -ForegroundColor Yellow
Write-Host '  2) Verify manual execution consumes credits for service key kotomegane.' -ForegroundColor Yellow
Write-Host '  3) Verify batch submit consumes credits once per job with an idempotency key.' -ForegroundColor Yellow
