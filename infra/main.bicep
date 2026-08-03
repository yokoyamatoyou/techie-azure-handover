// ============================================================
// TECHIE Azure SaaS main infrastructure
// Phase 2 foundation keeps the original resource names for the
// existing PostgreSQL server and Container Apps.
// ============================================================

targetScope = 'resourceGroup'

@description('Deployment environment')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'prod'

@description('Azure region')
param location string = 'japanwest'

@description('Reuse the existing Container Apps environment instead of modifying network configuration.')
param useExistingContainerAppsEnv bool = true

@description('Existing Container Apps environment name.')
param existingContainerAppsEnvName string = 'techie-cae'

@description('Reuse the existing Container Apps instead of redeploying them with image assumptions.')
param useExistingContainerApps bool = true

@description('Reuse the existing PostgreSQL Flexible Server instead of modifying network configuration.')
param useExistingPostgres bool = true

@description('Existing PostgreSQL Flexible Server name.')
param existingPostgresServerName string = 'techie-pg-server'

@description('PostgreSQL administrator login name.')
param postgresAdminUser string = 'techieadmin'

@description('PostgreSQL admin password')
@secure()
param postgresAdminPassword string

@description('OpenAI API key')
@secure()
param openaiApiKey string

@description('Stripe secret key')
@secure()
param stripeSecretKey string

@description('Stripe webhook secret')
@secure()
param stripeWebhookSecret string

@description('Stripe publishable key')
@secure()
param stripePublishableKey string = ''

@description('Azure AD B2C tenant name')
param b2cTenantName string = ''

@description('Microsoft Entra External ID directory tenant ID')
param b2cTenantId string = ''

@description('Azure AD B2C client ID')
param b2cClientId string = ''

@description('Azure AD B2C policy name')
param b2cPolicy string = 'B2C_1_signup_signin'

@description('Canonical identity resolver mode. Keep legacy until schema and shadow gates pass.')
@allowed(['legacy', 'shadow', 'enforce'])
param identityResolverMode string = 'legacy'

@description('Confirms that the additive identity schema was hash-verified and applied.')
param identitySchemaVerified bool = false

@description('Enable new identity auto-provisioning only after enforce collision gates pass.')
param identityAutoProvision bool = false

@description('Trust Entra tenant/principal binding claims only after their write controls are audited.')
param trustEntraBindingClaims bool = false

var effectiveIdentityResolverMode = identitySchemaVerified && !empty(b2cTenantId) ? identityResolverMode : 'legacy'
var effectiveIdentityAutoProvision = effectiveIdentityResolverMode == 'enforce' && identityAutoProvision
var effectiveTrustEntraBindingClaims = effectiveIdentityResolverMode == 'enforce' && trustEntraBindingClaims

var prefix = 'techie-${environment}'
var acrName = replace('acr${prefix}', '-', '')
var tags = {
  project: 'techie'
  environment: environment
  phase: 'phase2'
}
var includeStripePublishableSecret = !empty(stripePublishableKey)
var sharedSecretRefs = concat([
  { name: 'openai-api-key', value: openaiApiKey }
  { name: 'storage-connection-string', value: queues.outputs.connectionString }
  { name: 'appinsights-connection-string', value: appInsights.outputs.connectionString }
], includeStripePublishableSecret ? [
  { name: 'stripe-publishable-key', value: stripePublishableKey }
] : [])

// ========== Observability ==========
module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'logAnalytics'
  params: {
    name: 'log-${prefix}'
    location: location
    tags: tags
  }
}

module appInsights 'modules/app-insights.bicep' = {
  name: 'appInsights'
  params: {
    name: 'appi-${prefix}'
    location: location
    tags: tags
  }
}

// ========== Network ==========
module vnet 'modules/vnet.bicep' = if (!useExistingContainerAppsEnv || !useExistingPostgres) {
  name: 'vnet'
  params: {
    name: 'vnet-${prefix}'
    location: location
    tags: tags
  }
}

// ========== PostgreSQL Flexible Server ==========
module postgres 'modules/postgres.bicep' = if (!useExistingPostgres) {
  name: 'postgres'
  params: {
    name: existingPostgresServerName
    location: location
    tags: tags
    adminPassword: postgresAdminPassword
    subnetId: vnet!.outputs.postgresSubnetId
    privateDnsZoneId: vnet!.outputs.postgresDnsZoneId
  }
}

resource existingPostgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' existing = if (useExistingPostgres) {
  name: existingPostgresServerName
}

var postgresServerNameValue = useExistingPostgres ? existingPostgres!.name : postgres!.outputs.name
var postgresHostValue = useExistingPostgres ? existingPostgres!.properties.fullyQualifiedDomainName : postgres!.outputs.host
var postgresConnectionStringValue = 'postgresql://${postgresAdminUser}:PASSWORD@${postgresHostValue}:5432/techie?sslmode=require'

// ========== Queue-backed phase 2 jobs ==========
module queues 'modules/storage-queues.bicep' = {
  name: 'storageQueues'
  params: {
    name: take(replace('st${prefix}ops', '-', ''), 24)
    location: location
    tags: tags
  }
}

// ========== Key Vault ==========
module keyVault 'modules/keyvault.bicep' = {
  name: 'keyVault'
  params: {
    name: 'kv-${prefix}'
    location: location
    tags: tags
    openaiApiKey: openaiApiKey
    stripeSecretKey: stripeSecretKey
    stripeWebhookSecret: stripeWebhookSecret
    stripePublishableKey: stripePublishableKey
    postgresConnectionString: postgresConnectionStringValue
    storageConnectionString: queues.outputs.connectionString
    appInsightsConnectionString: appInsights.outputs.connectionString
  }
}

// ========== Container Registry ==========
module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    name: acrName
    location: location
    tags: tags
  }
}

resource existingAcr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

var acrUsername = existingAcr.listCredentials().username
var acrPassword = existingAcr.listCredentials().passwords[0].value

// ========== Container Apps environment ==========
module containerAppsEnv 'modules/container-apps-env.bicep' = if (!useExistingContainerAppsEnv) {
  name: 'containerAppsEnv'
  params: {
    name: existingContainerAppsEnvName
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
    subnetId: vnet!.outputs.containerAppsSubnetId
  }
}

resource existingContainerAppsEnv 'Microsoft.App/managedEnvironments@2024-03-01' existing = if (useExistingContainerAppsEnv) {
  name: existingContainerAppsEnvName
}

var containerAppsEnvId = useExistingContainerAppsEnv ? existingContainerAppsEnv!.id : containerAppsEnv!.outputs.envId

// ========== Container Apps (existing 4 services) ==========
module kotomake 'modules/container-app.bicep' = if (!useExistingContainerApps) {
  name: 'kotomake'
  params: {
    name: 'kotomake'
    location: location
    tags: tags
    envId: containerAppsEnvId
    acrLoginServer: acr.outputs.loginServer
    imageName: 'notecode'
    imageTag: 'latest'
    targetPort: 8080
    isExternal: true
    cpu: '1.0'
    memory: '2Gi'
    minReplicas: 1
    maxReplicas: 3
    envVars: [
      { name: 'PORT', value: '8080' }
      { name: 'HEADLESS', value: '1' }
      { name: 'AUTH_IDENTITY_MODE', value: 'entra_external_id' }
      { name: 'AUTH_IDENTITY_RESOLVER_MODE', value: effectiveIdentityResolverMode }
      { name: 'AUTH_IDENTITY_AUTO_PROVISION', value: effectiveIdentityAutoProvision ? '1' : '0' }
      { name: 'AUTH_TRUST_ENTRA_BINDING_CLAIMS', value: effectiveTrustEntraBindingClaims ? '1' : '0' }
      { name: 'ENTRA_EXTERNAL_ID_TENANT_NAME', value: b2cTenantName }
      { name: 'ENTRA_EXTERNAL_ID_TENANT_ID', value: b2cTenantId }
      { name: 'ENTRA_EXTERNAL_ID_CLIENT_ID', value: b2cClientId }
      { name: 'ENTRA_EXTERNAL_ID_POLICY', value: b2cPolicy }
      { name: 'AZURE_B2C_TENANT_NAME', value: b2cTenantName }
      { name: 'AZURE_B2C_CLIENT_ID', value: b2cClientId }
      { name: 'AZURE_B2C_POLICY', value: b2cPolicy }
      { name: 'AUTH_DEV_MODE', value: environment == 'dev' ? '1' : '0' }
    ]
    secretRefs: concat(sharedSecretRefs, [
      { name: 'database-url', value: postgresConnectionStringValue }
    ])
    registryUsername: acrUsername
    registryPassword: acrPassword
  }
}

module kotomigaki 'modules/container-app.bicep' = if (!useExistingContainerApps) {
  name: 'kotomigaki'
  params: {
    name: 'kotomigaki'
    location: location
    tags: tags
    envId: containerAppsEnvId
    acrLoginServer: acr.outputs.loginServer
    imageName: 'aio2-main'
    imageTag: 'latest'
    targetPort: 8081
    isExternal: true
    cpu: '2.0'
    memory: '4Gi'
    minReplicas: 1
    maxReplicas: 3
    envVars: [
      { name: 'PORT', value: '8081' }
      { name: 'HEADLESS', value: '1' }
      { name: 'PLAYWRIGHT_BROWSERS_PATH', value: '/ms-playwright' }
      { name: 'AUTH_IDENTITY_MODE', value: 'entra_external_id' }
      { name: 'AUTH_IDENTITY_RESOLVER_MODE', value: effectiveIdentityResolverMode }
      { name: 'AUTH_IDENTITY_AUTO_PROVISION', value: effectiveIdentityAutoProvision ? '1' : '0' }
      { name: 'AUTH_TRUST_ENTRA_BINDING_CLAIMS', value: effectiveTrustEntraBindingClaims ? '1' : '0' }
      { name: 'ENTRA_EXTERNAL_ID_TENANT_NAME', value: b2cTenantName }
      { name: 'ENTRA_EXTERNAL_ID_TENANT_ID', value: b2cTenantId }
      { name: 'ENTRA_EXTERNAL_ID_CLIENT_ID', value: b2cClientId }
      { name: 'ENTRA_EXTERNAL_ID_POLICY', value: b2cPolicy }
      { name: 'AZURE_B2C_TENANT_NAME', value: b2cTenantName }
      { name: 'AZURE_B2C_CLIENT_ID', value: b2cClientId }
      { name: 'AZURE_B2C_POLICY', value: b2cPolicy }
      { name: 'AUTH_DEV_MODE', value: environment == 'dev' ? '1' : '0' }
    ]
    secretRefs: concat(sharedSecretRefs, [
      { name: 'database-url', value: postgresConnectionStringValue }
    ])
    registryUsername: acrUsername
    registryPassword: acrPassword
  }
}

module kotomusubi 'modules/container-app.bicep' = if (!useExistingContainerApps) {
  name: 'kotomusubi'
  params: {
    name: 'kotomusubi'
    location: location
    tags: tags
    envId: containerAppsEnvId
    acrLoginServer: acr.outputs.loginServer
    imageName: 'doorknock'
    imageTag: 'latest'
    targetPort: 8082
    isExternal: false
    cpu: '1.0'
    memory: '2Gi'
    minReplicas: 1
    maxReplicas: 2
    envVars: [
      { name: 'PORT', value: '8082' }
      { name: 'HEADLESS', value: '1' }
      { name: 'PYTHONPATH', value: '/app/aio2-main' }
    ]
    secretRefs: sharedSecretRefs
    registryUsername: acrUsername
    registryPassword: acrPassword
  }
}

module hub 'modules/container-app.bicep' = if (!useExistingContainerApps) {
  name: 'hub'
  params: {
    name: 'techie-hub'
    location: location
    tags: tags
    envId: containerAppsEnvId
    acrLoginServer: acr.outputs.loginServer
    imageName: 'techie-hub'
    imageTag: 'latest'
    targetPort: 8090
    isExternal: true
    cpu: '0.25'
    memory: '0.5Gi'
    minReplicas: 1
    maxReplicas: 1
    envVars: [
      { name: 'PORT', value: '8090' }
      { name: 'AUTH_IDENTITY_MODE', value: 'entra_external_id' }
      { name: 'AUTH_IDENTITY_RESOLVER_MODE', value: effectiveIdentityResolverMode }
      { name: 'AUTH_IDENTITY_AUTO_PROVISION', value: effectiveIdentityAutoProvision ? '1' : '0' }
      { name: 'AUTH_TRUST_ENTRA_BINDING_CLAIMS', value: effectiveTrustEntraBindingClaims ? '1' : '0' }
      { name: 'ENTRA_EXTERNAL_ID_TENANT_NAME', value: b2cTenantName }
      { name: 'ENTRA_EXTERNAL_ID_TENANT_ID', value: b2cTenantId }
      { name: 'ENTRA_EXTERNAL_ID_CLIENT_ID', value: b2cClientId }
      { name: 'ENTRA_EXTERNAL_ID_POLICY', value: b2cPolicy }
      { name: 'AZURE_B2C_TENANT_NAME', value: b2cTenantName }
      { name: 'AZURE_B2C_CLIENT_ID', value: b2cClientId }
      { name: 'AZURE_B2C_POLICY', value: b2cPolicy }
      { name: 'AUTH_DEV_MODE', value: environment == 'dev' ? '1' : '0' }
    ]
    secretRefs: concat(sharedSecretRefs, [
      { name: 'database-url', value: postgresConnectionStringValue }
    ])
    registryUsername: acrUsername
    registryPassword: acrPassword
  }
}

// ========== Outputs ==========
output resourceGroupName string = resourceGroup().name
output acrLoginServer string = acr.outputs.loginServer
output postgresServerName string = postgresServerNameValue
output postgresHost string = postgresHostValue
output kotomakeAppName string = useExistingContainerApps ? 'kotomake' : kotomake!.outputs.name
output kotomakeFqdn string = useExistingContainerApps ? '' : kotomake!.outputs.fqdn
output kotomigakiAppName string = useExistingContainerApps ? 'kotomigaki' : kotomigaki!.outputs.name
output kotomigakiFqdn string = useExistingContainerApps ? '' : kotomigaki!.outputs.fqdn
output kotomusubiAppName string = useExistingContainerApps ? 'kotomusubi' : kotomusubi!.outputs.name
output hubAppName string = useExistingContainerApps ? 'techie-hub' : hub!.outputs.name
output hubFqdn string = useExistingContainerApps ? '' : hub!.outputs.fqdn
output storageAccountName string = queues.outputs.accountName
output stripeWebhookQueueName string = queues.outputs.stripeWebhookQueueName
output stripeWebhookDeadLetterQueueName string = queues.outputs.stripeWebhookDeadLetterQueueName
output resellerPayoutQueueName string = queues.outputs.resellerPayoutQueueName
output resellerPayoutDeadLetterQueueName string = queues.outputs.resellerPayoutDeadLetterQueueName
output couponQueueName string = queues.outputs.couponQueueName
output couponDeadLetterQueueName string = queues.outputs.couponDeadLetterQueueName
output appInsightsName string = appInsights.outputs.name
