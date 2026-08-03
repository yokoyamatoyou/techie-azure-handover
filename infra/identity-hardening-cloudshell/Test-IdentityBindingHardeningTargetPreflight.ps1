[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$modulePath = Join-Path $PSScriptRoot 'IdentityBindingHardeningTargetPreflight.psm1'
$runnerPath = Join-Path $PSScriptRoot 'Invoke-IdentityBindingHardeningTargetPreflight.ps1'
Import-Module $modulePath -Force -ErrorAction Stop

function Assert-Condition {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Code
    )
    if (-not $Condition) { throw $Code }
}

function Assert-ThrowsSafeCode {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Action,
        [Parameter(Mandatory = $true)][string]$ExpectedCode
    )
    try { & $Action }
    catch {
        Assert-Condition -Condition ($_.Exception.Message -eq $ExpectedCode) -Code "UNEXPECTED_ERROR_CODE_$ExpectedCode"
        return
    }
    throw "EXPECTED_ERROR_NOT_THROWN_$ExpectedCode"
}

function Copy-TestObject {
    param([Parameter(Mandatory = $true)][object]$Value)
    return ($Value | ConvertTo-Json -Depth 20 | ConvertFrom-Json)
}

$inputArguments = @{
    ExpectedSubscriptionId = '11111111-1111-4111-8111-111111111111'
    ExpectedResourceTenantId = '22222222-2222-4222-8222-222222222222'
    ExpectedExternalDirectoryId = '33333333-3333-4333-8333-333333333333'
    ResourceGroupName = 'TECHIE-TEST'
    WebAppName = 'techie-web-test'
    PostgresServerName = 'techie-pg-test'
    DatabaseName = 'techie'
    DatabaseSettingName = 'DATABASE_URL'
    DatabasePort = 5432
}
$expectedContextSha256 = Get-HardeningTargetContextSha256 @inputArguments
$scope = "/subscriptions/$($inputArguments.ExpectedSubscriptionId)/resourceGroups/$($inputArguments.ResourceGroupName)"
$account = [pscustomobject]@{
    subscriptionId = $inputArguments.ExpectedSubscriptionId
    tenantId = $inputArguments.ExpectedResourceTenantId
}
$webApp = [pscustomobject]@{
    id = "$scope/providers/Microsoft.Web/sites/$($inputArguments.WebAppName)"
}
$settings = @(
    [pscustomobject]@{
        name = 'DATABASE_URL'
        value = 'postgresql://fixture-user:fixture-credential@db.example.test:5432/techie?sslmode=require'
    }
)
$postgres = [pscustomobject]@{
    id = "$scope/providers/Microsoft.DBforPostgreSQL/flexibleServers/$($inputArguments.PostgresServerName)"
    fullyQualifiedDomainName = 'DB.EXAMPLE.TEST'
}

function Invoke-TestEvidence {
    param(
        [Parameter(Mandatory = $true)][object]$Account,
        [Parameter(Mandatory = $true)][object]$WebApp,
        [Parameter(Mandatory = $true)][object[]]$DatabaseSettings,
        [Parameter(Mandatory = $true)][object]$PostgresServer
    )
    $result = Test-IdentityBindingHardeningTargetEvidence -Account $Account -WebApp $WebApp -DatabaseSettings $DatabaseSettings -PostgresServer $PostgresServer -ExpectedSubscriptionId '11111111-1111-4111-8111-111111111111' -ExpectedResourceTenantId '22222222-2222-4222-8222-222222222222' -ExpectedExternalDirectoryId '33333333-3333-4333-8333-333333333333' -ResourceGroupName 'TECHIE-TEST' -WebAppName 'techie-web-test' -PostgresServerName 'techie-pg-test' -DatabaseName 'techie' -ExpectedContextSha256 $expectedContextSha256 -DatabaseSettingName 'DATABASE_URL' -DatabasePort 5432
    return $result
}

$valid = Invoke-TestEvidence -Account $account -WebApp $webApp -DatabaseSettings $settings -PostgresServer $postgres
Assert-Condition -Condition ($valid.AccountMatch -and $valid.DirectoryRolesSeparated -and $valid.TargetMatch -and $valid.ContextMatch) -Code 'VALID_EVIDENCE_FAILED'
Assert-Condition -Condition ([string]$valid.ConfirmationSha256 -match '^[0-9A-F]{64}$') -Code 'VALID_HASH_FAILED'
Assert-Condition -Condition ([string]$valid.ContextSha256 -ceq $expectedContextSha256) -Code 'VALID_CONTEXT_HASH_FAILED'

$changedContextArguments = @{} + $inputArguments
$changedContextArguments.DatabaseName = 'other'
$changedContextSha256 = Get-HardeningTargetContextSha256 @changedContextArguments
Assert-Condition -Condition ($changedContextSha256 -cne $expectedContextSha256) -Code 'CONTEXT_HASH_CHANGE_NOT_DETECTED'
Assert-ThrowsSafeCode -ExpectedCode 'EXPECTED_CONTEXT_SHA256_MISMATCH' -Action {
    Test-IdentityBindingHardeningTargetEvidence -Account $account -WebApp $webApp -DatabaseSettings $settings -PostgresServer $postgres -ExpectedSubscriptionId $inputArguments.ExpectedSubscriptionId -ExpectedResourceTenantId $inputArguments.ExpectedResourceTenantId -ExpectedExternalDirectoryId $inputArguments.ExpectedExternalDirectoryId -ResourceGroupName $inputArguments.ResourceGroupName -WebAppName $inputArguments.WebAppName -PostgresServerName $inputArguments.PostgresServerName -DatabaseName $inputArguments.DatabaseName -ExpectedContextSha256 ('0' * 64) -DatabaseSettingName $inputArguments.DatabaseSettingName -DatabasePort $inputArguments.DatabasePort
}

$sameDirectory = @{} + $inputArguments
$sameDirectory.ExpectedExternalDirectoryId = $sameDirectory.ExpectedResourceTenantId
Assert-ThrowsSafeCode -ExpectedCode 'DIRECTORY_ROLE_SEPARATION_INVALID' -Action {
    Assert-IdentityBindingHardeningTargetInput @sameDirectory
}

$externalAccount = Copy-TestObject $account
$externalAccount.tenantId = $inputArguments.ExpectedExternalDirectoryId
Assert-ThrowsSafeCode -ExpectedCode 'EXTERNAL_DIRECTORY_SELECTED_FOR_RESOURCE_READ' -Action {
    Invoke-TestEvidence -Account $externalAccount -WebApp $webApp -DatabaseSettings $settings -PostgresServer $postgres
}

$wrongSubscription = Copy-TestObject $account
$wrongSubscription.subscriptionId = '44444444-4444-4444-8444-444444444444'
Assert-ThrowsSafeCode -ExpectedCode 'AZURE_ACCOUNT_CONTEXT_MISMATCH' -Action {
    Invoke-TestEvidence -Account $wrongSubscription -WebApp $webApp -DatabaseSettings $settings -PostgresServer $postgres
}

$wrongWebApp = Copy-TestObject $webApp
$wrongWebApp.id = "$scope/providers/Microsoft.Web/sites/other"
Assert-ThrowsSafeCode -ExpectedCode 'WEB_APP_RESOURCE_MISMATCH' -Action {
    Invoke-TestEvidence -Account $account -WebApp $wrongWebApp -DatabaseSettings $settings -PostgresServer $postgres
}

$wrongPostgres = Copy-TestObject $postgres
$wrongPostgres.id = "$scope/providers/Microsoft.DBforPostgreSQL/flexibleServers/other"
Assert-ThrowsSafeCode -ExpectedCode 'POSTGRES_RESOURCE_MISMATCH' -Action {
    Invoke-TestEvidence -Account $account -WebApp $webApp -DatabaseSettings $settings -PostgresServer $wrongPostgres
}

$duplicateSettings = @($settings[0], (Copy-TestObject $settings[0]))
Assert-ThrowsSafeCode -ExpectedCode 'DATABASE_SETTING_NOT_UNIQUE' -Action {
    Invoke-TestEvidence -Account $account -WebApp $webApp -DatabaseSettings $duplicateSettings -PostgresServer $postgres
}

$wrongHostSettings = @(
    [pscustomobject]@{
        name = 'DATABASE_URL'
        value = 'postgresql://fixture-user:fixture-credential@other.example.test:5432/techie?sslmode=require'
    }
)
Assert-ThrowsSafeCode -ExpectedCode 'DATABASE_TARGET_INDEPENDENT_SOURCE_MISMATCH' -Action {
    Invoke-TestEvidence -Account $account -WebApp $webApp -DatabaseSettings $wrongHostSettings -PostgresServer $postgres
}

$invalidProtocolSettings = @(
    [pscustomobject]@{
        name = 'DATABASE_URL'
        value = 'https://db.example.test/techie'
    }
)
Assert-ThrowsSafeCode -ExpectedCode 'DATABASE_URL_PROTOCOL_INVALID' -Action {
    Invoke-TestEvidence -Account $account -WebApp $webApp -DatabaseSettings $invalidProtocolSettings -PostgresServer $postgres
}

$moduleHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $modulePath).Hash.ToUpperInvariant()
$runnerSource = Get-Content -Raw -Encoding utf8 -LiteralPath $runnerPath
$hashMatch = [regex]::Match($runnerSource, "ReviewedModuleSha256 = '([0-9A-F]{64})'")
Assert-Condition -Condition ($hashMatch.Success -and $hashMatch.Groups[1].Value -ceq $moduleHash) -Code 'REVIEWED_MODULE_HASH_MISMATCH'

function Invoke-RunnerPreAzureGate {
    param(
        [Parameter(Mandatory = $true)][string]$ContextSha256,
        [Parameter(Mandatory = $true)][string]$Operation
    )
    $powershellPath = (Get-Command powershell.exe -CommandType Application -ErrorAction Stop).Source
    $priorErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $captured = @(& $powershellPath -NoProfile -ExecutionPolicy Bypass -File $runnerPath `
            -ExpectedSubscriptionId $inputArguments.ExpectedSubscriptionId `
            -ExpectedResourceTenantId $inputArguments.ExpectedResourceTenantId `
            -ExpectedExternalDirectoryId $inputArguments.ExpectedExternalDirectoryId `
            -ResourceGroupName $inputArguments.ResourceGroupName `
            -WebAppName $inputArguments.WebAppName `
            -PostgresServerName $inputArguments.PostgresServerName `
            -DatabaseName $inputArguments.DatabaseName `
            -ExpectedContextSha256 $ContextSha256 `
            -ConfirmOperation $Operation `
            -DatabaseSettingName $inputArguments.DatabaseSettingName `
            -DatabasePort $inputArguments.DatabasePort 2>&1)
        $nativeExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $priorErrorActionPreference
    }
    return [pscustomobject]@{
        ExitCode = $nativeExitCode
        Text = (($captured | ForEach-Object { [string]$_ }) -join "`n")
    }
}

$wrongContextGate = Invoke-RunnerPreAzureGate -ContextSha256 ('0' * 64) -Operation 'READ_ONLY_TECHIE_IDENTITY_HARDENING_TARGET_PREFLIGHT_20260804'
Assert-Condition -Condition ($wrongContextGate.ExitCode -eq 1 -and $wrongContextGate.Text -match 'EXPECTED_CONTEXT_SHA256_MISMATCH') -Code 'WRAPPER_CONTEXT_GATE_FAILED'
$wrongOperationGate = Invoke-RunnerPreAzureGate -ContextSha256 $expectedContextSha256 -Operation 'WRONG_OPERATION'
Assert-Condition -Condition ($wrongOperationGate.ExitCode -eq 1 -and $wrongOperationGate.Text -match 'TARGET_PREFLIGHT_OPERATION_CONFIRMATION_MISMATCH') -Code 'WRAPPER_OPERATION_GATE_FAILED'
Assert-Condition -Condition (($wrongContextGate.Text + $wrongOperationGate.Text) -notmatch '11111111|22222222|33333333|TECHIE-TEST|techie-web-test|techie-pg-test') -Code 'WRAPPER_PRE_AZURE_FAILURE_LEAKED_INPUT'

$parserFiles = @($modulePath, $runnerPath, $PSCommandPath)
foreach ($file in $parserFiles) {
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($file, [ref]$tokens, [ref]$errors)
    Assert-Condition -Condition ($errors.Count -eq 0) -Code 'POWERSHELL_PARSE_ERROR'
}

$combinedSource = (Get-Content -Raw -Encoding utf8 -LiteralPath $modulePath) + "`n" + $runnerSource
$forbiddenPatterns = @(
    'account\s+set',
    'az\s+login',
    'appsettings\s+(?:set|delete)',
    'webapp\s+(?:create|delete|restart|stop|start)',
    'postgres\s+flexible-server\s+(?:create|update|delete|restart|stop|start)',
    'deployment\s+group\s+create',
    'Invoke-WebRequest',
    'Invoke-RestMethod',
    'NpgsqlConnection',
    'database_connection_opened\s*=\s*\$true'
)
foreach ($pattern in $forbiddenPatterns) {
    Assert-Condition -Condition ($combinedSource -notmatch $pattern) -Code 'MUTATION_OR_CONNECTION_COMMAND_PRESENT'
}
Assert-Condition -Condition ($runnerSource -match "'account', 'show'") -Code 'ACCOUNT_SHOW_COMMAND_MISSING'
Assert-Condition -Condition ($runnerSource -match "'webapp', 'show'") -Code 'WEBAPP_SHOW_COMMAND_MISSING'
Assert-Condition -Condition ($runnerSource -match "'webapp', 'config', 'appsettings', 'list'") -Code 'APPSETTINGS_LIST_COMMAND_MISSING'
Assert-Condition -Condition ($runnerSource -match "'postgres', 'flexible-server', 'show'") -Code 'POSTGRES_SHOW_COMMAND_MISSING'
Assert-Condition -Condition ($runnerSource -match 'ExpectedContextSha256') -Code 'EXPECTED_CONTEXT_HASH_GATE_MISSING'
Assert-Condition -Condition ($runnerSource -match 'READ_ONLY_TECHIE_IDENTITY_HARDENING_TARGET_PREFLIGHT_20260804') -Code 'OPERATION_CONFIRMATION_GATE_MISSING'
foreach ($stage in @(
    'MODULE_VERIFY',
    'INPUT_CONTEXT_VALIDATE',
    'AZURE_CLI_RESOLVE',
    'ACCOUNT_READ',
    'WEB_APP_READ',
    'DATABASE_SETTING_READ',
    'POSTGRES_RESOURCE_READ',
    'EVIDENCE_VALIDATE',
    'SAFE_OUTPUT'
)) {
    Assert-Condition -Condition ($runnerSource -match [regex]::Escape("TargetPreflightStage = '$stage'")) -Code "SAFE_STAGE_MARKER_MISSING_$stage"
}
Assert-Condition -Condition ($runnerSource -match 'UNEXPECTED_TARGET_PREFLIGHT_FAILURE_\$Stage') -Code 'SAFE_STAGE_ERROR_MAPPING_MISSING'
Assert-Condition -Condition ($runnerSource -notmatch 'Write-Output[^\r\n]*(?:databaseSettings|DATABASE_URL|fullyQualifiedDomainName)') -Code 'SENSITIVE_OUTPUT_PATH_PRESENT'

Write-Output 'IDENTITY_BINDING_HARDENING_CLOUDSHELL_PREFLIGHT_TEST_PASS scenarios=13 parser_files=3 mutation_or_connection_commands=0 sensitive_output_paths=0'
