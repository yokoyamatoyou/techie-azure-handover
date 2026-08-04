[CmdletBinding()]
param(
  [ValidateSet('dev','staging','prod')]
  [string]$Environment = 'prod',

  [string]$Location = 'japanwest',

  [string]$SubscriptionId = '',

  [string]$ServiceBaseUrl = 'https://api.techie.jp',

  [string]$HubBaseUrl = 'https://app.techie.jp',

  [string]$PlatformAdminEmails = '',

  [ValidateSet('legacy','shadow','enforce')]
  [string]$IdentityResolverMode = 'legacy',

  [switch]$IdentitySchemaVerified,

  [switch]$EnableIdentityLinking,

  [switch]$ConfirmIdentityBindingHardeningApplied,

  [string]$IdentityBindingHardeningReceiptSha256 = '',

  [switch]$ConfirmExistingCustomerBootstrapVerified,

  [string]$ExistingCustomerBootstrapReceiptSha256 = '',

  [switch]$EnableNativeEmailBroker,

  [switch]$PublishNativeEmail,

  [switch]$ConfirmNativeEmailLiveVerified,

  [string]$NativeAuthTenantSubdomain = '',

  [switch]$SkipBuild,

  [switch]$SkipWebApps,

  [switch]$SkipKotomegane
)

$scriptPath = Join-Path $PSScriptRoot 'deploy-azure0429-refresh.ps1'

& $scriptPath `
  -Environment $Environment `
  -Location $Location `
  -SubscriptionId $SubscriptionId `
  -ResourceGroupName 'TECHIE' `
  -AcrName 'techiereg2026' `
  -ServiceBaseUrl $ServiceBaseUrl `
  -HubBaseUrl $HubBaseUrl `
  -PlatformAdminEmails $PlatformAdminEmails `
  -IdentityResolverMode $IdentityResolverMode `
  -IdentitySchemaVerified:$IdentitySchemaVerified `
  -EnableIdentityLinking:$EnableIdentityLinking `
  -ConfirmIdentityBindingHardeningApplied:$ConfirmIdentityBindingHardeningApplied `
  -IdentityBindingHardeningReceiptSha256 $IdentityBindingHardeningReceiptSha256 `
  -ConfirmExistingCustomerBootstrapVerified:$ConfirmExistingCustomerBootstrapVerified `
  -ExistingCustomerBootstrapReceiptSha256 $ExistingCustomerBootstrapReceiptSha256 `
  -EnableNativeEmailBroker:$EnableNativeEmailBroker `
  -PublishNativeEmail:$PublishNativeEmail `
  -ConfirmNativeEmailLiveVerified:$ConfirmNativeEmailLiveVerified `
  -NativeAuthTenantSubdomain $NativeAuthTenantSubdomain `
  -SkipBuild:$SkipBuild `
  -SkipWebApps:$SkipWebApps `
  -SkipKotomegane:$SkipKotomegane

exit $LASTEXITCODE
