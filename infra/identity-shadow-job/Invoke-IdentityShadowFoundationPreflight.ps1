[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('ContextOnly', 'FoundationWhatIf', 'JobWhatIf')]
    [string]$Action,

    [Parameter(Mandatory = $true)][string]$ExpectedSubscriptionId,
    [Parameter(Mandatory = $true)][string]$ExpectedResourceTenantId,
    [Parameter(Mandatory = $true)][string]$ExpectedExternalDirectoryId,
    [Parameter(Mandatory = $true)][string]$ResourceGroupName,
    [Parameter(Mandatory = $true)][string]$ContainerAppsEnvironmentName,
    [Parameter(Mandatory = $true)][string]$AcrName,
    [Parameter(Mandatory = $true)][string]$KeyVaultName,
    [string]$DatabaseSecretName = 'database-url',
    [string]$IdentityName = 'techie-identity-shadow-mi',
    [string]$JobName = 'techie-identity-shadow',
    [string]$ImageRepository = 'techie-identity-shadow',
    [string]$ImageDigest,
    [string]$DatabaseSecretVersion,
    [string]$WorkloadProfileName = 'Consumption'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$modulePath = Join-Path $PSScriptRoot 'IdentityShadowFoundationPreflight.psm1'
$foundationPath = Join-Path $PSScriptRoot 'foundation.bicep'
$jobPath = Join-Path $PSScriptRoot 'job.bicep'

function Throw-PreflightSafeError {
    param([Parameter(Mandatory = $true)][string]$Code)
    throw [System.InvalidOperationException]::new($Code)
}

function Get-PreflightSafeErrorCode {
    param([Parameter(Mandatory = $true)][System.Exception]$Exception)
    $candidate = [string]$Exception.Message
    if ($candidate -match '^[A-Z0-9_]{1,96}$') {
        return $candidate
    }
    return 'UNEXPECTED_PREFLIGHT_FAILURE'
}

function Invoke-AzureCliCapture {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    if ($Arguments.Count -lt 2) {
        Throw-PreflightSafeError -Code 'AZURE_CLI_ARGUMENTS_INVALID'
    }
    $commandPrefix = "$($Arguments[0]) $($Arguments[1])"
    $allowedPrefixes = @(
        'account show',
        'resource show',
        'resource list',
        'keyvault secret',
        'role assignment',
        'deployment group'
    )
    if (-not ($allowedPrefixes -contains $commandPrefix)) {
        Throw-PreflightSafeError -Code 'AZURE_CLI_COMMAND_OUTSIDE_READ_ONLY_ALLOWLIST'
    }
    if ($commandPrefix -eq 'keyvault secret' -and ($Arguments.Count -lt 3 -or $Arguments[2] -ne 'list-versions')) {
        Throw-PreflightSafeError -Code 'AZURE_CLI_KEY_VAULT_COMMAND_REJECTED'
    }
    if ($commandPrefix -eq 'role assignment' -and ($Arguments.Count -lt 3 -or $Arguments[2] -ne 'list')) {
        Throw-PreflightSafeError -Code 'AZURE_CLI_ROLE_ASSIGNMENT_COMMAND_REJECTED'
    }
    if ($commandPrefix -eq 'deployment group' -and ($Arguments.Count -lt 3 -or $Arguments[2] -ne 'what-if')) {
        Throw-PreflightSafeError -Code 'AZURE_CLI_DEPLOYMENT_COMMAND_REJECTED'
    }

    $captured = @(& $script:AzureCliCommand @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    return [pscustomobject]@{
        ExitCode = $exitCode
        Text = (($captured | ForEach-Object { [string]$_ }) -join "`n").Trim()
    }
}

function Invoke-AzureCliRequiredText {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$FailureCode
    )
    $result = Invoke-AzureCliCapture -Arguments $Arguments
    if ($result.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($result.Text)) {
        Throw-PreflightSafeError -Code $FailureCode
    }
    return $result.Text
}

function Assert-AzureResourceExists {
    param(
        [Parameter(Mandatory = $true)][string]$ResourceId,
        [Parameter(Mandatory = $true)][string]$SubscriptionId,
        [Parameter(Mandatory = $true)][string]$FailureCode
    )
    $actual = Invoke-AzureCliRequiredText -FailureCode $FailureCode -Arguments @(
        'resource', 'show',
        '--ids', $ResourceId,
        '--subscription', $SubscriptionId,
        '--query', 'id',
        '--output', 'tsv',
        '--only-show-errors'
    )
    if ($actual.Trim().TrimEnd('/') -ine $ResourceId.Trim().TrimEnd('/')) {
        Throw-PreflightSafeError -Code $FailureCode
    }
}

function Get-AzureResourceNameCount {
    param(
        [Parameter(Mandatory = $true)][string]$ResourceGroupName,
        [Parameter(Mandatory = $true)][string]$ResourceType,
        [Parameter(Mandatory = $true)][string]$ResourceName,
        [Parameter(Mandatory = $true)][string]$SubscriptionId,
        [Parameter(Mandatory = $true)][string]$FailureCode
    )
    $query = "[?name=='$ResourceName'] | length(@)"
    $raw = Invoke-AzureCliRequiredText -FailureCode $FailureCode -Arguments @(
        'resource', 'list',
        '--resource-group', $ResourceGroupName,
        '--resource-type', $ResourceType,
        '--subscription', $SubscriptionId,
        '--query', $query,
        '--output', 'tsv',
        '--only-show-errors'
    )
    $count = 0
    if (-not [int]::TryParse($raw.Trim(), [ref]$count)) {
        Throw-PreflightSafeError -Code $FailureCode
    }
    return $count
}

function Test-DatabaseSecretPresent {
    param(
        [Parameter(Mandatory = $true)][string]$KeyVaultName,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretName,
        [Parameter(Mandatory = $true)][string]$SubscriptionId
    )
    $result = Invoke-AzureCliCapture -Arguments @(
        'keyvault', 'secret', 'list-versions',
        '--vault-name', $KeyVaultName,
        '--name', $DatabaseSecretName,
        '--subscription', $SubscriptionId,
        '--query', 'length(@)',
        '--output', 'tsv',
        '--only-show-errors'
    )
    if ($result.ExitCode -eq 0) {
        $versionCount = 0
        if (-not [int]::TryParse($result.Text.Trim(), [ref]$versionCount)) {
            Throw-PreflightSafeError -Code 'DATABASE_SECRET_VERSION_COUNT_INVALID'
        }
        return ($versionCount -gt 0)
    }
    if ($result.Text -match '(?i)SecretNotFound|secret[^\r\n]{0,80}not found') {
        return $false
    }
    Throw-PreflightSafeError -Code 'DATABASE_SECRET_READ_STATE_UNVERIFIED'
}

function Get-IdentityPrincipalId {
    param(
        [Parameter(Mandatory = $true)][string]$IdentityResourceId,
        [Parameter(Mandatory = $true)][string]$SubscriptionId
    )
    $raw = Invoke-AzureCliRequiredText -FailureCode 'IDENTITY_PRINCIPAL_READ_FAILED' -Arguments @(
        'resource', 'show',
        '--ids', $IdentityResourceId,
        '--subscription', $SubscriptionId,
        '--query', '{id:id,principalId:properties.principalId}',
        '--output', 'json',
        '--only-show-errors'
    )
    try {
        $identity = $raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        Throw-PreflightSafeError -Code 'IDENTITY_PRINCIPAL_RESPONSE_INVALID'
    }
    if (
        [string]$identity.id -ine $IdentityResourceId -or
        [string]::IsNullOrWhiteSpace([string]$identity.principalId)
    ) {
        Throw-PreflightSafeError -Code 'IDENTITY_PRINCIPAL_RESPONSE_INVALID'
    }
    return [string]$identity.principalId
}

function Get-IdentityEffectiveRoleAssignments {
    param(
        [Parameter(Mandatory = $true)][string]$IdentityPrincipalId,
        [Parameter(Mandatory = $true)][string]$SubscriptionId
    )
    $raw = Invoke-AzureCliRequiredText -FailureCode 'IDENTITY_ROLE_ASSIGNMENT_READ_FAILED' -Arguments @(
        'role', 'assignment', 'list',
        '--assignee-object-id', $IdentityPrincipalId,
        '--all',
        '--include-inherited',
        '--fill-principal-name', 'false',
        '--fill-role-definition-name', 'false',
        '--subscription', $SubscriptionId,
        '--query', '[].{principalId:principalId,principalType:principalType,roleDefinitionId:roleDefinitionId,scope:scope,condition:condition,conditionVersion:conditionVersion,description:description,delegatedManagedIdentityResourceId:delegatedManagedIdentityResourceId}',
        '--output', 'json',
        '--only-show-errors'
    )
    try {
        $parsed = $raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        Throw-PreflightSafeError -Code 'IDENTITY_ROLE_ASSIGNMENT_RESPONSE_INVALID'
    }
    return @($parsed)
}

function Test-DatabaseSecretVersionEnabled {
    param(
        [Parameter(Mandatory = $true)][string]$KeyVaultName,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretName,
        [Parameter(Mandatory = $true)][string]$DatabaseSecretVersion,
        [Parameter(Mandatory = $true)][string]$SubscriptionId
    )
    $raw = Invoke-AzureCliRequiredText -FailureCode 'DATABASE_SECRET_VERSION_READ_FAILED' -Arguments @(
        'keyvault', 'secret', 'list-versions',
        '--vault-name', $KeyVaultName,
        '--name', $DatabaseSecretName,
        '--subscription', $SubscriptionId,
        '--query', '[].{id:id,enabled:attributes.enabled}',
        '--output', 'json',
        '--only-show-errors'
    )
    try {
        $versions = @($raw | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        Throw-PreflightSafeError -Code 'DATABASE_SECRET_VERSION_RESPONSE_INVALID'
    }
    $expectedId = "https://$KeyVaultName.vault.azure.net/secrets/$DatabaseSecretName/$DatabaseSecretVersion"
    $matches = @($versions | Where-Object { [string]$_.id -ieq $expectedId })
    if ($matches.Count -ne 1) {
        Throw-PreflightSafeError -Code 'DATABASE_SECRET_VERSION_NOT_CONFIRMED'
    }
    if ($matches[0].enabled -ne $true) {
        Throw-PreflightSafeError -Code 'DATABASE_SECRET_VERSION_NOT_ENABLED'
    }
    return $true
}

try {
    if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) {
        Throw-PreflightSafeError -Code 'PREFLIGHT_MODULE_MISSING'
    }
    if (-not (Test-Path -LiteralPath $foundationPath -PathType Leaf)) {
        Throw-PreflightSafeError -Code 'FOUNDATION_TEMPLATE_MISSING'
    }
    if (-not (Test-Path -LiteralPath $jobPath -PathType Leaf)) {
        Throw-PreflightSafeError -Code 'JOB_TEMPLATE_MISSING'
    }
    Import-Module $modulePath -Force -ErrorAction Stop
    [void](Assert-IdentityShadowReviewedTemplateHash -TemplateKind 'Foundation' -TemplatePath $foundationPath)
    [void](Assert-IdentityShadowReviewedTemplateHash -TemplateKind 'Job' -TemplatePath $jobPath)

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

    $azureCli = Get-Command 'az' -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $azureCli -or [string]::IsNullOrWhiteSpace([string]$azureCli.Source)) {
        Throw-PreflightSafeError -Code 'AZURE_CLI_NOT_FOUND'
    }
    $script:AzureCliCommand = $azureCli.Source

    $accountText = Invoke-AzureCliRequiredText -FailureCode 'AZURE_ACCOUNT_READ_FAILED' -Arguments @(
        'account', 'show',
        '--query', '{subscriptionId:id,tenantId:tenantId}',
        '--output', 'json',
        '--only-show-errors'
    )
    try {
        $account = $accountText | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        Throw-PreflightSafeError -Code 'AZURE_ACCOUNT_RESPONSE_INVALID'
    }
    if (
        [string]$account.subscriptionId -ine $expected.Input.SubscriptionId -or
        [string]$account.tenantId -ine $expected.Input.ResourceTenantId
    ) {
        Throw-PreflightSafeError -Code 'AZURE_ACCOUNT_CONTEXT_MISMATCH'
    }
    if ([string]$account.tenantId -ieq $expected.Input.ExternalDirectoryId) {
        Throw-PreflightSafeError -Code 'EXTERNAL_DIRECTORY_SELECTED_FOR_RESOURCE_OPERATION'
    }

    Assert-AzureResourceExists -ResourceId $expected.ContainerAppsEnvironmentId -SubscriptionId $expected.Input.SubscriptionId -FailureCode 'CONTAINER_APPS_ENVIRONMENT_NOT_CONFIRMED'
    Assert-AzureResourceExists -ResourceId $expected.AcrId -SubscriptionId $expected.Input.SubscriptionId -FailureCode 'ACR_NOT_CONFIRMED'
    Assert-AzureResourceExists -ResourceId $expected.KeyVaultId -SubscriptionId $expected.Input.SubscriptionId -FailureCode 'KEY_VAULT_NOT_CONFIRMED'

    $identityCount = Get-AzureResourceNameCount -ResourceGroupName $expected.Input.ResourceGroupName -ResourceType 'Microsoft.ManagedIdentity/userAssignedIdentities' -ResourceName $expected.Input.IdentityName -SubscriptionId $expected.Input.SubscriptionId -FailureCode 'IDENTITY_EXISTENCE_CHECK_FAILED'
    $jobCount = Get-AzureResourceNameCount -ResourceGroupName $expected.Input.ResourceGroupName -ResourceType 'Microsoft.App/jobs' -ResourceName $expected.Input.JobName -SubscriptionId $expected.Input.SubscriptionId -FailureCode 'JOB_EXISTENCE_CHECK_FAILED'
    if ($jobCount -ne 0) {
        Throw-PreflightSafeError -Code 'SHADOW_JOB_ALREADY_EXISTS'
    }

    if ($Action -eq 'JobWhatIf') {
        $jobArguments = @{
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
            ImageRepository = $ImageRepository
            ImageDigest = $ImageDigest
            DatabaseSecretVersion = $DatabaseSecretVersion
            WorkloadProfileName = $WorkloadProfileName
        }
        $runtime = Assert-IdentityShadowJobRuntimeInput @jobArguments
        if ($identityCount -ne 1) {
            Throw-PreflightSafeError -Code 'DEDICATED_IDENTITY_NOT_CONFIRMED'
        }
        $principalId = Get-IdentityPrincipalId -IdentityResourceId $expected.IdentityId -SubscriptionId $expected.Input.SubscriptionId
        $assignments = Get-IdentityEffectiveRoleAssignments -IdentityPrincipalId $principalId -SubscriptionId $expected.Input.SubscriptionId
        $roleState = Test-IdentityShadowFoundationRoleAssignments -Assignments $assignments -IdentityPrincipalId $principalId @resourceArguments
        [void](Test-DatabaseSecretVersionEnabled -KeyVaultName $expected.Input.KeyVaultName -DatabaseSecretName $expected.Input.DatabaseSecretName -DatabaseSecretVersion $runtime.DatabaseSecretVersion -SubscriptionId $expected.Input.SubscriptionId)

        $whatIfText = Invoke-AzureCliRequiredText -FailureCode 'JOB_WHAT_IF_COMMAND_FAILED' -Arguments @(
            'deployment', 'group', 'what-if',
            '--name', 'techie-identity-shadow-job-preflight',
            '--resource-group', $expected.Input.ResourceGroupName,
            '--subscription', $expected.Input.SubscriptionId,
            '--mode', 'Incremental',
            '--template-file', $jobPath,
            '--parameters',
            "containerAppsEnvironmentName=$($expected.Input.ContainerAppsEnvironmentName)",
            "acrName=$($expected.Input.AcrName)",
            "keyVaultName=$($expected.Input.KeyVaultName)",
            "identityName=$($expected.Input.IdentityName)",
            "jobName=$($expected.Input.JobName)",
            "imageRepository=$($runtime.ImageRepository)",
            "imageDigest=$($runtime.ImageDigest)",
            "databaseSecretName=$($expected.Input.DatabaseSecretName)",
            "databaseSecretVersion=$($runtime.DatabaseSecretVersion)",
            "workloadProfileName=$($runtime.WorkloadProfileName)",
            '--result-format', 'ResourceIdOnly',
            '--no-pretty-print',
            '--no-prompt', 'true',
            '--output', 'json',
            '--only-show-errors'
        )
        try {
            $whatIfResult = $whatIfText | ConvertFrom-Json -ErrorAction Stop
        }
        catch {
            Throw-PreflightSafeError -Code 'JOB_WHAT_IF_RESPONSE_INVALID'
        }
        $validated = Test-IdentityShadowJobWhatIf -WhatIfResult $whatIfResult @jobArguments
        $safeSummary = [ordered]@{
            action = 'JobWhatIf'
            account_match = $true
            directory_roles_separated = $true
            dedicated_identity_present = $true
            foundation_role_assignment_count = $roleState.AssignmentCount
            database_secret_version_enabled = $true
            immutable_image_digest = $true
            create_count = $validated.CreateCount
            job_create_count = $validated.JobCreateCount
            non_create_count = 0
            azure_write_performed = $false
            job_execution_started = $false
        }
        Write-Output ("IDENTITY_SHADOW_JOB_WHAT_IF_PASS " + ($safeSummary | ConvertTo-Json -Compress))
        exit 0
    }

    if ($identityCount -ne 0) {
        Throw-PreflightSafeError -Code 'DEDICATED_IDENTITY_ALREADY_EXISTS'
    }

    $databaseSecretPresent = Test-DatabaseSecretPresent -KeyVaultName $expected.Input.KeyVaultName -DatabaseSecretName $expected.Input.DatabaseSecretName -SubscriptionId $expected.Input.SubscriptionId
    if ($Action -eq 'ContextOnly') {
        $safeSummary = [ordered]@{
            action = 'ContextOnly'
            account_match = $true
            directory_roles_separated = $true
            required_resources_present = $true
            dedicated_identity_absent = $true
            shadow_job_absent = $true
            database_secret_present = $databaseSecretPresent
            azure_write_performed = $false
        }
        Write-Output ("IDENTITY_SHADOW_CONTEXT_PASS " + ($safeSummary | ConvertTo-Json -Compress))
        exit 0
    }

    if (-not $databaseSecretPresent) {
        Throw-PreflightSafeError -Code 'DATABASE_SECRET_REQUIRED_FOR_FOUNDATION_WHAT_IF'
    }

    $whatIfText = Invoke-AzureCliRequiredText -FailureCode 'FOUNDATION_WHAT_IF_COMMAND_FAILED' -Arguments @(
        'deployment', 'group', 'what-if',
        '--name', 'techie-identity-shadow-foundation-preflight',
        '--resource-group', $expected.Input.ResourceGroupName,
        '--subscription', $expected.Input.SubscriptionId,
        '--mode', 'Incremental',
        '--template-file', $foundationPath,
        '--parameters',
        "acrName=$($expected.Input.AcrName)",
        "keyVaultName=$($expected.Input.KeyVaultName)",
        "databaseSecretName=$($expected.Input.DatabaseSecretName)",
        "identityName=$($expected.Input.IdentityName)",
        '--result-format', 'ResourceIdOnly',
        '--no-pretty-print',
        '--no-prompt', 'true',
        '--output', 'json',
        '--only-show-errors'
    )
    try {
        $whatIfResult = $whatIfText | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        Throw-PreflightSafeError -Code 'FOUNDATION_WHAT_IF_RESPONSE_INVALID'
    }
    $validated = Test-IdentityShadowFoundationWhatIf -WhatIfResult $whatIfResult @resourceArguments
    $safeSummary = [ordered]@{
        action = 'FoundationWhatIf'
        account_match = $true
        directory_roles_separated = $true
        database_secret_present = $true
        create_count = $validated.CreateCount
        identity_create_count = $validated.IdentityCreateCount
        acr_role_create_count = $validated.AcrRoleCreateCount
        key_vault_secret_role_create_count = $validated.KeyVaultSecretRoleCreateCount
        non_create_count = 0
        azure_write_performed = $false
    }
    Write-Output ("IDENTITY_SHADOW_FOUNDATION_WHAT_IF_PASS " + ($safeSummary | ConvertTo-Json -Compress))
    exit 0
}
catch {
    $safeCode = Get-PreflightSafeErrorCode -Exception $_.Exception
    [Console]::Error.WriteLine("IDENTITY_SHADOW_PREFLIGHT_ERROR $safeCode azure_write_performed=false")
    exit 1
}
