//********************************************************
// Parameters
//********************************************************

@description('Name of the AI Services account')
param name string

@description('Location for AI Services account')
param location string = resourceGroup().location

@description('Tags for the AI Services account')
param tags object = {}

@description('Kind of AI Services account')
param kind string = 'CognitiveServices'

@description('Role assignments for the Azure Search account')
param roles array = []

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

@description('Deployments for the AI Services account')
param deployments array = [
  {
    name: 'gpt-4-32k'
    version: '0613'
  }
  {
    name: 'gpt-35-turbo-16k'
    version: '0613'
  }
  {
    name: 'text-embedding-ada-002'
    version: '2'
  }
]

//********************************************************
// Resources
//********************************************************

resource aisaNew 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'S0'
  }
  kind: kind
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: name
  }

  @batchSize(1)
  resource aisaDeployments 'deployments@2023-05-01' = [
    for deployment in deployments: if (kind == 'OpenAI') {
      name: '${deployment.name}-${deployment.version}'
      properties: {
        model: {
          format: 'OpenAI'
          name: deployment.name
          version: deployment.version
        }
        versionUpgradeOption: 'NoAutoUpgrade'
      }
      sku: {
        name: 'Standard'
        capacity: contains(deployment, 'capacity') ? deployment.capacity : 20
      }
    }
  ]
}

resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'all-logs-all-metrics'
  scope: aisaNew
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
    scope: aisaNew
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

output name string = aisaNew.name
output id string = aisaNew.id
output principalId string = aisaNew.identity.principalId
