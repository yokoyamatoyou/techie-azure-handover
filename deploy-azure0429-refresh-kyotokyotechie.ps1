[CmdletBinding()]
param(
  [ValidateSet('dev','staging','prod')]
  [string]$Environment = 'prod',

  [string]$Location = 'japanwest',

  [string]$SubscriptionId = '',

  [string]$ServiceBaseUrl = 'https://api.techie.jp',

  [string]$HubBaseUrl = 'https://app.techie.jp',

  [string]$PlatformAdminEmails = '',

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
  -SkipBuild:$SkipBuild `
  -SkipWebApps:$SkipWebApps `
  -SkipKotomegane:$SkipKotomegane

exit $LASTEXITCODE
