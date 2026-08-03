[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$modulePath = Join-Path $PSScriptRoot 'IdentityShadowFoundationPreflight.psm1'
$runnerPath = Join-Path $PSScriptRoot 'Invoke-IdentityShadowFoundationPreflight.ps1'
Import-Module $modulePath -Force -ErrorAction Stop

function Assert-Condition {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Code
    )
    if (-not $Condition) {
        throw $Code
    }
}

function Assert-ThrowsSafeCode {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Action,
        [Parameter(Mandatory = $true)][string]$ExpectedCode
    )
    try {
        & $Action
    }
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

$arguments = @{
    ExpectedSubscriptionId = '11111111-1111-4111-8111-111111111111'
    ExpectedResourceTenantId = '22222222-2222-4222-8222-222222222222'
    ExpectedExternalDirectoryId = '33333333-3333-4333-8333-333333333333'
    ResourceGroupName = 'TECHIE-TEST'
    ContainerAppsEnvironmentName = 'techie-cae-test'
    AcrName = 'techieregtest'
    KeyVaultName = 'kv-techie-test'
    DatabaseSecretName = 'database-url'
    IdentityName = 'techie-identity-shadow-mi'
    JobName = 'techie-identity-shadow'
}

$expected = Get-IdentityShadowFoundationExpectedResources @arguments
$whatIf = [pscustomobject]@{
    status = 'Succeeded'
    changes = @(
        [pscustomobject]@{
            changeType = 'Create'
            resourceId = $expected.IdentityId
        },
        [pscustomobject]@{
            changeType = 'Create'
            resourceId = "$($expected.AcrId)/providers/Microsoft.Authorization/roleAssignments/44444444-4444-4444-8444-444444444444"
        },
        [pscustomobject]@{
            changeType = 'Create'
            resourceId = "$($expected.DatabaseSecretId)/providers/Microsoft.Authorization/roleAssignments/55555555-5555-4555-8555-555555555555"
        }
    )
}

$validated = Test-IdentityShadowFoundationWhatIf -WhatIfResult $whatIf @arguments
Assert-Condition -Condition ($validated.CreateCount -eq 3) -Code 'VALID_RESULT_CREATE_COUNT_FAILED'
Assert-Condition -Condition ($validated.IdentityCreateCount -eq 1) -Code 'VALID_RESULT_IDENTITY_COUNT_FAILED'
Assert-Condition -Condition ($validated.AcrRoleCreateCount -eq 1) -Code 'VALID_RESULT_ACR_ROLE_COUNT_FAILED'
Assert-Condition -Condition ($validated.KeyVaultSecretRoleCreateCount -eq 1) -Code 'VALID_RESULT_SECRET_ROLE_COUNT_FAILED'

$modify = Copy-TestObject $whatIf
$modify.changes[0].changeType = 'Modify'
Assert-ThrowsSafeCode -ExpectedCode 'WHAT_IF_NON_CREATE_CHANGE_REJECTED' -Action {
    Test-IdentityShadowFoundationWhatIf -WhatIfResult $modify @arguments
}

$delete = Copy-TestObject $whatIf
$delete.changes[1].changeType = 'Delete'
Assert-ThrowsSafeCode -ExpectedCode 'WHAT_IF_NON_CREATE_CHANGE_REJECTED' -Action {
    Test-IdentityShadowFoundationWhatIf -WhatIfResult $delete @arguments
}

$ignore = Copy-TestObject $whatIf
$ignore.changes[2].changeType = 'Ignore'
Assert-ThrowsSafeCode -ExpectedCode 'WHAT_IF_NON_CREATE_CHANGE_REJECTED' -Action {
    Test-IdentityShadowFoundationWhatIf -WhatIfResult $ignore @arguments
}

$unexpected = Copy-TestObject $whatIf
$unexpected.changes[2].resourceId = "/subscriptions/$($arguments.ExpectedSubscriptionId)/resourceGroups/$($arguments.ResourceGroupName)/providers/Microsoft.App/jobs/unexpected"
Assert-ThrowsSafeCode -ExpectedCode 'WHAT_IF_RESOURCE_OUTSIDE_ALLOWLIST' -Action {
    Test-IdentityShadowFoundationWhatIf -WhatIfResult $unexpected @arguments
}

$broadVaultScope = Copy-TestObject $whatIf
$broadVaultScope.changes[2].resourceId = "$($expected.KeyVaultId)/providers/Microsoft.Authorization/roleAssignments/55555555-5555-4555-8555-555555555555"
Assert-ThrowsSafeCode -ExpectedCode 'WHAT_IF_RESOURCE_OUTSIDE_ALLOWLIST' -Action {
    Test-IdentityShadowFoundationWhatIf -WhatIfResult $broadVaultScope @arguments
}

$duplicate = Copy-TestObject $whatIf
$duplicate.changes[2].resourceId = $duplicate.changes[1].resourceId
Assert-ThrowsSafeCode -ExpectedCode 'WHAT_IF_RESOURCE_ID_INVALID_OR_DUPLICATE' -Action {
    Test-IdentityShadowFoundationWhatIf -WhatIfResult $duplicate @arguments
}

$wrongStatus = Copy-TestObject $whatIf
$wrongStatus.status = 'Failed'
Assert-ThrowsSafeCode -ExpectedCode 'WHAT_IF_STATUS_NOT_SUCCEEDED' -Action {
    Test-IdentityShadowFoundationWhatIf -WhatIfResult $wrongStatus @arguments
}

$sameDirectory = @{} + $arguments
$sameDirectory.ExpectedExternalDirectoryId = $sameDirectory.ExpectedResourceTenantId
Assert-ThrowsSafeCode -ExpectedCode 'DIRECTORY_ROLE_SEPARATION_INVALID' -Action {
    Assert-IdentityShadowPreflightInput @sameDirectory
}

$parserFiles = @($modulePath, $runnerPath, $PSCommandPath)
foreach ($file in $parserFiles) {
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($file, [ref]$tokens, [ref]$errors)
    Assert-Condition -Condition ($errors.Count -eq 0) -Code 'POWERSHELL_PARSE_ERROR'
}

$runnerSource = Get-Content -Raw -Encoding utf8 -LiteralPath $runnerPath
$forbiddenPatterns = @(
    'deployment\s+group\s+create',
    'role\s+assignment\s+create',
    'identity\s+create',
    'containerapp\s+job\s+create',
    'containerapp\s+job\s+start',
    'keyvault\s+secret\s+set',
    'acr\s+build',
    'account\s+set',
    'az\s+login'
)
foreach ($pattern in $forbiddenPatterns) {
    Assert-Condition -Condition ($runnerSource -notmatch $pattern) -Code 'MUTATION_COMMAND_PRESENT'
}

$sensitivePatterns = @(
    '(?i)client[_-]?secret\s*[=:]',
    '(?i)stripe[_-]?(secret|key)\s*[=:]',
    '(?i)sk_(live|test)_[A-Za-z0-9]+',
    '(?i)database_url\s*[=:]\s*[^\s$]'
)
$scannedSource = (Get-Content -Raw -Encoding utf8 -LiteralPath $modulePath) + "`n" + $runnerSource + "`n" + (Get-Content -Raw -Encoding utf8 -LiteralPath $PSCommandPath)
foreach ($pattern in $sensitivePatterns) {
    Assert-Condition -Condition ($scannedSource -notmatch $pattern) -Code 'SENSITIVE_LITERAL_PRESENT'
}

Write-Output 'IDENTITY_SHADOW_FOUNDATION_PREFLIGHT_TEST_PASS scenarios=9 parser_files=3 mutation_commands=0 sensitive_literals=0'
