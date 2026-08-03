Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Throw-HardeningTargetSafeError {
    param(
        [Parameter(Mandatory = $true)]
        [ValidatePattern('^[A-Z0-9_]{1,96}$')]
        [string]$Code
    )
    throw [System.InvalidOperationException]::new($Code)
}

function ConvertTo-HardeningTargetGuid {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$ErrorCode
    )
    $parsed = [guid]::Empty
    if (-not [guid]::TryParseExact($Value, 'D', [ref]$parsed)) {
        Throw-HardeningTargetSafeError -Code $ErrorCode
    }
    return $parsed.ToString('D').ToLowerInvariant()
}

function Assert-HardeningTargetName {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$Pattern,
        [Parameter(Mandatory = $true)][string]$ErrorCode
    )
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -ne $Value.Trim() -or $Value -notmatch $Pattern) {
        Throw-HardeningTargetSafeError -Code $ErrorCode
    }
}

function Assert-IdentityBindingHardeningTargetInput {
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
    $subscription = ConvertTo-HardeningTargetGuid -Value $ExpectedSubscriptionId -ErrorCode 'EXPECTED_SUBSCRIPTION_ID_INVALID'
    $resourceTenant = ConvertTo-HardeningTargetGuid -Value $ExpectedResourceTenantId -ErrorCode 'EXPECTED_RESOURCE_TENANT_ID_INVALID'
    $externalDirectory = ConvertTo-HardeningTargetGuid -Value $ExpectedExternalDirectoryId -ErrorCode 'EXPECTED_EXTERNAL_DIRECTORY_ID_INVALID'
    if ($resourceTenant -eq $externalDirectory) {
        Throw-HardeningTargetSafeError -Code 'DIRECTORY_ROLE_SEPARATION_INVALID'
    }
    Assert-HardeningTargetName -Value $ResourceGroupName -Pattern '^[A-Za-z0-9._()\-]{1,90}$' -ErrorCode 'RESOURCE_GROUP_NAME_INVALID'
    Assert-HardeningTargetName -Value $WebAppName -Pattern '^[A-Za-z0-9-]{2,60}$' -ErrorCode 'WEB_APP_NAME_INVALID'
    Assert-HardeningTargetName -Value $PostgresServerName -Pattern '^[A-Za-z0-9-]{3,63}$' -ErrorCode 'POSTGRES_SERVER_NAME_INVALID'
    Assert-HardeningTargetName -Value $DatabaseName -Pattern '^[A-Za-z0-9_.-]{1,63}$' -ErrorCode 'DATABASE_NAME_INVALID'
    Assert-HardeningTargetName -Value $DatabaseSettingName -Pattern '^[A-Za-z0-9_.-]{1,64}$' -ErrorCode 'DATABASE_SETTING_NAME_INVALID'
    if ($DatabasePort -lt 1 -or $DatabasePort -gt 65535) {
        Throw-HardeningTargetSafeError -Code 'DATABASE_PORT_INVALID'
    }
    return [pscustomobject]@{
        SubscriptionId = $subscription
        ResourceTenantId = $resourceTenant
        ExternalDirectoryId = $externalDirectory
        ResourceGroupName = $ResourceGroupName
        WebAppName = $WebAppName
        PostgresServerName = $PostgresServerName
        DatabaseName = $DatabaseName
        DatabaseSettingName = $DatabaseSettingName
        DatabasePort = $DatabasePort
    }
}

function Get-HardeningTargetSha256FromParts {
    param(
        [Parameter(Mandatory = $true)][string]$HostName,
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][string]$DatabaseName
    )
    $normalizedHost = $HostName.Trim().ToLowerInvariant()
    Assert-HardeningTargetName -Value $normalizedHost -Pattern '^[a-z0-9.-]+$' -ErrorCode 'DATABASE_TARGET_HOST_INVALID'
    Assert-HardeningTargetName -Value $DatabaseName -Pattern '^[A-Za-z0-9_.-]{1,63}$' -ErrorCode 'DATABASE_TARGET_NAME_INVALID'
    if ($Port -lt 1 -or $Port -gt 65535) {
        Throw-HardeningTargetSafeError -Code 'DATABASE_TARGET_PORT_INVALID'
    }
    $canonical = "postgresql://${normalizedHost}:$Port/$DatabaseName"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($canonical)
    try {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '')
    }
    finally {
        if ($null -ne $sha) { $sha.Dispose() }
        [Array]::Clear($bytes, 0, $bytes.Length)
    }
}

function Get-HardeningTargetSha256FromConnectionString {
    param([Parameter(Mandatory = $true)][string]$ConnectionString)
    try {
        $uri = [System.Uri]::new($ConnectionString)
    }
    catch {
        Throw-HardeningTargetSafeError -Code 'DATABASE_URL_INVALID'
    }
    if ($uri.Scheme -notin @('postgres', 'postgresql')) {
        Throw-HardeningTargetSafeError -Code 'DATABASE_URL_PROTOCOL_INVALID'
    }
    if ([string]::IsNullOrWhiteSpace($uri.Host)) {
        Throw-HardeningTargetSafeError -Code 'DATABASE_URL_HOST_MISSING'
    }
    $databaseName = [System.Uri]::UnescapeDataString($uri.AbsolutePath.TrimStart('/'))
    Assert-HardeningTargetName -Value $databaseName -Pattern '^[A-Za-z0-9_.-]{1,63}$' -ErrorCode 'DATABASE_URL_NAME_INVALID'
    $port = if ($uri.Port -gt 0) { $uri.Port } else { 5432 }
    return Get-HardeningTargetSha256FromParts -HostName $uri.Host -Port $port -DatabaseName $databaseName
}

function Test-IdentityBindingHardeningTargetEvidence {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object]$Account,
        [Parameter(Mandatory = $true)][object]$WebApp,
        [Parameter(Mandatory = $true)][object[]]$DatabaseSettings,
        [Parameter(Mandatory = $true)][object]$PostgresServer,
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
    $inputState = Assert-IdentityBindingHardeningTargetInput @inputArguments
    if ([string]$Account.tenantId -ieq $inputState.ExternalDirectoryId) {
        Throw-HardeningTargetSafeError -Code 'EXTERNAL_DIRECTORY_SELECTED_FOR_RESOURCE_READ'
    }
    if (
        [string]$Account.subscriptionId -ine $inputState.SubscriptionId -or
        [string]$Account.tenantId -ine $inputState.ResourceTenantId
    ) {
        Throw-HardeningTargetSafeError -Code 'AZURE_ACCOUNT_CONTEXT_MISMATCH'
    }
    $scope = "/subscriptions/$($inputState.SubscriptionId)/resourceGroups/$($inputState.ResourceGroupName)"
    $expectedWebAppId = "$scope/providers/Microsoft.Web/sites/$($inputState.WebAppName)"
    $expectedPostgresId = "$scope/providers/Microsoft.DBforPostgreSQL/flexibleServers/$($inputState.PostgresServerName)"
    if ([string]$WebApp.id -ine $expectedWebAppId) {
        Throw-HardeningTargetSafeError -Code 'WEB_APP_RESOURCE_MISMATCH'
    }
    if ([string]$PostgresServer.id -ine $expectedPostgresId) {
        Throw-HardeningTargetSafeError -Code 'POSTGRES_RESOURCE_MISMATCH'
    }
    $settings = @($DatabaseSettings | Where-Object { [string]$_.name -ceq $inputState.DatabaseSettingName })
    if ($settings.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$settings[0].value)) {
        Throw-HardeningTargetSafeError -Code 'DATABASE_SETTING_NOT_UNIQUE'
    }
    if ([string]::IsNullOrWhiteSpace([string]$PostgresServer.fullyQualifiedDomainName)) {
        Throw-HardeningTargetSafeError -Code 'POSTGRES_FQDN_MISSING'
    }
    $actualHash = Get-HardeningTargetSha256FromConnectionString -ConnectionString ([string]$settings[0].value)
    $expectedHash = Get-HardeningTargetSha256FromParts -HostName ([string]$PostgresServer.fullyQualifiedDomainName) -Port $inputState.DatabasePort -DatabaseName $inputState.DatabaseName
    if ($actualHash -cne $expectedHash) {
        Throw-HardeningTargetSafeError -Code 'DATABASE_TARGET_INDEPENDENT_SOURCE_MISMATCH'
    }
    return [pscustomobject]@{
        ConfirmationSha256 = $actualHash
        AccountMatch = $true
        DirectoryRolesSeparated = $true
        WebAppResourceMatch = $true
        PostgresResourceMatch = $true
        TargetMatch = $true
    }
}

Export-ModuleMember -Function @(
    'Assert-IdentityBindingHardeningTargetInput',
    'Get-HardeningTargetSha256FromConnectionString',
    'Get-HardeningTargetSha256FromParts',
    'Test-IdentityBindingHardeningTargetEvidence'
)
