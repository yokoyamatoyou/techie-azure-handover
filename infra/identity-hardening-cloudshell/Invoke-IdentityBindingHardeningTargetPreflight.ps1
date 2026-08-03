[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExpectedSubscriptionId,
    [Parameter(Mandatory = $true)][string]$ExpectedResourceTenantId,
    [Parameter(Mandatory = $true)][string]$ExpectedExternalDirectoryId,
    [Parameter(Mandatory = $true)][string]$ResourceGroupName,
    [Parameter(Mandatory = $true)][string]$WebAppName,
    [Parameter(Mandatory = $true)][string]$PostgresServerName,
    [Parameter(Mandatory = $true)][string]$DatabaseName,
    [Parameter(Mandatory = $true)][string]$ExpectedContextSha256,
    [Parameter(Mandatory = $true)][string]$ConfirmOperation,
    [string]$DatabaseSettingName = 'DATABASE_URL',
    [int]$DatabasePort = 5432
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$modulePath = Join-Path $PSScriptRoot 'IdentityBindingHardeningTargetPreflight.psm1'
$script:ReviewedModuleSha256 = 'ADEB85E208CFBF8DC2AF086E558FA57C079817BB8F0C0D7EAD351EFDC212C875'
$script:ExpectedOperation = 'READ_ONLY_TECHIE_IDENTITY_HARDENING_TARGET_PREFLIGHT_20260804'
$script:TargetPreflightStage = 'START'

function Throw-TargetPreflightSafeError {
    param([Parameter(Mandatory = $true)][string]$Code)
    throw [System.InvalidOperationException]::new($Code)
}

function Get-TargetPreflightSafeErrorCode {
    param(
        [Parameter(Mandatory = $true)][System.Exception]$Exception,
        [Parameter(Mandatory = $true)][ValidatePattern('^[A-Z0-9_]{1,48}$')][string]$Stage
    )
    $candidate = [string]$Exception.Message
    if ($candidate -match '^[A-Z0-9_]{1,96}$') { return $candidate }
    return "UNEXPECTED_TARGET_PREFLIGHT_FAILURE_$Stage"
}

function Invoke-TargetPreflightAzureCli {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    $prefix = ($Arguments | Select-Object -First ([Math]::Min(4, $Arguments.Count))) -join ' '
    $allowed = (
        $prefix -like 'account show *' -or
        $prefix -like 'webapp show *' -or
        $prefix -like 'webapp config appsettings list*' -or
        $prefix -like 'postgres flexible-server show *'
    )
    if (-not $allowed) {
        Throw-TargetPreflightSafeError -Code 'AZURE_CLI_COMMAND_OUTSIDE_READ_ONLY_ALLOWLIST'
    }
    $captured = @(& $script:AzureCliCommand @Arguments 2>&1)
    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Text = (($captured | ForEach-Object { [string]$_ }) -join "`n").Trim()
    }
}

function Invoke-TargetPreflightAzureJson {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$FailureCode
    )
    $result = Invoke-TargetPreflightAzureCli -Arguments $Arguments
    if ($result.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($result.Text)) {
        Throw-TargetPreflightSafeError -Code $FailureCode
    }
    try { return ($result.Text | ConvertFrom-Json -ErrorAction Stop) }
    catch { Throw-TargetPreflightSafeError -Code $FailureCode }
}

try {
    $script:TargetPreflightStage = 'MODULE_VERIFY'
    if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) {
        Throw-TargetPreflightSafeError -Code 'TARGET_PREFLIGHT_MODULE_MISSING'
    }
    $moduleHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $modulePath).Hash.ToUpperInvariant()
    if ($moduleHash -cne $script:ReviewedModuleSha256) {
        Throw-TargetPreflightSafeError -Code 'TARGET_PREFLIGHT_MODULE_HASH_MISMATCH'
    }
    Import-Module $modulePath -Force -ErrorAction Stop
    $script:TargetPreflightStage = 'INPUT_CONTEXT_VALIDATE'
    $inputArguments = @{
        ExpectedSubscriptionId = $ExpectedSubscriptionId
        ExpectedResourceTenantId = $ExpectedResourceTenantId
        ExpectedExternalDirectoryId = $ExpectedExternalDirectoryId
        ResourceGroupName = $ResourceGroupName
        WebAppName = $WebAppName
        PostgresServerName = $PostgresServerName
        DatabaseName = $DatabaseName
        DatabaseSettingName = $DatabaseSettingName
        DatabasePort = $DatabasePort
    }
    [void](Assert-IdentityBindingHardeningTargetInput @inputArguments)
    if ($ConfirmOperation -cne $script:ExpectedOperation) {
        Throw-TargetPreflightSafeError -Code 'TARGET_PREFLIGHT_OPERATION_CONFIRMATION_MISMATCH'
    }
    $normalizedExpectedContextSha256 = $ExpectedContextSha256.Trim().ToUpperInvariant()
    if ($normalizedExpectedContextSha256 -notmatch '^[0-9A-F]{64}$') {
        Throw-TargetPreflightSafeError -Code 'EXPECTED_CONTEXT_SHA256_INVALID'
    }
    $actualExpectedContextSha256 = Get-HardeningTargetContextSha256 @inputArguments
    if ($actualExpectedContextSha256 -cne $normalizedExpectedContextSha256) {
        Throw-TargetPreflightSafeError -Code 'EXPECTED_CONTEXT_SHA256_MISMATCH'
    }
    $script:TargetPreflightStage = 'AZURE_CLI_RESOLVE'
    $azureCli = Get-Command 'az' -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $azureCli -or [string]::IsNullOrWhiteSpace([string]$azureCli.Source)) {
        Throw-TargetPreflightSafeError -Code 'AZURE_CLI_NOT_FOUND'
    }
    $script:AzureCliCommand = $azureCli.Source
    $script:TargetPreflightStage = 'ACCOUNT_READ'
    $account = Invoke-TargetPreflightAzureJson -FailureCode 'AZURE_ACCOUNT_READ_FAILED' -Arguments @(
        'account', 'show', '--query', '{subscriptionId:id,tenantId:tenantId}', '--output', 'json', '--only-show-errors'
    )
    $script:TargetPreflightStage = 'WEB_APP_READ'
    $webApp = Invoke-TargetPreflightAzureJson -FailureCode 'WEB_APP_READ_FAILED' -Arguments @(
        'webapp', 'show', '--resource-group', $ResourceGroupName, '--name', $WebAppName,
        '--subscription', $ExpectedSubscriptionId, '--query', '{id:id}', '--output', 'json', '--only-show-errors'
    )
    $script:TargetPreflightStage = 'DATABASE_SETTING_READ'
    $databaseSettings = @(Invoke-TargetPreflightAzureJson -FailureCode 'DATABASE_SETTING_READ_FAILED' -Arguments @(
        'webapp', 'config', 'appsettings', 'list', '--resource-group', $ResourceGroupName,
        '--name', $WebAppName, '--subscription', $ExpectedSubscriptionId,
        '--query', "[?name=='$DatabaseSettingName'].{name:name,value:value}", '--output', 'json', '--only-show-errors'
    ))
    $script:TargetPreflightStage = 'POSTGRES_RESOURCE_READ'
    $postgres = Invoke-TargetPreflightAzureJson -FailureCode 'POSTGRES_RESOURCE_READ_FAILED' -Arguments @(
        'postgres', 'flexible-server', 'show', '--resource-group', $ResourceGroupName,
        '--name', $PostgresServerName, '--subscription', $ExpectedSubscriptionId,
        '--query', '{id:id,fullyQualifiedDomainName:fullyQualifiedDomainName}', '--output', 'json', '--only-show-errors'
    )
    $script:TargetPreflightStage = 'EVIDENCE_VALIDATE'
    $evidence = Test-IdentityBindingHardeningTargetEvidence `
        -Account $account `
        -WebApp $webApp `
        -DatabaseSettings $databaseSettings `
        -PostgresServer $postgres `
        -ExpectedSubscriptionId $ExpectedSubscriptionId `
        -ExpectedResourceTenantId $ExpectedResourceTenantId `
        -ExpectedExternalDirectoryId $ExpectedExternalDirectoryId `
        -ResourceGroupName $ResourceGroupName `
        -WebAppName $WebAppName `
        -PostgresServerName $PostgresServerName `
        -DatabaseName $DatabaseName `
        -ExpectedContextSha256 $normalizedExpectedContextSha256 `
        -DatabaseSettingName $DatabaseSettingName `
        -DatabasePort $DatabasePort
    $databaseSettings = $null
    $script:TargetPreflightStage = 'SAFE_OUTPUT'
    $safe = [ordered]@{
        account_match = $evidence.AccountMatch
        directory_roles_separated = $evidence.DirectoryRolesSeparated
        web_app_resource_match = $evidence.WebAppResourceMatch
        postgres_resource_match = $evidence.PostgresResourceMatch
        target_match = $evidence.TargetMatch
        expected_context_match = $evidence.ContextMatch
        confirm_expected_context_sha256 = $evidence.ContextSha256
        confirm_database_target_sha256 = $evidence.ConfirmationSha256
        azure_write_performed = $false
        database_connection_opened = $false
    }
    Write-Output ('IDENTITY_BINDING_HARDENING_TARGET_PREFLIGHT_PASS ' + ($safe | ConvertTo-Json -Compress))
    exit 0
}
catch {
    $safeCode = Get-TargetPreflightSafeErrorCode -Exception $_.Exception -Stage $script:TargetPreflightStage
    [Console]::Error.WriteLine("IDENTITY_BINDING_HARDENING_TARGET_PREFLIGHT_ERROR $safeCode azure_write_performed=false database_connection_opened=false")
    exit 1
}
