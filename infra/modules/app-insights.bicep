param name string
param location string
param tags object
param applicationType string = 'web'

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: applicationType
  }
}

output name string = appInsights.name
output connectionString string = appInsights.properties.ConnectionString
