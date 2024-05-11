//********************************************************
// Parameters
//********************************************************

// @description('Resource group name')
// param resourceGroupName string = 'rg-example-scenario-azure-databricks-online-inference-containers'

// @description('Databricks managed resource group name')
// param mrgDatabricksName string = 'rgm-example-scenario-azure-databricks-online-inference-containers-databricks'

// @description('Kubernetes managed resource group name')
// param mrgKubernetesName string = 'rgm-example-scenario-azure-databricks-online-inference-containers-kubernetes'

@description('Location for resources')
param location string = az.resourceGroup().location

@description('User Object ID for authenticated user')
param userObjectId string

//********************************************************
// Variables
//********************************************************

var serviceSuffix = substring(uniqueString(az.resourceGroup().id), 0, 5)

var resources = {
  applicationInsightsName: 'appi01${serviceSuffix}'
  containerRegistryName: 'cr01${serviceSuffix}'
  logAnalyticsWorkspaceName: 'log01${serviceSuffix}'
  storageAccountName: 'st01${serviceSuffix}'
  userAssignedIdentityName: 'id01${serviceSuffix}'
  containerAppEnvironmnetName: 'cae01${serviceSuffix}'
  aiSearchName: 'srch01${serviceSuffix}'
  openAiName: 'oai01${serviceSuffix}'
  aiServicesName: 'aisa01${serviceSuffix}'
  deploymentScriptName: 'ds01${serviceSuffix}'
}

// ********************************************************
// Modules
// ********************************************************

module userAssignedIdentity './modules/user-assigned-identity.bicep' = {
  name: '${resources.userAssignedIdentityName}-deployment'
  params: {
    name: resources.userAssignedIdentityName
    location: location
    tags: {
      environment: 'shared'
    }
  }
}

module storageAccount './modules/storage-account.bicep' = {
  name: '${resources.storageAccountName}-01-deployment'
  params: {
    name: resources.storageAccountName
    location: location
    tags: {
      environment: 'shared'
    }
  }
}

module storageAccountRoleAssignements './modules/storage-account.bicep' = {
  name: '${resources.storageAccountName}-02-deployment'
  params: {
    name: resources.storageAccountName
    location: location
    roles: [
      {
        principalId: aiSearch.outputs.principalId
        id: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
      }
      {
        principalId: userObjectId
        id: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
        type: 'User'
      }
    ]
  }
}

module logAnalyticsWorkspace './modules/log-analytics-workspace.bicep' = {
  name: '${resources.logAnalyticsWorkspaceName}-deployment'
  params: {
    name: resources.logAnalyticsWorkspaceName
    location: location
    tags: {
      environment: 'shared'
    }
    storageAccountId: storageAccount.outputs.id
  }
}

module containerRegistry './modules/container-registry.bicep' = {
  name: '${resources.containerRegistryName}-deployment'
  params: {
    name: resources.containerRegistryName
    location: location
    tags: {
      environment: 'shared'
    }
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.outputs.id
    roles: [
      {
        principalId: userAssignedIdentity.outputs.principalId
        id: '7f951dda-4ed3-4680-a7ca-43fe172d538d' // ACR Pull role
      }
    ]
  }
}

module containerAppsEnvironment './modules/container-app-environment.bicep' = {
  name: '${resources.containerAppEnvironmnetName}-deployment'
  params: {
    name: resources.containerAppEnvironmnetName
    location: location
    tags: {
      environment: 'shared'
    }
    logAnalyticsWorkspaceName: logAnalyticsWorkspace.outputs.name
    logAnalyticsWorkspaceResourceGroupName: az.resourceGroup().name
  }
}

module aiSearch './modules/ai-search.bicep' = {
  name: '${resources.aiSearchName}-deployment'
  params: {
    name: resources.aiSearchName
    location: location
    tags: {
      environment: 'shared'
    }
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.outputs.id
    roles: [
      {
        principalId: userAssignedIdentity.outputs.principalId
        id: '7ca78c08-252a-4471-8644-bb5ff32d4ba0' // Search Service Contributor
      }
      {
        principalId: userAssignedIdentity.outputs.principalId
        id: '1407120a-92aa-4202-b7e9-c0e197c71c8f' // Search Index Data Reader
      }
      {
        principalId: openAi.outputs.principalId
        id: '7ca78c08-252a-4471-8644-bb5ff32d4ba0' // Search Service Contributor
      }
      {
        principalId: openAi.outputs.principalId
        id: '1407120a-92aa-4202-b7e9-c0e197c71c8f' // Search Index Data Reader
      }
      {
        principalId: userObjectId
        id: '7ca78c08-252a-4471-8644-bb5ff32d4ba0' // Search Service Contributor
        type: 'User'
      }
      {
        principalId: userObjectId
        id: '8ebe5a00-799e-43f5-93ac-243d3dce84a7' // Search Index Data Contributor
        type: 'User'
      }
    ]
  }
}

module openAi './modules/ai-services.bicep' = {
  name: '${resources.openAiName}-01-deployment'
  params: {
    name: resources.openAiName
    location: location
    tags: {
      environment: 'shared'
    }
    kind: 'OpenAI'
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.outputs.id
    roles: [
      {
        principalId: userAssignedIdentity.outputs.principalId
        id: 'a001fd3d-188f-4b5d-821b-7da978bf7442' // Cognitive Services OpenAI Contributor
      }
      {
        principalId: userObjectId
        id: 'a001fd3d-188f-4b5d-821b-7da978bf7442' // Cognitive Services OpenAI Contributor
        type: 'User'
      }
    ]
  }
}

module openAiRoleAssignments './modules/ai-services.bicep' = {
  name: '${resources.openAiName}-02-deployment'
  params: {
    name: resources.openAiName
    location: location
    tags: {
      environment: 'shared'
    }
    kind: 'OpenAI'
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.outputs.id
    roles: [
      {
        principalId: aiSearch.outputs.principalId
        id: 'a001fd3d-188f-4b5d-821b-7da978bf7442' // Cognitive Services OpenAI Contributor
      }
    ]
  }
}

module aiServices './modules/ai-services.bicep' = {
  name: '${resources.aiServicesName}-deployment'
  params: {
    name: resources.aiServicesName
    location: location
    tags: {
      environment: 'shared'
    }
    kind: 'CognitiveServices'
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.outputs.id
    roles: [
      {
        principalId: userAssignedIdentity.outputs.principalId
        id: '25fbc0a9-bd7c-42a3-aa1a-3b75d497ee68' // Cognitive Services Contributor
      }
    ]
  }
}

//********************************************************
// Outputs
//********************************************************

output storageAccountName string = storageAccount.outputs.name
output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.outputs.name
output containerRegistryName string = containerRegistry.outputs.name
output userAssignedIdentityName string = userAssignedIdentity.outputs.name
output containerAppEnvironmnetStagingName string = containerAppsEnvironment.outputs.name
