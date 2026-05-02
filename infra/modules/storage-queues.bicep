param name string
param location string
param tags object

var queueNames = [
  'stripe-webhook-events'
  'stripe-webhook-deadletter'
  'reseller-payout-jobs'
  'reseller-payout-deadletter'
  'coupon-jobs'
  'coupon-deadletter'
]

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    accessTier: 'Hot'
  }
}

resource queueService 'Microsoft.Storage/storageAccounts/queueServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource queues 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-05-01' = [for queueName in queueNames: {
  parent: queueService
  name: queueName
}]

output accountName string = storage.name
output queueEndpoint string = 'https://${storage.name}.queue.${environment().suffixes.storage}'
@secure()
output connectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
output stripeWebhookQueueName string = queueNames[0]
output stripeWebhookDeadLetterQueueName string = queueNames[1]
output resellerPayoutQueueName string = queueNames[2]
output resellerPayoutDeadLetterQueueName string = queueNames[3]
output couponQueueName string = queueNames[4]
output couponDeadLetterQueueName string = queueNames[5]
