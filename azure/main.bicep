param location string = resourceGroup().location
param storageName string = 'callpilot${uniqueString(resourceGroup().id)}'
param functionName string = 'callpilot-fn-${uniqueString(resourceGroup().id)}'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
  }
}

resource plan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: 'callpilot-consumption'
  location: location
  kind: 'linux'
  sku: { name: 'Y1', tier: 'Dynamic' }
  properties: { reserved: true }
}

resource app 'Microsoft.Web/sites@2022-03-01' = {
  name: functionName
  location: location
  kind: 'functionapp,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      appSettings: [
        { name: 'FUNCTIONS_EXTENSION_VERSION'; value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME'; value: 'python' }
        { name: 'AzureWebJobsStorage'; value: 'UseDevelopmentStorage=true' }
      ]
    }
  }
}

output functionAppName string = app.name
output storageAccountName string = storage.name
