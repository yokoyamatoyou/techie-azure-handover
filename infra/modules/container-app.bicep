param name string
param location string
param tags object
param envId string
param acrLoginServer string
param imageName string
param imageTag string = 'latest'
param targetPort int
param isExternal bool = true
param cpu string = '0.5'
param memory string = '1Gi'
param minReplicas int = 1
param maxReplicas int = 3
param envVars array = []
param secretRefs array = []
param keyVaultId string = ''
param grantKeyVaultSecretsUserRole bool = false
param registryUsername string = ''
@secure()
param registryPassword string = ''

var secretEnvVars = [for secret in secretRefs: {
  name: replace(toUpper(replace(secret.name, '-', '_')), ' ', '')
  secretRef: secret.name
}]

var includeRegistryPassword = !empty(registryUsername) && !empty(registryPassword)

var containerAppSecrets = [for secret in secretRefs: union({
  name: secret.name
}, contains(secret, 'value') ? {
  value: secret.value
} : {}, contains(secret, 'keyVaultUrl') ? {
  keyVaultUrl: secret.keyVaultUrl
  identity: 'system'
} : {})]

var allSecrets = includeRegistryPassword
  ? concat(containerAppSecrets, [
      {
        name: 'acr-password'
        value: registryPassword
      }
    ])
  : containerAppSecrets

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: envId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: isExternal
        targetPort: targetPort
        transport: 'auto'
        corsPolicy: {
          allowedOrigins: ['*']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          maxAge: 3600
        }
      }
      registries: includeRegistryPassword
        ? [
            {
              server: acrLoginServer
              username: registryUsername
              passwordSecretRef: 'acr-password'
            }
          ]
        : [
            {
              server: acrLoginServer
              identity: 'system'
            }
          ]
      secrets: allSecrets
    }
    template: {
      containers: [
        {
          name: imageName
          image: '${acrLoginServer}/${imageName}:${imageTag}'
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: concat(envVars, secretEnvVars)
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                port: targetPort
                path: '/health'
              }
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                port: targetPort
                path: '/health'
              }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// Key Vault へのアクセス許可 (RBAC)
resource kvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (grantKeyVaultSecretsUserRole && !empty(keyVaultId)) {
  name: guid(keyVaultId, containerApp.id, 'Key Vault Secrets User')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output fqdn string = containerApp.properties.configuration.ingress.fqdn
output appId string = containerApp.id
output name string = containerApp.name
