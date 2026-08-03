Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:ReviewedFoundationTemplateSha256 = 'EEC7F55C1CBCEBD578E69D6AB7A8220FC64DA36542FF9C8D2E25F4AFF1D9623E'
$script:ReviewedJobTemplateSha256 = 'BDB474F05EAF4C856826351D0C2B1911C51E0B0F95B463DA3644311A213D0267'

function Throw-IdentityShadowSafeError {
    param(
        [Parameter(Mandatory = $true)]
        [ValidatePattern('^[A-Z0-9_]{1,96}$')]
        [string]$Code
    )

    throw [System.InvalidOperationException]::new($Code)
}

function ConvertTo-NormalizedGuid {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value,

        [Parameter(Mandatory = $true)]
        [string]$ErrorCode
    )

    $parsed = [guid]::Empty
    if (-not [guid]::TryParseExact($Value, 'D', [ref]$parsed)) {
        Throw-IdentityShadowSafeError -Code $ErrorCode
    }
    return $parsed.ToString('D').ToLowerInvariant()
}

function Assert-IdentityShadowSafeResourceGroupName {
    param([Parameter(Mandatory = $true)][string]$Value)

    if (
        [string]::IsNullOrWhiteSpace($Value) -or
        $Value.Length -gt 90 -or
        $Value -ne $Value.Trim() -or
        $Value -match '[\x00-\x1f\x7f/\\?#]'
    ) {
        Throw-IdentityShadowSafeError -Code 'RESOURCE_GROUP_NAME_INVALID'
    }
}

function Assert-IdentityShadowPreflightInput {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$ExpectedSubscriptionId,
        [Parameter(Mandatory = $true)][string]$ExpectedResourceTenantId,
        [Parameter(Mandatory = $true)][string]$ExpectedExternalDirectoryId,
        [Parameter(Mandatory = $true)][string]$ResourceGroupName,
        [Parameter(Mandatory = $true)][string]$ContainerAppsEnvironmentName,
        [Parameter(Mandatory = $true)][string]$AcrName,
        [Parameter(Mandatory = $true)][string]$KeyVaultName,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretName,
        [Parameter(Mandatory = $true)][string]$IdentityName,
        [Parameter(Mandatory = $true)][string]$JobName
    )

    $subscription = ConvertTo-NormalizedGuid -Value $ExpectedSubscriptionId -ErrorCode 'EXPECTED_SUBSCRIPTION_ID_INVALID'
    $resourceTenant = ConvertTo-NormalizedGuid -Value $ExpectedResourceTenantId -ErrorCode 'EXPECTED_RESOURCE_TENANT_ID_INVALID'
    $externalTenant = ConvertTo-NormalizedGuid -Value $ExpectedExternalDirectoryId -ErrorCode 'EXPECTED_EXTERNAL_DIRECTORY_ID_INVALID'
    if ($resourceTenant -eq $externalTenant) {
        Throw-IdentityShadowSafeError -Code 'DIRECTORY_ROLE_SEPARATION_INVALID'
    }

    Assert-IdentityShadowSafeResourceGroupName -Value $ResourceGroupName
    if ($ContainerAppsEnvironmentName -notmatch '^[A-Za-z0-9-]{2,64}$') {
        Throw-IdentityShadowSafeError -Code 'CONTAINER_APPS_ENVIRONMENT_NAME_INVALID'
    }
    if ($AcrName -notmatch '^[A-Za-z0-9]{5,50}$') {
        Throw-IdentityShadowSafeError -Code 'ACR_NAME_INVALID'
    }
    if ($KeyVaultName -notmatch '^[A-Za-z0-9-]{3,24}$') {
        Throw-IdentityShadowSafeError -Code 'KEY_VAULT_NAME_INVALID'
    }
    if ($DatabaseSecretName -notmatch '^[A-Za-z0-9-]{1,127}$') {
        Throw-IdentityShadowSafeError -Code 'DATABASE_SECRET_NAME_INVALID'
    }
    if ($IdentityName -notmatch '^[A-Za-z0-9-_]{3,128}$') {
        Throw-IdentityShadowSafeError -Code 'IDENTITY_NAME_INVALID'
    }
    if ($JobName -notmatch '^[A-Za-z0-9-]{2,31}$') {
        Throw-IdentityShadowSafeError -Code 'JOB_NAME_INVALID'
    }

    return [pscustomobject]@{
        SubscriptionId = $subscription
        ResourceTenantId = $resourceTenant
        ExternalDirectoryId = $externalTenant
        ResourceGroupName = $ResourceGroupName
        ContainerAppsEnvironmentName = $ContainerAppsEnvironmentName
        AcrName = $AcrName
        KeyVaultName = $KeyVaultName
        DatabaseSecretName = $DatabaseSecretName
        IdentityName = $IdentityName
        JobName = $JobName
    }
}

function Get-IdentityShadowFoundationExpectedResources {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$ExpectedSubscriptionId,
        [Parameter(Mandatory = $true)][string]$ExpectedResourceTenantId,
        [Parameter(Mandatory = $true)][string]$ExpectedExternalDirectoryId,
        [Parameter(Mandatory = $true)][string]$ResourceGroupName,
        [Parameter(Mandatory = $true)][string]$ContainerAppsEnvironmentName,
        [Parameter(Mandatory = $true)][string]$AcrName,
        [Parameter(Mandatory = $true)][string]$KeyVaultName,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretName,
        [Parameter(Mandatory = $true)][string]$IdentityName,
        [Parameter(Mandatory = $true)][string]$JobName
    )

    $inputState = Assert-IdentityShadowPreflightInput @PSBoundParameters
    $scope = "/subscriptions/$($inputState.SubscriptionId)/resourceGroups/$($inputState.ResourceGroupName)"
    return [pscustomobject]@{
        Input = $inputState
        ContainerAppsEnvironmentId = "$scope/providers/Microsoft.App/managedEnvironments/$($inputState.ContainerAppsEnvironmentName)"
        AcrId = "$scope/providers/Microsoft.ContainerRegistry/registries/$($inputState.AcrName)"
        KeyVaultId = "$scope/providers/Microsoft.KeyVault/vaults/$($inputState.KeyVaultName)"
        DatabaseSecretId = "$scope/providers/Microsoft.KeyVault/vaults/$($inputState.KeyVaultName)/secrets/$($inputState.DatabaseSecretName)"
        IdentityId = "$scope/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$($inputState.IdentityName)"
        JobId = "$scope/providers/Microsoft.App/jobs/$($inputState.JobName)"
    }
}

function Test-IdentityShadowFoundationWhatIf {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object]$WhatIfResult,
        [Parameter(Mandatory = $true)][string]$ExpectedSubscriptionId,
        [Parameter(Mandatory = $true)][string]$ExpectedResourceTenantId,
        [Parameter(Mandatory = $true)][string]$ExpectedExternalDirectoryId,
        [Parameter(Mandatory = $true)][string]$ResourceGroupName,
        [Parameter(Mandatory = $true)][string]$ContainerAppsEnvironmentName,
        [Parameter(Mandatory = $true)][string]$AcrName,
        [Parameter(Mandatory = $true)][string]$KeyVaultName,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretName,
        [Parameter(Mandatory = $true)][string]$IdentityName,
        [Parameter(Mandatory = $true)][string]$JobName
    )

    $resourceArguments = @{
        ExpectedSubscriptionId = $ExpectedSubscriptionId
        ExpectedResourceTenantId = $ExpectedResourceTenantId
        ExpectedExternalDirectoryId = $ExpectedExternalDirectoryId
        ResourceGroupName = $ResourceGroupName
        ContainerAppsEnvironmentName = $ContainerAppsEnvironmentName
        AcrName = $AcrName
        KeyVaultName = $KeyVaultName
        DatabaseSecretName = $DatabaseSecretName
        IdentityName = $IdentityName
        JobName = $JobName
    }
    $expected = Get-IdentityShadowFoundationExpectedResources @resourceArguments

    $rootProperties = @($WhatIfResult.PSObject.Properties.Name)
    if (-not ($rootProperties -contains 'status') -or [string]$WhatIfResult.status -ne 'Succeeded') {
        Throw-IdentityShadowSafeError -Code 'WHAT_IF_STATUS_NOT_SUCCEEDED'
    }
    if (-not ($rootProperties -contains 'changes') -or $null -eq $WhatIfResult.changes) {
        Throw-IdentityShadowSafeError -Code 'WHAT_IF_CHANGES_MISSING'
    }

    $changes = @($WhatIfResult.changes)
    if ($changes.Count -ne 3) {
        Throw-IdentityShadowSafeError -Code 'WHAT_IF_CHANGE_COUNT_UNEXPECTED'
    }

    $identityId = $expected.IdentityId.ToLowerInvariant()
    $acrRolePrefix = ($expected.AcrId + '/providers/Microsoft.Authorization/roleAssignments/').ToLowerInvariant()
    $secretRolePrefix = ($expected.DatabaseSecretId + '/providers/Microsoft.Authorization/roleAssignments/').ToLowerInvariant()
    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $identityCreates = 0
    $acrRoleCreates = 0
    $secretRoleCreates = 0

    foreach ($change in $changes) {
        $properties = @($change.PSObject.Properties.Name)
        if (-not ($properties -contains 'changeType') -or -not ($properties -contains 'resourceId')) {
            Throw-IdentityShadowSafeError -Code 'WHAT_IF_CHANGE_SHAPE_INVALID'
        }
        if ([string]$change.changeType -ne 'Create') {
            Throw-IdentityShadowSafeError -Code 'WHAT_IF_NON_CREATE_CHANGE_REJECTED'
        }

        $resourceId = ([string]$change.resourceId).Trim().TrimEnd('/').ToLowerInvariant()
        if ([string]::IsNullOrWhiteSpace($resourceId) -or -not $seen.Add($resourceId)) {
            Throw-IdentityShadowSafeError -Code 'WHAT_IF_RESOURCE_ID_INVALID_OR_DUPLICATE'
        }

        if ($resourceId -eq $identityId) {
            $identityCreates += 1
            continue
        }

        $roleTail = $null
        if ($resourceId.StartsWith($acrRolePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            $roleTail = $resourceId.Substring($acrRolePrefix.Length)
            $acrRoleCreates += 1
        }
        elseif ($resourceId.StartsWith($secretRolePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            $roleTail = $resourceId.Substring($secretRolePrefix.Length)
            $secretRoleCreates += 1
        }
        else {
            Throw-IdentityShadowSafeError -Code 'WHAT_IF_RESOURCE_OUTSIDE_ALLOWLIST'
        }

        $roleGuid = [guid]::Empty
        if ($roleTail.Contains('/') -or -not [guid]::TryParseExact($roleTail, 'D', [ref]$roleGuid)) {
            Throw-IdentityShadowSafeError -Code 'WHAT_IF_ROLE_ASSIGNMENT_ID_INVALID'
        }
    }

    if ($identityCreates -ne 1 -or $acrRoleCreates -ne 1 -or $secretRoleCreates -ne 1) {
        Throw-IdentityShadowSafeError -Code 'WHAT_IF_REQUIRED_CREATES_MISMATCH'
    }

    return [pscustomobject]@{
        Status = 'pass'
        CreateCount = 3
        IdentityCreateCount = 1
        AcrRoleCreateCount = 1
        KeyVaultSecretRoleCreateCount = 1
    }
}

function Assert-IdentityShadowReviewedTemplateHash {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][ValidateSet('Foundation', 'Job')][string]$TemplateKind,
        [Parameter(Mandatory = $true)][string]$TemplatePath
    )

    if (-not (Test-Path -LiteralPath $TemplatePath -PathType Leaf)) {
        Throw-IdentityShadowSafeError -Code 'REVIEWED_TEMPLATE_MISSING'
    }
    $expectedHash = if ($TemplateKind -eq 'Foundation') {
        $script:ReviewedFoundationTemplateSha256
    }
    else {
        $script:ReviewedJobTemplateSha256
    }
    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $TemplatePath).Hash.ToUpperInvariant()
    if ($actualHash -ne $expectedHash) {
        Throw-IdentityShadowSafeError -Code 'REVIEWED_TEMPLATE_HASH_MISMATCH'
    }
    return [pscustomobject]@{
        Status = 'pass'
        TemplateKind = $TemplateKind
    }
}

function Assert-IdentityShadowJobRuntimeInput {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$ExpectedSubscriptionId,
        [Parameter(Mandatory = $true)][string]$ExpectedResourceTenantId,
        [Parameter(Mandatory = $true)][string]$ExpectedExternalDirectoryId,
        [Parameter(Mandatory = $true)][string]$ResourceGroupName,
        [Parameter(Mandatory = $true)][string]$ContainerAppsEnvironmentName,
        [Parameter(Mandatory = $true)][string]$AcrName,
        [Parameter(Mandatory = $true)][string]$KeyVaultName,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretName,
        [Parameter(Mandatory = $true)][string]$IdentityName,
        [Parameter(Mandatory = $true)][string]$JobName,
        [Parameter(Mandatory = $true)][string]$ImageRepository,
        [Parameter(Mandatory = $true)][string]$ImageDigest,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretVersion,
        [Parameter(Mandatory = $true)][string]$WorkloadProfileName
    )

    $resourceArguments = @{
        ExpectedSubscriptionId = $ExpectedSubscriptionId
        ExpectedResourceTenantId = $ExpectedResourceTenantId
        ExpectedExternalDirectoryId = $ExpectedExternalDirectoryId
        ResourceGroupName = $ResourceGroupName
        ContainerAppsEnvironmentName = $ContainerAppsEnvironmentName
        AcrName = $AcrName
        KeyVaultName = $KeyVaultName
        DatabaseSecretName = $DatabaseSecretName
        IdentityName = $IdentityName
        JobName = $JobName
    }
    $resourceState = Assert-IdentityShadowPreflightInput @resourceArguments
    if (
        [string]::IsNullOrWhiteSpace($ImageRepository) -or
        $ImageRepository.Length -gt 255 -or
        $ImageRepository -cnotmatch '^[a-z0-9]+(?:(?:[._-][a-z0-9]+)|(?:/[a-z0-9]+))*$'
    ) {
        Throw-IdentityShadowSafeError -Code 'IMAGE_REPOSITORY_INVALID'
    }
    if ($ImageDigest -cnotmatch '^sha256:[0-9a-f]{64}$') {
        Throw-IdentityShadowSafeError -Code 'IMAGE_DIGEST_INVALID'
    }
    if ($DatabaseSecretVersion -cnotmatch '^[0-9a-f]{32}$') {
        Throw-IdentityShadowSafeError -Code 'DATABASE_SECRET_VERSION_INVALID'
    }
    if ($WorkloadProfileName -cne 'Consumption') {
        Throw-IdentityShadowSafeError -Code 'WORKLOAD_PROFILE_NOT_ALLOWED'
    }

    return [pscustomobject]@{
        Resource = $resourceState
        ImageRepository = $ImageRepository
        ImageDigest = $ImageDigest
        DatabaseSecretVersion = $DatabaseSecretVersion
        WorkloadProfileName = $WorkloadProfileName
    }
}

function Test-IdentityShadowFoundationRoleAssignments {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object[]]$Assignments,
        [Parameter(Mandatory = $true)][string]$IdentityPrincipalId,
        [Parameter(Mandatory = $true)][string]$ExpectedSubscriptionId,
        [Parameter(Mandatory = $true)][string]$ExpectedResourceTenantId,
        [Parameter(Mandatory = $true)][string]$ExpectedExternalDirectoryId,
        [Parameter(Mandatory = $true)][string]$ResourceGroupName,
        [Parameter(Mandatory = $true)][string]$ContainerAppsEnvironmentName,
        [Parameter(Mandatory = $true)][string]$AcrName,
        [Parameter(Mandatory = $true)][string]$KeyVaultName,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretName,
        [Parameter(Mandatory = $true)][string]$IdentityName,
        [Parameter(Mandatory = $true)][string]$JobName
    )

    $resourceArguments = @{
        ExpectedSubscriptionId = $ExpectedSubscriptionId
        ExpectedResourceTenantId = $ExpectedResourceTenantId
        ExpectedExternalDirectoryId = $ExpectedExternalDirectoryId
        ResourceGroupName = $ResourceGroupName
        ContainerAppsEnvironmentName = $ContainerAppsEnvironmentName
        AcrName = $AcrName
        KeyVaultName = $KeyVaultName
        DatabaseSecretName = $DatabaseSecretName
        IdentityName = $IdentityName
        JobName = $JobName
    }
    $expected = Get-IdentityShadowFoundationExpectedResources @resourceArguments
    $principalId = ConvertTo-NormalizedGuid -Value $IdentityPrincipalId -ErrorCode 'IDENTITY_PRINCIPAL_ID_INVALID'
    $items = @($Assignments)
    if ($items.Count -ne 2) {
        Throw-IdentityShadowSafeError -Code 'FOUNDATION_ROLE_ASSIGNMENT_COUNT_MISMATCH'
    }

    $roleBase = "/subscriptions/$($expected.Input.SubscriptionId)/providers/Microsoft.Authorization/roleDefinitions"
    $acrRoleId = "$roleBase/7f951dda-4ed3-4680-a7ca-43fe172d538d"
    $secretRoleId = "$roleBase/4633458b-17de-408a-b874-0445c86b69e6"
    $acrMatches = 0
    $secretMatches = 0

    foreach ($assignment in $items) {
        $properties = @($assignment.PSObject.Properties.Name)
        foreach ($requiredProperty in @(
            'principalId',
            'principalType',
            'roleDefinitionId',
            'scope',
            'condition',
            'conditionVersion',
            'description',
            'delegatedManagedIdentityResourceId'
        )) {
            if (-not ($properties -contains $requiredProperty)) {
                Throw-IdentityShadowSafeError -Code 'FOUNDATION_ROLE_ASSIGNMENT_SHAPE_INVALID'
            }
        }
        if ([string]$assignment.principalId -ine $principalId) {
            Throw-IdentityShadowSafeError -Code 'FOUNDATION_ROLE_ASSIGNMENT_PRINCIPAL_MISMATCH'
        }
        if ([string]$assignment.principalType -ine 'ServicePrincipal') {
            Throw-IdentityShadowSafeError -Code 'FOUNDATION_ROLE_ASSIGNMENT_PRINCIPAL_TYPE_INVALID'
        }
        if (-not [string]::IsNullOrWhiteSpace([string]$assignment.condition)) {
            Throw-IdentityShadowSafeError -Code 'FOUNDATION_ROLE_ASSIGNMENT_CONDITION_REJECTED'
        }
        if (-not [string]::IsNullOrWhiteSpace([string]$assignment.conditionVersion)) {
            Throw-IdentityShadowSafeError -Code 'FOUNDATION_ROLE_ASSIGNMENT_CONDITION_VERSION_REJECTED'
        }
        if (-not [string]::IsNullOrWhiteSpace([string]$assignment.description)) {
            Throw-IdentityShadowSafeError -Code 'FOUNDATION_ROLE_ASSIGNMENT_DESCRIPTION_REJECTED'
        }
        if (-not [string]::IsNullOrWhiteSpace([string]$assignment.delegatedManagedIdentityResourceId)) {
            Throw-IdentityShadowSafeError -Code 'FOUNDATION_ROLE_ASSIGNMENT_DELEGATION_REJECTED'
        }

        $scope = ([string]$assignment.scope).Trim().TrimEnd('/')
        $roleDefinitionId = ([string]$assignment.roleDefinitionId).Trim().TrimEnd('/')
        if ($scope -ieq $expected.AcrId -and $roleDefinitionId -ieq $acrRoleId) {
            $acrMatches += 1
            continue
        }
        if ($scope -ieq $expected.DatabaseSecretId -and $roleDefinitionId -ieq $secretRoleId) {
            $secretMatches += 1
            continue
        }
        Throw-IdentityShadowSafeError -Code 'FOUNDATION_ROLE_ASSIGNMENT_OUTSIDE_ALLOWLIST'
    }

    if ($acrMatches -ne 1 -or $secretMatches -ne 1) {
        Throw-IdentityShadowSafeError -Code 'FOUNDATION_ROLE_ASSIGNMENT_REQUIRED_PAIR_MISSING'
    }
    return [pscustomobject]@{
        Status = 'pass'
        AssignmentCount = 2
        AcrRoleCount = 1
        KeyVaultSecretRoleCount = 1
    }
}

function Test-IdentityShadowJobWhatIf {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object]$WhatIfResult,
        [Parameter(Mandatory = $true)][string]$ExpectedSubscriptionId,
        [Parameter(Mandatory = $true)][string]$ExpectedResourceTenantId,
        [Parameter(Mandatory = $true)][string]$ExpectedExternalDirectoryId,
        [Parameter(Mandatory = $true)][string]$ResourceGroupName,
        [Parameter(Mandatory = $true)][string]$ContainerAppsEnvironmentName,
        [Parameter(Mandatory = $true)][string]$AcrName,
        [Parameter(Mandatory = $true)][string]$KeyVaultName,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretName,
        [Parameter(Mandatory = $true)][string]$IdentityName,
        [Parameter(Mandatory = $true)][string]$JobName,
        [Parameter(Mandatory = $true)][string]$ImageRepository,
        [Parameter(Mandatory = $true)][string]$ImageDigest,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretVersion,
        [Parameter(Mandatory = $true)][string]$WorkloadProfileName
    )

    $jobArguments = @{} + $PSBoundParameters
    [void]$jobArguments.Remove('WhatIfResult')
    $runtime = Assert-IdentityShadowJobRuntimeInput @jobArguments
    $resourceArguments = @{
        ExpectedSubscriptionId = $ExpectedSubscriptionId
        ExpectedResourceTenantId = $ExpectedResourceTenantId
        ExpectedExternalDirectoryId = $ExpectedExternalDirectoryId
        ResourceGroupName = $ResourceGroupName
        ContainerAppsEnvironmentName = $ContainerAppsEnvironmentName
        AcrName = $AcrName
        KeyVaultName = $KeyVaultName
        DatabaseSecretName = $DatabaseSecretName
        IdentityName = $IdentityName
        JobName = $JobName
    }
    $expected = Get-IdentityShadowFoundationExpectedResources @resourceArguments
    $rootProperties = @($WhatIfResult.PSObject.Properties.Name)
    if (-not ($rootProperties -contains 'status') -or [string]$WhatIfResult.status -ne 'Succeeded') {
        Throw-IdentityShadowSafeError -Code 'JOB_WHAT_IF_STATUS_NOT_SUCCEEDED'
    }
    if (-not ($rootProperties -contains 'changes') -or $null -eq $WhatIfResult.changes) {
        Throw-IdentityShadowSafeError -Code 'JOB_WHAT_IF_CHANGES_MISSING'
    }
    $changes = @($WhatIfResult.changes)
    if ($changes.Count -ne 1) {
        Throw-IdentityShadowSafeError -Code 'JOB_WHAT_IF_CHANGE_COUNT_UNEXPECTED'
    }
    $change = $changes[0]
    $properties = @($change.PSObject.Properties.Name)
    if (-not ($properties -contains 'changeType') -or -not ($properties -contains 'resourceId')) {
        Throw-IdentityShadowSafeError -Code 'JOB_WHAT_IF_CHANGE_SHAPE_INVALID'
    }
    if ([string]$change.changeType -ne 'Create') {
        Throw-IdentityShadowSafeError -Code 'JOB_WHAT_IF_NON_CREATE_CHANGE_REJECTED'
    }
    if (([string]$change.resourceId).Trim().TrimEnd('/') -ine $expected.JobId) {
        Throw-IdentityShadowSafeError -Code 'JOB_WHAT_IF_RESOURCE_OUTSIDE_ALLOWLIST'
    }

    return [pscustomobject]@{
        Status = 'pass'
        CreateCount = 1
        JobCreateCount = 1
        TemplateInputValidated = ($null -ne $runtime)
    }
}

Export-ModuleMember -Function @(
    'Assert-IdentityShadowJobRuntimeInput',
    'Assert-IdentityShadowPreflightInput',
    'Assert-IdentityShadowReviewedTemplateHash',
    'Get-IdentityShadowFoundationExpectedResources',
    'Test-IdentityShadowFoundationRoleAssignments',
    'Test-IdentityShadowFoundationWhatIf',
    'Test-IdentityShadowJobWhatIf'
)
