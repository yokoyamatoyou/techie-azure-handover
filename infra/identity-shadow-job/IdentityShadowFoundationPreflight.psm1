Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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

Export-ModuleMember -Function @(
    'Assert-IdentityShadowPreflightInput',
    'Get-IdentityShadowFoundationExpectedResources',
    'Test-IdentityShadowFoundationWhatIf'
)
