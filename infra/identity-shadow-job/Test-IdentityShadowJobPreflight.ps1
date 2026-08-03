[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$modulePath = Join-Path $PSScriptRoot 'IdentityShadowFoundationPreflight.psm1'
$runnerPath = Join-Path $PSScriptRoot 'Invoke-IdentityShadowFoundationPreflight.ps1'
$foundationPath = Join-Path $PSScriptRoot 'foundation.bicep'
$jobPath = Join-Path $PSScriptRoot 'job.bicep'
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

$resourceArguments = @{
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
$jobArguments = @{} + $resourceArguments
$jobArguments.ImageRepository = 'techie-identity-shadow'
$jobArguments.ImageDigest = 'sha256:' + ('a' * 64)
$jobArguments.DatabaseSecretVersion = 'b' * 32
$jobArguments.WorkloadProfileName = 'Consumption'

[void](Assert-IdentityShadowReviewedTemplateHash -TemplateKind 'Foundation' -TemplatePath $foundationPath)
[void](Assert-IdentityShadowReviewedTemplateHash -TemplateKind 'Job' -TemplatePath $jobPath)
$runtime = Assert-IdentityShadowJobRuntimeInput @jobArguments
Assert-Condition -Condition ($runtime.ImageDigest -eq $jobArguments.ImageDigest) -Code 'VALID_RUNTIME_DIGEST_FAILED'

$invalidDigest = @{} + $jobArguments
$invalidDigest.ImageDigest = 'latest'
Assert-ThrowsSafeCode -ExpectedCode 'IMAGE_DIGEST_INVALID' -Action {
    Assert-IdentityShadowJobRuntimeInput @invalidDigest
}

$uppercaseDigest = @{} + $jobArguments
$uppercaseDigest.ImageDigest = 'sha256:' + ('A' * 64)
Assert-ThrowsSafeCode -ExpectedCode 'IMAGE_DIGEST_INVALID' -Action {
    Assert-IdentityShadowJobRuntimeInput @uppercaseDigest
}

$invalidVersion = @{} + $jobArguments
$invalidVersion.DatabaseSecretVersion = 'not-a-version'
Assert-ThrowsSafeCode -ExpectedCode 'DATABASE_SECRET_VERSION_INVALID' -Action {
    Assert-IdentityShadowJobRuntimeInput @invalidVersion
}

$invalidProfile = @{} + $jobArguments
$invalidProfile.WorkloadProfileName = 'Dedicated'
Assert-ThrowsSafeCode -ExpectedCode 'WORKLOAD_PROFILE_NOT_ALLOWED' -Action {
    Assert-IdentityShadowJobRuntimeInput @invalidProfile
}

$invalidRepository = @{} + $jobArguments
$invalidRepository.ImageRepository = '../unsafe'
Assert-ThrowsSafeCode -ExpectedCode 'IMAGE_REPOSITORY_INVALID' -Action {
    Assert-IdentityShadowJobRuntimeInput @invalidRepository
}

$expected = Get-IdentityShadowFoundationExpectedResources @resourceArguments
$principalId = '66666666-6666-4666-8666-666666666666'
$roleBase = "/subscriptions/$($resourceArguments.ExpectedSubscriptionId)/providers/Microsoft.Authorization/roleDefinitions"
$assignments = @(
    [pscustomobject]@{
        principalId = $principalId
        principalType = 'ServicePrincipal'
        roleDefinitionId = "$roleBase/7f951dda-4ed3-4680-a7ca-43fe172d538d"
        scope = $expected.AcrId
        condition = $null
        conditionVersion = $null
        description = $null
        delegatedManagedIdentityResourceId = $null
    },
    [pscustomobject]@{
        principalId = $principalId
        principalType = 'ServicePrincipal'
        roleDefinitionId = "$roleBase/4633458b-17de-408a-b874-0445c86b69e6"
        scope = $expected.DatabaseSecretId
        condition = $null
        conditionVersion = $null
        description = $null
        delegatedManagedIdentityResourceId = $null
    }
)
$roles = Test-IdentityShadowFoundationRoleAssignments -Assignments $assignments -IdentityPrincipalId $principalId @resourceArguments
Assert-Condition -Condition ($roles.AssignmentCount -eq 2) -Code 'VALID_ROLE_ASSIGNMENT_COUNT_FAILED'

$extraAssignment = @($assignments[0], $assignments[1], $assignments[0])
Assert-ThrowsSafeCode -ExpectedCode 'FOUNDATION_ROLE_ASSIGNMENT_COUNT_MISMATCH' -Action {
    Test-IdentityShadowFoundationRoleAssignments -Assignments $extraAssignment -IdentityPrincipalId $principalId @resourceArguments
}

$broadScope = Copy-TestObject $assignments
$broadScope[1].scope = $expected.KeyVaultId
Assert-ThrowsSafeCode -ExpectedCode 'FOUNDATION_ROLE_ASSIGNMENT_OUTSIDE_ALLOWLIST' -Action {
    Test-IdentityShadowFoundationRoleAssignments -Assignments $broadScope -IdentityPrincipalId $principalId @resourceArguments
}

$wrongRole = Copy-TestObject $assignments
$wrongRole[0].roleDefinitionId = "$roleBase/00000000-0000-4000-8000-000000000000"
Assert-ThrowsSafeCode -ExpectedCode 'FOUNDATION_ROLE_ASSIGNMENT_OUTSIDE_ALLOWLIST' -Action {
    Test-IdentityShadowFoundationRoleAssignments -Assignments $wrongRole -IdentityPrincipalId $principalId @resourceArguments
}

$conditionalRole = Copy-TestObject $assignments
$conditionalRole[0].condition = 'unexpected-condition'
Assert-ThrowsSafeCode -ExpectedCode 'FOUNDATION_ROLE_ASSIGNMENT_CONDITION_REJECTED' -Action {
    Test-IdentityShadowFoundationRoleAssignments -Assignments $conditionalRole -IdentityPrincipalId $principalId @resourceArguments
}

$conditionVersionRole = Copy-TestObject $assignments
$conditionVersionRole[0].conditionVersion = '2.0'
Assert-ThrowsSafeCode -ExpectedCode 'FOUNDATION_ROLE_ASSIGNMENT_CONDITION_VERSION_REJECTED' -Action {
    Test-IdentityShadowFoundationRoleAssignments -Assignments $conditionVersionRole -IdentityPrincipalId $principalId @resourceArguments
}

$describedRole = Copy-TestObject $assignments
$describedRole[0].description = 'unexpected-description'
Assert-ThrowsSafeCode -ExpectedCode 'FOUNDATION_ROLE_ASSIGNMENT_DESCRIPTION_REJECTED' -Action {
    Test-IdentityShadowFoundationRoleAssignments -Assignments $describedRole -IdentityPrincipalId $principalId @resourceArguments
}

$wrongPrincipal = Copy-TestObject $assignments
$wrongPrincipal[1].principalId = '77777777-7777-4777-8777-777777777777'
Assert-ThrowsSafeCode -ExpectedCode 'FOUNDATION_ROLE_ASSIGNMENT_PRINCIPAL_MISMATCH' -Action {
    Test-IdentityShadowFoundationRoleAssignments -Assignments $wrongPrincipal -IdentityPrincipalId $principalId @resourceArguments
}

$whatIf = [pscustomobject]@{
    status = 'Succeeded'
    changes = @(
        [pscustomobject]@{
            changeType = 'Create'
            resourceId = $expected.JobId
        }
    )
}
$validated = Test-IdentityShadowJobWhatIf -WhatIfResult $whatIf @jobArguments
Assert-Condition -Condition ($validated.JobCreateCount -eq 1) -Code 'VALID_JOB_CREATE_COUNT_FAILED'

$modify = Copy-TestObject $whatIf
$modify.changes[0].changeType = 'Modify'
Assert-ThrowsSafeCode -ExpectedCode 'JOB_WHAT_IF_NON_CREATE_CHANGE_REJECTED' -Action {
    Test-IdentityShadowJobWhatIf -WhatIfResult $modify @jobArguments
}

$extraChange = Copy-TestObject $whatIf
$extraChange.changes = @($extraChange.changes[0], [pscustomobject]@{ changeType = 'Create'; resourceId = $expected.IdentityId })
Assert-ThrowsSafeCode -ExpectedCode 'JOB_WHAT_IF_CHANGE_COUNT_UNEXPECTED' -Action {
    Test-IdentityShadowJobWhatIf -WhatIfResult $extraChange @jobArguments
}

$wrongResource = Copy-TestObject $whatIf
$wrongResource.changes[0].resourceId = $expected.IdentityId
Assert-ThrowsSafeCode -ExpectedCode 'JOB_WHAT_IF_RESOURCE_OUTSIDE_ALLOWLIST' -Action {
    Test-IdentityShadowJobWhatIf -WhatIfResult $wrongResource @jobArguments
}

$failedStatus = Copy-TestObject $whatIf
$failedStatus.status = 'Failed'
Assert-ThrowsSafeCode -ExpectedCode 'JOB_WHAT_IF_STATUS_NOT_SUCCEEDED' -Action {
    Test-IdentityShadowJobWhatIf -WhatIfResult $failedStatus @jobArguments
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
    'keyvault\s+secret\s+(show|set|delete|purge|recover|restore)',
    'acr\s+build',
    'account\s+set',
    'az\s+login'
)
foreach ($pattern in $forbiddenPatterns) {
    Assert-Condition -Condition ($runnerSource -notmatch $pattern) -Code 'MUTATION_OR_VALUE_READ_COMMAND_PRESENT'
}
Assert-Condition -Condition ($runnerSource -match "'keyvault', 'secret', 'list-versions'") -Code 'SECRET_METADATA_ONLY_COMMAND_MISSING'

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

Write-Output 'IDENTITY_SHADOW_JOB_PREFLIGHT_TEST_PASS scenarios=19 parser_files=3 mutation_or_value_read_commands=0 sensitive_literals=0'
