targetScope = 'resourceGroup'

@description('Azure region of the existing TECHIE resources.')
param location string = resourceGroup().location

@description('Existing Azure Container Registry name.')
param acrName string

@description('Existing production Key Vault name. The template never reads or writes a secret value.')
param keyVaultName string

@description('Existing Key Vault secret name to which read access is narrowly scoped.')
param databaseSecretName string = 'database-url'

@description('Dedicated user-assigned identity for the manual shadow job.')
@minLength(3)
@maxLength(128)
param identityName string = 'techie-identity-shadow-mi'

@description('Non-secret governance tags.')
param tags object = {
  purpose: 'identity-shadow-read-only'
  productionTraffic: 'none'
  managedBy: 'reviewed-bicep'
}

var acrPullRoleDefinitionId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
var keyVaultSecretsUserRoleDefinitionId = '4633458b-17de-408a-b874-0445c86b69e6'

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource databaseSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' existing = {
  parent: vault
  name: databaseSecretName
}

resource shadowIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: tags
}

resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, shadowIdentity.id, acrPullRoleDefinitionId)
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleDefinitionId)
    principalId: shadowIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource keyVaultSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(databaseSecret.id, shadowIdentity.id, keyVaultSecretsUserRoleDefinitionId)
  scope: databaseSecret
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleDefinitionId)
    principalId: shadowIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output identityResourceId string = shadowIdentity.id
output identityPrincipalId string = shadowIdentity.properties.principalId
output acrPullRoleAssignmentId string = acrPullRole.id
output keyVaultSecretRoleAssignmentId string = keyVaultSecretsUserRole.id
