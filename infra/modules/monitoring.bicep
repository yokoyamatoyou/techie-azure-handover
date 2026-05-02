// ============================================================
// TECHIE 監視・アラート設定
//
// デプロイ:
//   az deployment group create \
//     --resource-group rg-techie-prod \
//     --template-file monitoring.bicep \
//     --parameters alertEmail=admin@example.com
// ============================================================

param location string = resourceGroup().location
param alertEmail string
param logAnalyticsWorkspaceId string
param environment string = 'prod'

var prefix = 'techie-${environment}'

// ========== アクション グループ ==========
resource actionGroup 'Microsoft.Insights/actionGroups@2023-09-01-preview' = {
  name: 'ag-${prefix}-critical'
  location: 'global'
  properties: {
    groupShortName: 'TechieAlert'
    enabled: true
    emailReceivers: [
      {
        name: 'admin'
        emailAddress: alertEmail
        useCommonAlertSchema: true
      }
    ]
  }
}

// ========== サービスダウン アラート ==========
resource alertContainerDown 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'alert-${prefix}-container-down'
  location: 'global'
  properties: {
    description: 'Container App のレプリカが 0 になった場合のアラート'
    severity: 0
    enabled: true
    scopes: [resourceGroup().id]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.MultipleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'ReplicaCount'
          metricName: 'Replicas'
          metricNamespace: 'Microsoft.App/containerApps'
          operator: 'LessThan'
          threshold: 1
          timeAggregation: 'Average'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroup.id
      }
    ]
  }
}

// ========== 5xx エラー率アラート ==========
resource alertHighErrorRate 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = {
  name: 'alert-${prefix}-5xx-rate'
  location: location
  properties: {
    description: '5xx エラー率が 10% を超えた場合'
    severity: 1
    enabled: true
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    scopes: [logAnalyticsWorkspaceId]
    criteria: {
      allOf: [
        {
          query: '''
            ContainerAppConsoleLogs_CL
            | where StatusCode_d >= 500
            | summarize ErrorCount = count() by bin(TimeGenerated, 5m)
            | where ErrorCount > 10
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [actionGroup.id]
    }
  }
}

// ========== PostgreSQL CPU アラート ==========
resource alertPostgresCpu 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'alert-${prefix}-postgres-cpu'
  location: 'global'
  properties: {
    description: 'PostgreSQL CPU が 80% を超過'
    severity: 2
    enabled: true
    scopes: [resourceGroup().id]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.MultipleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'CpuPercent'
          metricName: 'cpu_percent'
          metricNamespace: 'Microsoft.DBforPostgreSQL/flexibleServers'
          operator: 'GreaterThan'
          threshold: 80
          timeAggregation: 'Average'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroup.id
      }
    ]
  }
}
