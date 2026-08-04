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

  [string]$ExternalTenantId = '198ccc88-e870-405e-bb50-5aac609976db',

  [string]$ExternalClientId = 'bbef0e62-048c-49b7-850b-e49c229482d1',

  [string]$ExternalAuthority = 'https://kyotokogyotechie.ciamlogin.com/198ccc88-e870-405e-bb50-5aac609976db',

  [ValidateSet('legacy','shadow','enforce')]
  [string]$IdentityResolverMode = 'legacy',

  [switch]$IdentitySchemaVerified,

  [switch]$EnableIdentityAutoProvision,

  [switch]$TrustEntraBindingClaims,

  [switch]$EnableIdentityLinking,

  [switch]$ConfirmIdentityBindingHardeningApplied,

  [string]$IdentityBindingHardeningReceiptSha256 = '',

  [switch]$ConfirmExistingCustomerBootstrapVerified,

  [string]$ExistingCustomerBootstrapReceiptSha256 = '',

  [switch]$EnableNativeEmailBroker,

  [switch]$PublishNativeEmail,

  [switch]$ConfirmNativeEmailLiveVerified,

  [string]$NativeAuthTenantSubdomain = '',

  [string]$PlatformAdminEmails = '',

  [switch]$SkipBuild,

  [switch]$SkipWebApps,

  [switch]$SkipKotomegane
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($IdentityResolverMode -ne 'legacy' -and -not $IdentitySchemaVerified) {
  throw 'Non-legacy identity resolver deployment requires -IdentitySchemaVerified.'
}
if (($EnableIdentityAutoProvision -or $TrustEntraBindingClaims) -and $IdentityResolverMode -ne 'enforce') {
  throw 'Identity auto-provision and Entra binding claims require -IdentityResolverMode enforce.'
}
if ($IdentityResolverMode -ne 'legacy' -and [string]::IsNullOrWhiteSpace($ExternalTenantId)) {
  throw 'ExternalTenantId is required for shadow or enforce identity resolver mode.'
}
if ($EnableIdentityLinking -and $IdentityResolverMode -ne 'enforce') {
  throw 'Identity linking requires -IdentityResolverMode enforce.'
}
if ($EnableIdentityLinking -and -not $IdentitySchemaVerified) {
  throw 'Identity linking requires -IdentitySchemaVerified.'
}
if ($EnableIdentityLinking -and -not $ConfirmIdentityBindingHardeningApplied) {
  throw 'Identity linking requires -ConfirmIdentityBindingHardeningApplied.'
}
if ($EnableIdentityLinking -and -not $ConfirmExistingCustomerBootstrapVerified) {
  throw 'Identity linking requires -ConfirmExistingCustomerBootstrapVerified.'
}
if ($EnableIdentityLinking -and $IdentityBindingHardeningReceiptSha256 -notmatch '^(?!0{64}$)[0-9a-f]{64}$') {
  throw 'Identity linking requires a protected lowercase SHA-256 for the approved binding-hardening apply receipt.'
}
if ($EnableIdentityLinking -and $ExistingCustomerBootstrapReceiptSha256 -notmatch '^(?!0{64}$)[0-9a-f]{64}$') {
  throw 'Identity linking requires a protected lowercase SHA-256 for the approved existing-customer bootstrap receipt.'
}
if ($EnableIdentityLinking -and $IdentityBindingHardeningReceiptSha256 -eq $ExistingCustomerBootstrapReceiptSha256) {
  throw 'Identity-linking hardening and bootstrap receipt SHA-256 values must be independently derived.'
}
if ($EnableIdentityLinking -and ($EnableIdentityAutoProvision -or $TrustEntraBindingClaims)) {
  throw 'Identity linking initial rollout requires auto-provision and binding-claim trust to remain disabled.'
}
if (($ConfirmIdentityBindingHardeningApplied -or $ConfirmExistingCustomerBootstrapVerified) -and -not $EnableIdentityLinking) {
  throw 'Identity-linking confirmation switches are accepted only with -EnableIdentityLinking.'
}
if ((-not [string]::IsNullOrWhiteSpace($IdentityBindingHardeningReceiptSha256) -or -not [string]::IsNullOrWhiteSpace($ExistingCustomerBootstrapReceiptSha256)) -and -not $EnableIdentityLinking) {
  throw 'Identity-linking receipt SHA-256 values are accepted only with -EnableIdentityLinking.'
}
if ($PublishNativeEmail -and (-not $EnableNativeEmailBroker -or -not $ConfirmNativeEmailLiveVerified)) {
  throw 'Publishing Native Email requires both -EnableNativeEmailBroker and -ConfirmNativeEmailLiveVerified.'
}
if ($ConfirmNativeEmailLiveVerified -and -not $PublishNativeEmail) {
  throw '-ConfirmNativeEmailLiveVerified is accepted only with -PublishNativeEmail.'
}
if ($EnableNativeEmailBroker -and $NativeAuthTenantSubdomain -notmatch '^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$') {
  throw 'NativeAuthTenantSubdomain must be an explicit lowercase External ID tenant subdomain.'
}
if ($EnableNativeEmailBroker -and [string]::IsNullOrWhiteSpace($NativeAuthTenantSubdomain)) {
  throw 'NativeAuthTenantSubdomain is required when enabling the Native Email broker.'
}
if (-not $EnableNativeEmailBroker -and -not [string]::IsNullOrWhiteSpace($NativeAuthTenantSubdomain)) {
  throw 'NativeAuthTenantSubdomain must not be supplied while the Native Email broker is disabled.'
}

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

function Assert-NativeAuthSessionKey([string]$Value) {
  try {
    $normalized = $Value.Replace('-', '+').Replace('_', '/')
    $normalized += '=' * ((4 - ($normalized.Length % 4)) % 4)
    $decoded = [Convert]::FromBase64String($normalized)
  }
  catch {
    throw 'EMAIL_NATIVE_AUTH_SESSION_KEY must be base64url encoded.'
  }
  if ($decoded.Length -ne 32) {
    throw 'EMAIL_NATIVE_AUTH_SESSION_KEY must decode to exactly 32 bytes.'
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

function Escape-JsString([string]$Value) {
  return ($Value -replace '\\', '\\' -replace "'", "\'")
}

function Render-HubConfig {
  param(
    [string]$HubDirectory,
    [string]$HubUrl,
    [string]$ApiUrl,
    [string]$EntraAuthority,
    [string]$EntraClientId,
    [string]$EntryPriceId,
    [string]$StandardPriceId,
    [string]$ProPriceId,
    [string]$Addon10CreditPriceId,
    [string]$Addon1CreditPriceId,
    [bool]$NativeEmailEnabled,
    [bool]$NativeEmailLiveVerified,
    [bool]$IdentityLinkingEnabled
  )

  $templatePath = Join-Path $HubDirectory 'config.template.js'
  $targetPath = Join-Path $HubDirectory 'config.js'
  if (-not (Test-Path $templatePath)) {
    throw "Hub config template not found: $templatePath"
  }

  $content = Get-Content $templatePath -Raw -Encoding UTF8
  $replacements = @{
    'https://app.techie.jp' = $HubUrl.TrimEnd('/')
    'https://api.techie.jp' = $ApiUrl.TrimEnd('/')
    '%%ENTRA_AUTHORITY%%' = $EntraAuthority
    '%%ENTRA_CLIENT_ID%%' = $EntraClientId
    '%%STRIPE_ENTRY_PRICE_ID%%' = $EntryPriceId
    '%%STRIPE_STANDARD_PRICE_ID%%' = $StandardPriceId
    '%%STRIPE_PRO_PRICE_ID%%' = $ProPriceId
    '%%STRIPE_ADDON_10_CREDIT_PRICE_ID%%' = $Addon10CreditPriceId
    '%%STRIPE_ADDON_1_CREDIT_PRICE_ID%%' = $Addon1CreditPriceId
    '%%EMAIL_NATIVE_AUTH_ENABLED%%' = $NativeEmailEnabled.ToString().ToLowerInvariant()
    '%%EMAIL_NATIVE_AUTH_LIVE_VERIFIED%%' = $NativeEmailLiveVerified.ToString().ToLowerInvariant()
    '%%IDENTITY_LINKING_ENABLED%%' = $IdentityLinkingEnabled.ToString().ToLowerInvariant()
  }

  foreach ($key in $replacements.Keys) {
    $value = Escape-JsString ([string]$replacements[$key])
    $content = $content.Replace($key, $value)
  }

  Set-Content -Path $targetPath -Value $content -Encoding UTF8
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
$resolvedHubBaseUrl = $HubBaseUrl.TrimEnd('/')
$resolvedServiceBaseUrl = $ServiceBaseUrl.TrimEnd('/')

$envExternalAuthority = [Environment]::GetEnvironmentVariable('ENTRA_AUTHORITY')
$envExternalClientId = [Environment]::GetEnvironmentVariable('ENTRA_EXTERNAL_ID_CLIENT_ID')
if (-not [string]::IsNullOrWhiteSpace($envExternalAuthority)) {
  $ExternalAuthority = $envExternalAuthority
}
if (-not [string]::IsNullOrWhiteSpace($envExternalClientId)) {
  $ExternalClientId = $envExternalClientId
}

$stripeEntryPriceId = [Environment]::GetEnvironmentVariable('STRIPE_ENTRY_PRICE_ID')
$stripeStandardPriceId = [Environment]::GetEnvironmentVariable('STRIPE_STANDARD_PRICE_ID')
$stripeProPriceId = [Environment]::GetEnvironmentVariable('STRIPE_PRO_PRICE_ID')
$stripeAddon10CreditPriceId = [Environment]::GetEnvironmentVariable('STRIPE_ADDON_10_CREDIT_PRICE_ID')
$stripeAddon1CreditPriceId = [Environment]::GetEnvironmentVariable('STRIPE_ADDON_1_CREDIT_PRICE_ID')
if ([string]::IsNullOrWhiteSpace($stripeEntryPriceId)) {
  $stripeEntryPriceId = 'price_1TUeFVCW1iD1TojNuRHRB86E'
}
if ([string]::IsNullOrWhiteSpace($stripeStandardPriceId)) {
  $stripeStandardPriceId = 'price_1TUeJ7CW1iD1TojNteVdjHLm'
}
if ([string]::IsNullOrWhiteSpace($stripeProPriceId)) {
  $stripeProPriceId = 'price_1TUeKwCW1iD1TojNmAdBVyXr'
}
if ([string]::IsNullOrWhiteSpace($stripeAddon10CreditPriceId)) {
  $stripeAddon10CreditPriceId = 'price_1TUeNLCW1iD1TojNYNuY8XUG'
}
if ([string]::IsNullOrWhiteSpace($stripeAddon1CreditPriceId)) {
  $stripeAddon1CreditPriceId = 'price_1TqO5OCW1iD1TojNQotHGizo'
}

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
$nativeAuthSessionKey = ''
if ($EnableNativeEmailBroker) {
  $nativeAuthSessionKey = Read-Secret 'Native Email flow envelope key' 'EMAIL_NATIVE_AUTH_SESSION_KEY'
  Assert-NativeAuthSessionKey $nativeAuthSessionKey
}
foreach ($envName in @(
  'ANTHROPIC_API_KEY',
  'CLAUDE_API_KEY',
  'GEMINI_API_KEY',
  'GOOGLE_API_KEY',
  'STRIPE_ENTRY_PRICE_ID',
  'STRIPE_STANDARD_PRICE_ID',
  'STRIPE_PRO_PRICE_ID',
  'STRIPE_ADDON_10_CREDIT_PRICE_ID',
  'STRIPE_ADDON_1_CREDIT_PRICE_ID',
  'TECHIE_ENTRY_INCLUDED_CREDITS',
  'TECHIE_STANDARD_INCLUDED_CREDITS',
  'TECHIE_PRO_INCLUDED_CREDITS',
  'ENTRA_EXTERNAL_ID_TENANT_NAME',
  'ENTRA_EXTERNAL_ID_TENANT_DOMAIN',
  'ENTRA_EXTERNAL_ID_POLICY',
  'ENTRA_EXTERNAL_ID_DISCOVERY_URL',
  'ENTRA_EXTERNAL_ID_ISSUER'
)) {
  $envValue = [Environment]::GetEnvironmentVariable($envName)
  if (-not [string]::IsNullOrWhiteSpace($envValue)) {
    $optionalRuntimeSettings += "$envName=$envValue"
  }
}

$forcedRuntimeSettings = @(
  "ENVIRONMENT=$Environment",
  "CONTAINER_ENV=$Environment",
  'AUTH_DEV_MODE=0',
  'AUTH_IDENTITY_MODE=entra_external_id',
  "AUTH_IDENTITY_RESOLVER_MODE=$IdentityResolverMode",
  "AUTH_IDENTITY_AUTO_PROVISION=$(if ($EnableIdentityAutoProvision) { '1' } else { '0' })",
  "AUTH_TRUST_ENTRA_BINDING_CLAIMS=$(if ($TrustEntraBindingClaims) { '1' } else { '0' })",
  "IDENTITY_LINKING_ENABLED=$(if ($EnableIdentityLinking) { '1' } else { '0' })",
  'AUTH_ENFORCE_SERVICES=1',
  "HUB_LOGIN_URL=$resolvedHubBaseUrl/login",
  "HUB_BASE_URL=$resolvedHubBaseUrl",
  "HUB_URL=$resolvedHubBaseUrl",
  "KOTOMAKE_URL=$($resolvedHubBaseUrl.TrimEnd('/'))/service/kotomake",
  "KOTOMIGAKI_URL=$($resolvedHubBaseUrl.TrimEnd('/'))/service/kotomigaki",
  "KOTOMEGANE_URL=$($resolvedHubBaseUrl.TrimEnd('/'))/service/kotomegane",
  "SERVICE_BASE_URL=$resolvedServiceBaseUrl",
  "API_BASE_URL=$resolvedServiceBaseUrl",
  "ENTRA_EXTERNAL_ID_CLIENT_ID=$ExternalClientId",
  "ENTRA_EXTERNAL_ID_TENANT_ID=$ExternalTenantId",
  "ENTRA_EXTERNAL_ID_REDIRECT_URI=$resolvedHubBaseUrl/auth/callback",
  "ENTRA_EXTERNAL_ID_POST_LOGOUT_REDIRECT_URI=$resolvedHubBaseUrl/signed-out",
  'NICEGUI_STORAGE_SECRET=techie-prod-nicegui-storage-v1',
  'BLOGGEN_LLM_MODE=openai',
  'NOTECODE_ROUTE_0506_CLIENT_MODE=openai',
  'NOTECODE_UI_BODY_ROUTE=route_0506_structured_blog_ui_v1'
)

$nativeEmailRuntimeSettings = @(
  "ENTRA_CLIENT_ID=$ExternalClientId",
  "EMAIL_NATIVE_AUTH_ENABLED=$(if ($EnableNativeEmailBroker) { '1' } else { '0' })"
)
if ($EnableNativeEmailBroker) {
  $nativeEmailRuntimeSettings += @(
    "ENTRA_NATIVE_TENANT_SUBDOMAIN=$NativeAuthTenantSubdomain",
    "EMAIL_NATIVE_AUTH_SESSION_KEY=$nativeAuthSessionKey"
  )
}

$optionalRuntimeSettings = @($optionalRuntimeSettings + $forcedRuntimeSettings | Select-Object -Unique)

Render-HubConfig `
  -HubDirectory (Join-Path $repoRoot 'techie-hub') `
  -HubUrl $resolvedHubBaseUrl `
  -ApiUrl $resolvedServiceBaseUrl `
  -EntraAuthority $ExternalAuthority `
  -EntraClientId $ExternalClientId `
  -EntryPriceId $stripeEntryPriceId `
  -StandardPriceId $stripeStandardPriceId `
  -ProPriceId $stripeProPriceId `
  -Addon10CreditPriceId $stripeAddon10CreditPriceId `
  -Addon1CreditPriceId $stripeAddon1CreditPriceId `
  -NativeEmailEnabled ([bool]$PublishNativeEmail) `
  -NativeEmailLiveVerified ([bool]$ConfirmNativeEmailLiveVerified) `
  -IdentityLinkingEnabled ([bool]$EnableIdentityLinking)

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
    $envVars = @('HOST=0.0.0.0', 'NICEGUI_HOST=0.0.0.0', "DATABASE_URL=$databaseUrl", 'REQUIRE_ACTIVE_ENTITLEMENT=1', 'AUTH_REDIRECT_TO_PLANS_ON_NO_ENTITLEMENT_REDIRECT=0', 'TECHIE_SERVICE_KEY=kotomake') + $optionalRuntimeSettings + $nativeEmailRuntimeSettings
  }
  elseif ($item.AppName -eq 'kotomigaki') {
    $envVars = @('HOST=0.0.0.0', "DATABASE_URL=$databaseUrl", 'REQUIRE_ACTIVE_ENTITLEMENT=1', 'AUTH_REDIRECT_TO_PLANS_ON_NO_ENTITLEMENT=0', 'AUTH_ALLOW_UNSAFE_PAGE_ENTITLEMENT_REDIRECT=0', 'TECHIE_SERVICE_KEY=kotomigaki') + $optionalRuntimeSettings
  }
  elseif ($item.AppName -eq 'techie-hub') {
    $envVars = @("DATABASE_URL=$databaseUrl", "HUB_BASE_URL=$resolvedHubBaseUrl", "API_BASE_URL=$resolvedServiceBaseUrl")
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
    ) + $commonWebSettings + $nativeEmailRuntimeSettings)
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
