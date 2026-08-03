targetScope = 'resourceGroup'

@description('Azure region of the existing TECHIE resources.')
param location string = resourceGroup().location

@description('Existing Container Apps managed environment name.')
param containerAppsEnvironmentName string

@description('Existing Azure Container Registry name.')
param acrName string

@description('Existing production Key Vault name.')
param keyVaultName string

@description('Existing dedicated user-assigned identity created by foundation.bicep.')
param identityName string = 'techie-identity-shadow-mi'

@description('Manual Container Apps Job name. Creation does not start an execution.')
@minLength(2)
@maxLength(31)
param jobName string = 'techie-identity-shadow'

@description('ACR repository containing the reviewed read-only probe image.')
param imageRepository string = 'techie-identity-shadow'

@description('Immutable image manifest digest in sha256:<64 lowercase hexadecimal> form.')
@minLength(71)
@maxLength(71)
param imageDigest string

@description('Name only of the Key Vault secret containing DATABASE_URL.')
param databaseSecretName string = 'database-url'

@secure()
@description('Exact 32-character Key Vault secret version. Kept secure to suppress the versioned URI in deployment history.')
@minLength(32)
@maxLength(32)
param databaseSecretVersion string

@description('Existing workload profile. Consumption preserves scale-to-zero behavior between manual executions.')
param workloadProfileName string = 'Consumption'

@description('Non-secret governance tags.')
param tags object = {
  purpose: 'identity-shadow-read-only'
  productionTraffic: 'none'
  trigger: 'manual-only'
  managedBy: 'reviewed-bicep'
}

resource environment 'Microsoft.App/managedEnvironments@2025-07-01' existing = {
  name: containerAppsEnvironmentName
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource shadowIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: identityName
}

var imageReference = '${registry.properties.loginServer}/${imageRepository}@${imageDigest}'
var databaseSecretUrl = '${vault.properties.vaultUri}secrets/${databaseSecretName}/${databaseSecretVersion}'

resource shadowJob 'Microsoft.App/jobs@2025-07-01' = {
  name: jobName
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${shadowIdentity.id}': {}
    }
  }
  properties: {
    environmentId: environment.id
    workloadProfileName: workloadProfileName
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 300
      replicaRetryLimit: 0
      manualTriggerConfig: {
        parallelism: 1
        replicaCompletionCount: 1
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: shadowIdentity.id
        }
      ]
      secrets: [
        {
          name: 'database-url'
          keyVaultUrl: databaseSecretUrl
          identity: shadowIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'identity-shadow'
          image: imageReference
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'DATABASE_URL'
              secretRef: 'database-url'
            }
            {
              name: 'AUTH_IDENTITY_RESOLVER_MODE'
              value: 'shadow'
            }
            {
              name: 'AUTH_IDENTITY_AUTO_PROVISION'
              value: '0'
            }
            {
              name: 'AUTH_TRUST_ENTRA_BINDING_CLAIMS'
              value: '0'
            }
          ]
        }
      ]
    }
  }
}

output jobResourceId string = shadowJob.id
output deployedJobName string = shadowJob.name
output triggerType string = shadowJob.properties.configuration.triggerType
