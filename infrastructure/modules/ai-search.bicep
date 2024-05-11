//********************************************************
// Parameters
//********************************************************

@description('Name of the Azure AI Search service')
param name string

@description('Location for the Azure AI Search service')
param location string = resourceGroup().location

@description('Tags for the Azure AI Search service')
param tags object = {}

@description('Role assignments for the Azure AI Search service')
param roles array = []

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

resource srchNew 'Microsoft.Search/searchServices@2023-11-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'standard'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

//********************************************************
// Resources
//********************************************************

resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'all-logs-all-metrics'
  scope: srchNew
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource roleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for role in roles: {
    name: guid(name, role.principalId, role.id)
    scope: srchNew
    properties: {
      roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', role.id)
      principalId: role.principalId
      principalType: contains(role, 'type') ? role.type : 'ServicePrincipal'
    }
  }
]

//********************************************************
// Outputs
//********************************************************

output name string = srchNew.name
output id string = srchNew.id
output principalId string = srchNew.identity.principalId
