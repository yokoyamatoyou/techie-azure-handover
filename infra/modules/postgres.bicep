param name string
param location string
param tags object

@secure()
param adminPassword string
param subnetId string
param privateDnsZoneId string

var adminUser = 'techieadmin'

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Standard_B2ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: adminUser
    administratorLoginPassword: adminPassword
    storage: {
      storageSizeGB: 32
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      delegatedSubnetResourceId: subnetId
      privateDnsZoneArmResourceId: privateDnsZoneId
    }
  }
}

resource db 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: 'techie'
  properties: {
    charset: 'UTF8'
    collation: 'ja_JP.utf8'
  }
}

output host string = postgres.properties.fullyQualifiedDomainName
output connectionString string = 'postgresql://${adminUser}:PASSWORD@${postgres.properties.fullyQualifiedDomainName}:5432/techie?sslmode=require'
output name string = postgres.name
