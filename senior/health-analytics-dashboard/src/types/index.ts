// 数据类型定义

export interface HealthData {
  id: string
  user_id: string
  data_type: string
  value: number
  unit: string
  timestamp: string
  metadata?: any
}

export interface SensorData {
  id: string
  user_id: string
  device_type: string
  data_type: string
  raw_value: any
  processed_value: any
  quality_score: number
  timestamp: string
}

export interface PhysiologicalAnalysis {
  id: string
  user_id: string
  analysis_type: string
  heart_rate_variability: any
  blood_pressure_prediction: any
  sleep_quality_score: number
  respiratory_pattern: any
  anomalies: any[]
  ai_summary: string
  confidence_score: number
  analysis_time: string
}

export interface BehaviorPattern {
  id: string
  user_id: string
  pattern_type: string
  activity_trajectory: any
  abnormal_behaviors: any[]
  cognitive_assessment: any
  social_interaction_score: number
  risk_level: string
  ai_insights: string
  detection_time: string
}

export interface HealthPrediction {
  id: string
  user_id: string
  prediction_type: string
  time_range: string
  predicted_values: any[]
  risk_factors: any[]
  confidence_interval: any[]
  early_warning: any[]
  model_version: string
  accuracy_rate: number
  prediction_time: string
}

export interface ChronicCondition {
  id: string
  user_id: string
  condition_name: string
  diagnosis_date: string
  severity: string
  status: string
  notes: string
}

export interface Medication {
  id: string
  user_id: string
  medication_name: string
  dosage: string
  frequency: string
  start_date: string
  end_date?: string
  adherence_rate: number
}

export interface HealthAlert {
  id: string
  user_id: string
  alert_type: string
  severity: string
  indicator_name: string
  abnormal_value: string
  normal_range?: string
  risk_assessment?: string
  recommended_actions?: string
  notified_contacts?: any
  alert_time: string
  acknowledged: boolean
  resolved: boolean
  resolved_at?: string
  created_at?: string
}

export type UserRole = 'elderly' | 'family' | 'doctor' | 'nurse' | 'admin'

export type TimeRange = '24h' | '7d' | '30d' | '90d'

export type ChartType = 'line' | 'bar' | 'pie' | 'heatmap' | 'scatter'

export interface ChartConfig {
  type: ChartType
  title: string
  dataKey: string
  xAxisKey?: string
  yAxisKey?: string
  colors?: string[]
}

export interface DashboardFilter {
  timeRange: TimeRange
  userId?: string
  metricTypes?: string[]
  severityLevels?: string[]
}
