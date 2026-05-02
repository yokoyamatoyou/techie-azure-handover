param name string
param location string
param tags object

@secure()
param openaiApiKey string
@secure()
param stripeSecretKey string
@secure()
param stripeWebhookSecret string
@secure()
param stripePublishableKey string = ''
@secure()
param postgresConnectionString string
@secure()
param storageConnectionString string
@secure()
param appInsightsConnectionString string

resource keyVault 'Microsoft.KeyVault/vaults@2024-04-01-preview' = {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

resource secretOpenai 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: openaiApiKey
  }
}

resource secretStripe 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: keyVault
  name: 'stripe-secret-key'
  properties: {
    value: stripeSecretKey
  }
}

resource secretStripeWebhook 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: keyVault
  name: 'stripe-webhook-secret'
  properties: {
    value: stripeWebhookSecret
  }
}

resource secretStripePublishable 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = if (!empty(stripePublishableKey)) {
  parent: keyVault
  name: 'stripe-publishable-key'
  properties: {
    value: stripePublishableKey
  }
}

resource secretDb 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: keyVault
  name: 'database-url'
  properties: {
    value: postgresConnectionString
  }
}

resource secretStorage 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: keyVault
  name: 'storage-connection-string'
  properties: {
    value: storageConnectionString
  }
}

resource secretAppInsights 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: keyVault
  name: 'appinsights-connection-string'
  properties: {
    value: appInsightsConnectionString
  }
}

output vaultId string = keyVault.id
output vaultUri string = keyVault.properties.vaultUri
