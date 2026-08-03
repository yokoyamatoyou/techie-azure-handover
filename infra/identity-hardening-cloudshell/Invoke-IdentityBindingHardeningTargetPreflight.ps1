[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExpectedSubscriptionId,
    [Parameter(Mandatory = $true)][string]$ExpectedResourceTenantId,
    [Parameter(Mandatory = $true)][string]$ExpectedExternalDirectoryId,
    [Parameter(Mandatory = $true)][string]$ResourceGroupName,
    [Parameter(Mandatory = $true)][string]$WebAppName,
    [Parameter(Mandatory = $true)][string]$PostgresServerName,
    [Parameter(Mandatory = $true)][string]$DatabaseName,
    [string]$DatabaseSettingName = 'DATABASE_URL',
    [int]$DatabasePort = 5432
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$modulePath = Join-Path $PSScriptRoot 'IdentityBindingHardeningTargetPreflight.psm1'
$script:ReviewedModuleSha256 = '9ABD8271CE8ED481E2196FFFC031D6F8C791A2CE3515741C8AB40FB4EB975C04'

function Throw-TargetPreflightSafeError {
    param([Parameter(Mandatory = $true)][string]$Code)
    throw [System.InvalidOperationException]::new($Code)
}

function Get-TargetPreflightSafeErrorCode {
    param([Parameter(Mandatory = $true)][System.Exception]$Exception)
    $candidate = [string]$Exception.Message
    if ($candidate -match '^[A-Z0-9_]{1,96}$') { return $candidate }
    return 'UNEXPECTED_TARGET_PREFLIGHT_FAILURE'
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
    if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) {
        Throw-TargetPreflightSafeError -Code 'TARGET_PREFLIGHT_MODULE_MISSING'
    }
    $moduleHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $modulePath).Hash.ToUpperInvariant()
    if ($moduleHash -cne $script:ReviewedModuleSha256) {
        Throw-TargetPreflightSafeError -Code 'TARGET_PREFLIGHT_MODULE_HASH_MISMATCH'
    }
    Import-Module $modulePath -Force -ErrorAction Stop
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
    $azureCli = Get-Command 'az' -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $azureCli -or [string]::IsNullOrWhiteSpace([string]$azureCli.Source)) {
        Throw-TargetPreflightSafeError -Code 'AZURE_CLI_NOT_FOUND'
    }
    $script:AzureCliCommand = $azureCli.Source
    $account = Invoke-TargetPreflightAzureJson -FailureCode 'AZURE_ACCOUNT_READ_FAILED' -Arguments @(
        'account', 'show', '--query', '{subscriptionId:id,tenantId:tenantId}', '--output', 'json', '--only-show-errors'
    )
    $webApp = Invoke-TargetPreflightAzureJson -FailureCode 'WEB_APP_READ_FAILED' -Arguments @(
        'webapp', 'show', '--resource-group', $ResourceGroupName, '--name', $WebAppName,
        '--subscription', $ExpectedSubscriptionId, '--query', '{id:id}', '--output', 'json', '--only-show-errors'
    )
    $databaseSettings = @(Invoke-TargetPreflightAzureJson -FailureCode 'DATABASE_SETTING_READ_FAILED' -Arguments @(
        'webapp', 'config', 'appsettings', 'list', '--resource-group', $ResourceGroupName,
        '--name', $WebAppName, '--subscription', $ExpectedSubscriptionId,
        '--query', "[?name=='$DatabaseSettingName'].{name:name,value:value}", '--output', 'json', '--only-show-errors'
    ))
    $postgres = Invoke-TargetPreflightAzureJson -FailureCode 'POSTGRES_RESOURCE_READ_FAILED' -Arguments @(
        'postgres', 'flexible-server', 'show', '--resource-group', $ResourceGroupName,
        '--name', $PostgresServerName, '--subscription', $ExpectedSubscriptionId,
        '--query', '{id:id,fullyQualifiedDomainName:fullyQualifiedDomainName}', '--output', 'json', '--only-show-errors'
    )
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
        -DatabaseSettingName $DatabaseSettingName `
        -DatabasePort $DatabasePort
    $databaseSettings = $null
    $safe = [ordered]@{
        account_match = $evidence.AccountMatch
        directory_roles_separated = $evidence.DirectoryRolesSeparated
        web_app_resource_match = $evidence.WebAppResourceMatch
        postgres_resource_match = $evidence.PostgresResourceMatch
        target_match = $evidence.TargetMatch
        confirm_database_target_sha256 = $evidence.ConfirmationSha256
        azure_write_performed = $false
        database_connection_opened = $false
    }
    Write-Output ('IDENTITY_BINDING_HARDENING_TARGET_PREFLIGHT_PASS ' + ($safe | ConvertTo-Json -Compress))
    exit 0
}
catch {
    $safeCode = Get-TargetPreflightSafeErrorCode -Exception $_.Exception
    [Console]::Error.WriteLine("IDENTITY_BINDING_HARDENING_TARGET_PREFLIGHT_ERROR $safeCode azure_write_performed=false database_connection_opened=false")
    exit 1
}
