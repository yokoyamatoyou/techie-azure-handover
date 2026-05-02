[CmdletBinding()]
param(
  [ValidateSet('dev','staging','prod')]
  [string]$Environment = 'prod',

  [string]$Location = 'japanwest',

  [string]$SubscriptionId = '',

  [string]$ResourceGroupName = 'TECHIE',

  [string]$AcrName = 'techiereg2026',

  [string]$HubWebAppName = 'techie-app',

  [string]$ApiWebAppName = 'techie-api',

  [string]$PostgresServerName = 'techie-pg-server',

  [string]$PostgresDatabaseName = 'techie',

  [string]$PostgresAdminUser = 'techieadmin',

  [string]$ServiceBaseUrl = 'https://api.techie.jp',

  [string]$HubBaseUrl = 'https://app.techie.jp',

  [string]$PlatformAdminEmails = '',

  [switch]$SkipBuild,

  [switch]$SkipWebApps,

  [switch]$SkipKotomegane
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

function Ensure-AzLogin {
  $null = az account show --output none 2>$null
  if ($LASTEXITCODE -ne 0) {
    throw 'Azure CLI is not logged in. Run: az login'
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

function UrlEncode([string]$Value) {
  return [System.Uri]::EscapeDataString($Value)
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

function Build-AcrImage {
  param(
    [string]$Repository,
    [string]$Dockerfile,
    [string]$ContextPath,
    [string]$Tag,
    [string]$Registry
  )

  Write-Step "Building $Repository image in ACR"
  Invoke-AzCommandWithRetry `
    -FailureMessage "ACR build failed for $Repository" `
    -Command {
      az acr build `
        --registry $Registry `
        --image "${Repository}:$Tag" `
        --image "${Repository}:latest" `
        --file $Dockerfile `
        $ContextPath `
        --no-logs
    }
}

function Refresh-RegistryForApp {
  param(
    [string]$AppName,
    [string]$ResourceGroup,
    [string]$RegistryServer,
    [string]$RegistryUsername,
    [string]$RegistryPassword
  )

  Invoke-AzCommandWithRetry `
    -FailureMessage "Failed to refresh registry credentials for $AppName" `
    -Command {
      az containerapp registry set `
        --resource-group $ResourceGroup `
        --name $AppName `
        --server $RegistryServer `
        --username $RegistryUsername `
        --password $RegistryPassword `
        --output none
    }
}

function Update-AppImage {
  param(
    [string]$AppName,
    [string]$ResourceGroup,
    [string]$ImageRef,
    [string[]]$EnvVars = @()
  )

  Write-Step "Updating $AppName image"
  if ($EnvVars.Count -gt 0) {
    Invoke-AzCommandWithRetry `
      -FailureMessage "Failed to update Container App image for $AppName" `
      -Command {
        az containerapp update `
          --resource-group $ResourceGroup `
          --name $AppName `
          --image $ImageRef `
          --set-env-vars $EnvVars `
          --output none
      }
  }
  else {
    Invoke-AzCommandWithRetry `
      -FailureMessage "Failed to update Container App image for $AppName" `
      -Command {
        az containerapp update `
          --resource-group $ResourceGroup `
          --name $AppName `
          --image $ImageRef `
          --output none
      }
  }
}

function Update-WebAppContainer {
  param(
    [string]$WebAppName,
    [string]$ResourceGroup,
    [string]$ImageRef,
    [string]$RegistryServer,
    [string]$RegistryUsername,
    [string]$RegistryPassword,
    [string[]]$Settings
  )

  Write-Step "Updating Web App $WebAppName container"
  Invoke-AzCommandWithRetry `
    -FailureMessage "Failed to update Web App container for $WebAppName" `
    -Command {
      az webapp config container set `
        --resource-group $ResourceGroup `
        --name $WebAppName `
        --container-image-name $ImageRef `
        --container-registry-url "https://$RegistryServer" `
        --container-registry-user $RegistryUsername `
        --container-registry-password $RegistryPassword `
        --enable-app-service-storage false `
        --output none
    }

  Invoke-AzCommandWithRetry `
    -FailureMessage "Failed to update Web App settings for $WebAppName" `
    -Command {
      az webapp config appsettings set `
        --resource-group $ResourceGroup `
        --name $WebAppName `
        --settings $Settings `
        --output none
    }

  Invoke-AzCommandWithRetry `
    -FailureMessage "Failed to restart Web App $WebAppName" `
    -Command {
      az webapp restart `
        --resource-group $ResourceGroup `
        --name $WebAppName `
        --output none
    }
}

function Show-AppSummary {
  param(
    [string]$AppName,
    [string]$ResourceGroup
  )

  $summary = az containerapp show `
    --resource-group $ResourceGroup `
    --name $AppName `
    --query "{name:name,revision:properties.latestRevisionName,status:properties.runningStatus,image:properties.template.containers[0].image,fqdn:properties.configuration.ingress.fqdn}" `
    -o json

  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($summary)) {
    throw "Failed to read Container App summary for $AppName"
  }

  return ($summary | ConvertFrom-Json)
}

function Show-WebAppSummary {
  param(
    [string]$WebAppName,
    [string]$ResourceGroup
  )

  $summary = az webapp show `
    --resource-group $ResourceGroup `
    --name $WebAppName `
    --query "{name:name,state:state,host:defaultHostName}" `
    -o json

  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($summary)) {
    throw "Failed to read Web App summary for $WebAppName"
  }

  return ($summary | ConvertFrom-Json)
}

Write-Step 'Preflight checks'
Require-Command 'az'
Ensure-AzLogin

if (-not [string]::IsNullOrWhiteSpace($SubscriptionId)) {
  az account set --subscription $SubscriptionId
}

$repoRoot = $PSScriptRoot
$tag = if ($SkipBuild) { 'latest' } else { Get-Date -Format 'yyyyMMdd-HHmmss' }
$acrServer = "$AcrName.azurecr.io"
$postgresAdminPassword = Read-Secret 'PostgreSQL admin password' 'POSTGRES_ADMIN_PASSWORD'
$encodedPgPassword = UrlEncode $postgresAdminPassword
$postgresHost = "$PostgresServerName.postgres.database.azure.com"
$databaseUrl = "postgresql://${PostgresAdminUser}:${encodedPgPassword}@${postgresHost}:5432/${PostgresDatabaseName}?sslmode=require"

$optionalRuntimeSettings = @()
$requiredRuntimeSecrets = @(
  @{ Name = 'OPENAI_API_KEY'; Prompt = 'OpenAI API key' },
  @{ Name = 'STRIPE_SECRET_KEY'; Prompt = 'Stripe secret key' },
  @{ Name = 'STRIPE_PUBLISHABLE_KEY'; Prompt = 'Stripe publishable key' },
  @{ Name = 'STRIPE_WEBHOOK_SECRET'; Prompt = 'Stripe webhook signing secret' }
)
foreach ($requiredSecret in $requiredRuntimeSecrets) {
  $secretValue = Read-Secret $requiredSecret.Prompt $requiredSecret.Name
  $optionalRuntimeSettings += "$($requiredSecret.Name)=$secretValue"
}
foreach ($envName in @(
  'ANTHROPIC_API_KEY',
  'CLAUDE_API_KEY',
  'GEMINI_API_KEY',
  'GOOGLE_API_KEY',
  'ENTRA_EXTERNAL_ID_TENANT_NAME',
  'ENTRA_EXTERNAL_ID_TENANT_DOMAIN',
  'ENTRA_EXTERNAL_ID_TENANT_ID',
  'ENTRA_EXTERNAL_ID_CLIENT_ID',
  'ENTRA_EXTERNAL_ID_POLICY',
  'ENTRA_EXTERNAL_ID_DISCOVERY_URL',
  'ENTRA_EXTERNAL_ID_ISSUER',
  'AUTH_IDENTITY_MODE',
  'AUTH_DEV_MODE'
)) {
  $envValue = [Environment]::GetEnvironmentVariable($envName)
  if (-not [string]::IsNullOrWhiteSpace($envValue)) {
    $optionalRuntimeSettings += "$envName=$envValue"
  }
}

$appBuildMatrix = @(
  @{
    AppName = 'kotomake'
    Repository = 'kotomake'
    Dockerfile = (Join-Path $repoRoot 'notecode\Dockerfile')
    ContextPath = $repoRoot
  },
  @{
    AppName = 'kotomigaki'
    Repository = 'kotomigaki'
    Dockerfile = (Join-Path $repoRoot 'aio2-main\Dockerfile')
    ContextPath = $repoRoot
  },
  @{
    AppName = 'techie-hub'
    Repository = 'techie-hub'
    Dockerfile = (Join-Path $repoRoot 'techie-hub\Dockerfile')
    ContextPath = (Join-Path $repoRoot 'techie-hub')
  }
)

foreach ($item in $appBuildMatrix) {
  if (-not (Test-Path $item.Dockerfile)) {
    throw "Dockerfile not found: $($item.Dockerfile)"
  }
  if (-not (Test-Path $item.ContextPath)) {
    throw "Build context not found: $($item.ContextPath)"
  }
}

Write-Step 'Reading ACR credentials'
$acrCredsJson = az acr credential show --name $AcrName -o json
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($acrCredsJson)) {
  throw "Failed to read ACR credentials for $AcrName"
}
$acrCreds = $acrCredsJson | ConvertFrom-Json
$acrUsername = $acrCreds.username
$acrPassword = $acrCreds.passwords[0].value

if (-not $SkipBuild) {
  foreach ($item in $appBuildMatrix) {
    Build-AcrImage `
      -Repository $item.Repository `
      -Dockerfile $item.Dockerfile `
      -ContextPath $item.ContextPath `
      -Tag $tag `
      -Registry $AcrName
  }
}

foreach ($item in $appBuildMatrix) {
  $imageRef = "$acrServer/$($item.Repository):$tag"
  $envVars = @()
  if ($item.AppName -eq 'kotomake') {
    $envVars = @('HOST=0.0.0.0', 'NICEGUI_HOST=0.0.0.0', "DATABASE_URL=$databaseUrl")
  }
  elseif ($item.AppName -eq 'kotomigaki') {
    $envVars = @('HOST=0.0.0.0', "DATABASE_URL=$databaseUrl")
  }
  elseif ($item.AppName -eq 'techie-hub') {
    $envVars = @("DATABASE_URL=$databaseUrl")
  }
  Refresh-RegistryForApp `
    -AppName $item.AppName `
    -ResourceGroup $ResourceGroupName `
    -RegistryServer $acrServer `
    -RegistryUsername $acrUsername `
    -RegistryPassword $acrPassword
  Update-AppImage `
    -AppName $item.AppName `
    -ResourceGroup $ResourceGroupName `
    -ImageRef $imageRef `
    -EnvVars $envVars
}

if (-not $SkipWebApps) {
  $commonWebSettings = @(
    "DATABASE_URL=$databaseUrl",
    "SERVICE_BASE_URL=$ServiceBaseUrl",
    "API_BASE_URL=$ServiceBaseUrl",
    "HUB_BASE_URL=$HubBaseUrl",
    "HUB_URL=$HubBaseUrl",
    "KOTOMAKE_URL=https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io",
    "KOTOMIGAKI_URL=https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io",
    "KOTOMEGANE_URL=https://kotomegane.ashymushroom-021a53c5.japanwest.azurecontainerapps.io",
    "STRIPE_WEBHOOK_URL=$ServiceBaseUrl/webhook/stripe"
  ) + $optionalRuntimeSettings

  Update-WebAppContainer `
    -WebAppName $HubWebAppName `
    -ResourceGroup $ResourceGroupName `
    -ImageRef "$acrServer/techie-hub:$tag" `
    -RegistryServer $acrServer `
    -RegistryUsername $acrUsername `
    -RegistryPassword $acrPassword `
    -Settings (@(
      'WEBSITES_PORT=8090'
    ) + $commonWebSettings)

  Update-WebAppContainer `
    -WebAppName $ApiWebAppName `
    -ResourceGroup $ResourceGroupName `
    -ImageRef "$acrServer/kotomake:$tag" `
    -RegistryServer $acrServer `
    -RegistryUsername $acrUsername `
    -RegistryPassword $acrPassword `
    -Settings (@(
      'WEBSITES_PORT=8080',
      'PORT=8080',
      'HOST=0.0.0.0',
      'NICEGUI_HOST=0.0.0.0'
    ) + $commonWebSettings)
}

if (-not $SkipKotomegane) {
  Write-Step 'Deploying Kotomegane with provider/runtime settings'
  $kotomeganeWrapper = Join-Path $repoRoot 'deploy-kotomegane-kyotokyotechie.ps1'
  if (-not (Test-Path $kotomeganeWrapper)) {
    throw "Kotomegane wrapper not found: $kotomeganeWrapper"
  }

  & $kotomeganeWrapper `
    -Environment $Environment `
    -Location $Location `
    -SubscriptionId $SubscriptionId `
    -ServiceBaseUrl $ServiceBaseUrl `
    -HubBaseUrl $HubBaseUrl `
    -PlatformAdminEmails $PlatformAdminEmails `
    -SkipBuild:$SkipBuild

  if ($LASTEXITCODE -ne 0) {
    throw 'Kotomegane deployment wrapper failed.'
  }
}

Write-Step 'Azure0429 refresh summary'
foreach ($appName in @('techie-hub', 'kotomake', 'kotomigaki', 'kotomegane')) {
  if ($SkipKotomegane -and $appName -eq 'kotomegane') {
    continue
  }
  $app = Show-AppSummary -AppName $appName -ResourceGroup $ResourceGroupName
  Write-Host "App       : $($app.name)" -ForegroundColor Green
  Write-Host "Revision  : $($app.revision)" -ForegroundColor Green
  Write-Host "Status    : $($app.status)" -ForegroundColor Green
  Write-Host "Image     : $($app.image)" -ForegroundColor Green
  if (-not [string]::IsNullOrWhiteSpace($app.fqdn)) {
    Write-Host "URL       : https://$($app.fqdn)" -ForegroundColor Green
  }
  Write-Host ''
}

if (-not $SkipWebApps) {
  Write-Step 'Custom domain Web App summary'
  foreach ($webAppName in @($HubWebAppName, $ApiWebAppName)) {
    $webApp = Show-WebAppSummary -WebAppName $webAppName -ResourceGroup $ResourceGroupName
    Write-Host "Web App   : $($webApp.name)" -ForegroundColor Green
    Write-Host "State     : $($webApp.state)" -ForegroundColor Green
    Write-Host "Host      : https://$($webApp.host)" -ForegroundColor Green
    Write-Host ''
  }
}

Write-Host 'Recommended checks:' -ForegroundColor Yellow
Write-Host '  1) Open HUB, Kotomake, Kotomigaki, and Kotomegane in the browser.' -ForegroundColor Yellow
Write-Host '  2) Verify signup/login and Stripe-connected flows still open correctly.' -ForegroundColor Yellow
Write-Host '  3) Verify credit consumption on Kotomake/Kotomigaki/Kotomegane actions.' -ForegroundColor Yellow
Write-Host '  4) Verify GPT-image-2 generation on Kotomake and batch/manual flow on Kotomegane.' -ForegroundColor Yellow
