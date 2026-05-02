[CmdletBinding()]
param(
  [ValidateSet('dev','staging','prod')]
  [string]$Environment = 'prod',

  [string]$Location = 'japanwest',

  [string]$SubscriptionId = '',

  [string]$ServiceBaseUrl = 'https://api.techie.jp',

  [string]$HubBaseUrl = 'https://app.techie.jp',

  [string]$PlatformAdminEmails = '',

  [switch]$SkipDatabaseInit
)

$scriptPath = Join-Path $PSScriptRoot 'deploy-stage3.ps1'

& $scriptPath `
  -Environment $Environment `
  -Location $Location `
  -SubscriptionId $SubscriptionId `
  -ExternalTenantDomain 'kyotokyotechie.onmicrosoft.com' `
  -ExternalTenantName 'kyotokyotechie' `
  -ExternalTenantId '198ccc88-e870-405e-bb50-5aac609976db' `
  -ExternalClientId 'bbef0e62-048c-49b7-850b-e49c229482d1' `
  -ExternalDiscoveryUrl 'https://kyotokogyotechie.ciamlogin.com/198ccc88-e870-405e-bb50-5aac609976db/v2.0/.well-known/openid-configuration' `
  -ExternalLoginMethod 'email_otp' `
  -PlatformAdminEmails $PlatformAdminEmails `
  -ServiceBaseUrl $ServiceBaseUrl `
  -HubBaseUrl $HubBaseUrl `
  -SkipDatabaseInit:$SkipDatabaseInit

exit $LASTEXITCODE
