[CmdletBinding()]
param(
  [ValidateSet('dev','staging','prod')]
  [string]$Environment = 'prod',

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

  [string]$ServiceBaseUrl = 'https://api.techie.jp',

  [string]$HubBaseUrl = 'https://app.techie.jp',

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

function Write-Stage3Step([string]$Message) {
  Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

$phase2Script = Join-Path $PSScriptRoot 'deploy-phase2.ps1'
if (-not (Test-Path $phase2Script)) {
  throw "Base deployment script not found: $phase2Script"
}

Write-Stage3Step 'Running Stage 3 platform deployment'

& $phase2Script `
  -DeploymentLabel 'Stage 3' `
  -Environment $Environment `
  -Location $Location `
  -SubscriptionId $SubscriptionId `
  -ResourceGroupName $ResourceGroupName `
  -ExternalTenantDomain $ExternalTenantDomain `
  -ExternalTenantName $ExternalTenantName `
  -ExternalTenantId $ExternalTenantId `
  -ExternalClientId $ExternalClientId `
  -ExternalDiscoveryUrl $ExternalDiscoveryUrl `
  -ExternalIssuerUrl $ExternalIssuerUrl `
  -ExternalLoginMethod $ExternalLoginMethod `
  -PlatformAdminEmails $PlatformAdminEmails `
  -ServiceBaseUrl $ServiceBaseUrl `
  -HubBaseUrl $HubBaseUrl `
  -ExternalIdPolicy $ExternalIdPolicy `
  -StripeConnectAccountType $StripeConnectAccountType `
  -CouponApprovalMode $CouponApprovalMode `
  -PayoutLedgerMode $PayoutLedgerMode `
  -PayoutExecutionMode $PayoutExecutionMode `
  -PayoutRetryMaxAttempts $PayoutRetryMaxAttempts `
  -SkipDatabaseInit:$SkipDatabaseInit

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$resolvedServiceBaseUrl = $ServiceBaseUrl.TrimEnd('/')
$resolvedHubBaseUrl = $HubBaseUrl.TrimEnd('/')

Write-Stage3Step 'Stage 3 usage API summary'
Write-Host "Usage Summary API                 : $resolvedServiceBaseUrl/api/usage/summary?service_key=<service-key>" -ForegroundColor Green
Write-Host "Usage Consume API                 : $resolvedServiceBaseUrl/api/usage/consume" -ForegroundColor Green
Write-Host "Usage Grant API                   : $resolvedServiceBaseUrl/api/usage/grant" -ForegroundColor Green
Write-Host "Hub Base URL                      : $resolvedHubBaseUrl" -ForegroundColor Green
Write-Host "API Base URL                      : $resolvedServiceBaseUrl" -ForegroundColor Green

Write-Host "`nRecommended Stage 3 service keys:" -ForegroundColor Yellow
Write-Host '  - kotomake' -ForegroundColor Yellow
Write-Host '  - kotomigaki' -ForegroundColor Yellow
Write-Host '  - kotomegane' -ForegroundColor Yellow

Write-Host "`nStage 3 integration reminders:" -ForegroundColor Yellow
Write-Host '  1) Debit credits on each generate/analyze trigger using POST /api/usage/consume.' -ForegroundColor Yellow
Write-Host '  2) Show "insufficient credits" in the UI when the API returns HTTP 402.' -ForegroundColor Yellow
Write-Host '  3) For Kotomegane batch jobs, consume credits at batch submit time with an idempotency key.' -ForegroundColor Yellow
Write-Host '  4) Use GET /api/usage/summary to show remaining credits per service.' -ForegroundColor Yellow
