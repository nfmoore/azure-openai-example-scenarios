//********************************************************
// Parameters
//********************************************************

// Workload identifier used to create unique names for resources.
@description('A unique identifier for the workload.')
@minLength(2)
@maxLength(6)
param workloadIdentifier string = substring(uniqueString(resourceGroup().id), 1, 6)

// Environment identifier used to create unique names for resources.
@description('A unique identifier for the environment.')
@minLength(2)
@maxLength(8)
param environmentIdentifier string = '01'

// The location of resource deployments. Defaults to the location of the resource group.
@description('The location of resource deployments.')
param deploymentLocation string = resourceGroup().location

//********************************************************
// Variables
//********************************************************

// Search Index Data Reader
var azureRbacSearchIndexDataReaderRoleId = '1407120a-92aa-4202-b7e9-c0e197c71c8f'

// Search Service Contributor
var azureRbacSearchServiceContributorRoleId = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'

// Storage Blob Data Contributor
var azureRbacStorageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'

// Cognitive Services OpenAI Contributor
var azureRbacCognitiveServicesOpenAIContributorRoleId = 'a001fd3d-188f-4b5d-821b-7da978bf7442'

//********************************************************
// Resources
//********************************************************

// Azure Storage Account
resource r_storageAccount 'Microsoft.Storage/storageAccounts@2022-05-01' = {
  name: 'st${workloadIdentifier}${environmentIdentifier}'
  location: deploymentLocation
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    encryption: {
      services: {
        blob: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
    publicNetworkAccess: 'Enabled'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    isHnsEnabled: false
    minimumTlsVersion: 'TLS1_2'
  }
}

// Azure AI Search
resource r_aiSearch 'Microsoft.Search/searchServices@2023-11-01' = {
  name: 'search${workloadIdentifier}${environmentIdentifier}'
  location: deploymentLocation
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'standard'
  }
  properties: {
    networkRuleSet: {
      ipRules: []
    }
    publicNetworkAccess: 'enabled'
    disableLocalAuth: false
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

// Azure Open AI Account
resource r_aoaiAccount 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: 'aoai${workloadIdentifier}${environmentIdentifier}'
  location: deploymentLocation
  kind: 'OpenAI'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: 'aoai${workloadIdentifier}${environmentIdentifier}'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
  }
  sku: {
    name: 'S0'
  }
}

// Define Azure Open AI Account Deployments
var modelDeployments = [
  {
    name: 'gpt-35-turbo-16k-0613'
    modelName: 'gpt-35-turbo-16k'
    modelVersion: '0613'
  }
  {
    name: 'text-embedding-ada-002-2'
    modelName: 'text-embedding-ada-002'
    modelVersion: '2'
  }
]

// Azure Open AI Account Deployments
@batchSize(1)
resource r_aoaiDeploymentsChat 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = [for deployment in modelDeployments: {
  parent: r_aoaiAccount
  name: deployment.name
  properties: {
    model: {
      format: 'OpenAI'
      name: deployment.modelName
      version: deployment.modelVersion
    }
  }
  sku: {
    name: 'Standard'
    capacity: 30
  }
}]

//********************************************************
// RBAC Role Assignments
//********************************************************

resource r_azureSearchIndexDataReaderAzureOpenAiAssignment 'Microsoft.Authorization/roleAssignments@2020-08-01-preview' = {
  name: guid(r_aiSearch.name, r_aoaiAccount.name, 'searchIndexDataReader')
  scope: r_aiSearch
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', azureRbacSearchIndexDataReaderRoleId)
    principalId: r_aoaiAccount.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource r_azureSearchServiceContributorAzureOpenAiAssignment 'Microsoft.Authorization/roleAssignments@2020-08-01-preview' = {
  name: guid(r_aiSearch.name, r_aoaiAccount.name, 'searchServiceContributor')
  scope: r_aiSearch
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', azureRbacSearchServiceContributorRoleId)
    principalId: r_aoaiAccount.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource r_storageBlobDataContributorAzureOpenAiAssignment 'Microsoft.Authorization/roleAssignments@2020-08-01-preview' = {
  name: guid(r_storageAccount.name, r_aoaiAccount.name, 'storageBlobDataContributor')
  scope: r_storageAccount
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', azureRbacStorageBlobDataContributorRoleId)
    principalId: r_aoaiAccount.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource r_cognitiveServicesOpenAiContributorAzureAiSearchAssignment 'Microsoft.Authorization/roleAssignments@2020-08-01-preview' = {
  name: guid(r_aoaiAccount.name, r_aiSearch.name, 'cognitiveServicesOpenAiContributor')
  scope: r_aoaiAccount
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', azureRbacCognitiveServicesOpenAIContributorRoleId)
    principalId: r_aiSearch.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource r_storageBlobDataContributorAzureAiSearchAssignment 'Microsoft.Authorization/roleAssignments@2020-08-01-preview' = {
  name: guid(r_storageAccount.name, r_aiSearch.name, 'storageBlobDataContributor')
  scope: r_storageAccount
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', azureRbacStorageBlobDataContributorRoleId)
    principalId: r_aiSearch.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
