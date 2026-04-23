// 实时健康数据处理器
// 处理来自各种设备的实时健康数据流

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false
        }
      }
    )

    const { action, user_id, device_data, data_type } = await req.json()

    switch (action) {
      case 'process_raw_data':
        return await processRawHealthData(supabase, user_id, device_data, data_type)
      case 'real_time_analysis':
        return await performRealTimeAnalysis(supabase, user_id, device_data)
      case 'data_fusion':
        return await performDataFusion(supabase, user_id, device_data)
      case 'anomaly_detection':
        return await detectAnomaliesInRealTime(supabase, user_id, device_data)
      case 'update_trends':
        return await updateHealthTrends(supabase, user_id, device_data)
      default:
        throw new Error('Invalid action')
    }

  } catch (error) {
    console.error('Real-time processing error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Real-time processing failed',
        message: error.message 
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})

async function processRawHealthData(supabase: any, userId: string, deviceData: any, dataType: string) {
  // 数据质量评估
  const qualityScore = assessDataQuality(deviceData, dataType)
  
  // 数据预处理
  const processedData = preprocessHealthData(deviceData, dataType)
  
  // 存储原始数据
  const { data: rawDataResult, error: rawError } = await supabase
    .from('health_data_raw')
    .insert({
      user_id: userId,
      data_type: getDataTypeId(supabase, dataType),
      device_type: deviceData.device_type,
      device_id: deviceData.device_id,
      value: deviceData.value,
      unit: deviceData.unit,
      timestamp: deviceData.timestamp,
      location_data: deviceData.location || null,
      metadata: deviceData.metadata || null,
      data_quality_score: qualityScore
    })
    .select()

  if (rawError) throw rawError

  // 存储处理后的数据
  const { data: processedResult, error: processedError } = await supabase
    .from('health_data_processed')
    .insert({
      user_id: userId,
      data_type: dataType,
      processed_value: processedData,
      quality_score: qualityScore,
      analysis_features: extractFeatures(deviceData, dataType),
      timestamp: deviceData.timestamp
    })
    .select()

  if (processedError) throw processedError

  // 触发实时分析
  const analysisResults = await performQuickAnalysis(supabase, userId, processedData, dataType)
  
  // 检查是否需要生成预警
  const alerts = checkForAlerts(processedData, analysisResults, dataType)
  
  if (alerts.length > 0) {
    await createRealTimeAlerts(supabase, userId, alerts)
  }

  return new Response(
    JSON.stringify({ 
      success: true,
      raw_data_id: rawDataResult[0].id,
      processed_data_id: processedResult[0].id,
      quality_score: qualityScore,
      alerts_generated: alerts.length,
      quick_analysis: analysisResults
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
}

async function performRealTimeAnalysis(supabase: any, userId: string, deviceData: any) {
  // 获取最近的数据用于分析
  const { data: recentData } = await supabase
    .from('health_data_processed')
    .select('*')
    .eq('user_id', userId)
    .eq('data_type', deviceData.data_type)
    .order('timestamp', { ascending: false })
    .limit(50)

  if (!recentData || recentData.length < 5) {
    return new Response(
      JSON.stringify({ message: 'Insufficient data for analysis' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  // 执行不同类型的分析
  let analysisResults = {}
  
  switch (deviceData.data_type) {
    case 'heart_rate':
      analysisResults = await analyzeHeartRatePattern(recentData, deviceData)
      break
    case 'activity_level':
      analysisResults = await analyzeActivityPattern(recentData, deviceData)
      break
    case 'sleep_quality':
      analysisResults = await analyzeSleepPattern(recentData, deviceData)
      break
    case 'blood_pressure':
      analysisResults = await analyzeBloodPressurePattern(recentData, deviceData)
      break
  }

  return new Response(
    JSON.stringify({ 
      success: true,
      analysis_type: deviceData.data_type,
      results: analysisResults,
      data_points_analyzed: recentData.length
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
}

async function performDataFusion(supabase: any, userId: string, deviceData: any) {
  // 获取多种设备数据
  const { data: wearableData } = await supabase
    .from('health_data_processed')
    .select('*')
    .eq('user_id', userId)
    .eq('data_type', 'heart_rate')
    .gte('timestamp', new Date(Date.now() - 60000).toISOString()) // 最近1分钟
    .order('timestamp', { ascending: false })

  const { data: activityData } = await supabase
    .from('health_data_processed')
    .select('*')
    .eq('user_id', userId)
    .eq('data_type', 'activity_level')
    .gte('timestamp', new Date(Date.now() - 60000).toISOString())
    .order('timestamp', { ascending: false })

  const { data: environmentalData } = await supabase
    .from('health_data_processed')
    .select('*')
    .eq('user_id', userId)
    .eq('data_type', 'temperature')
    .gte('timestamp', new Date(Date.now() - 300000).toISOString()) // 最近5分钟
    .order('timestamp', { ascending: false })

  // 数据融合
  const fusedData = performMultimodalFusion(wearableData, activityData, environmentalData, deviceData)
  
  // 计算置信度
  const confidenceScore = calculateFusionConfidence(wearableData, activityData, environmentalData, deviceData)
  
  // 生成融合洞察
  const insights = generateFusionInsights(fusedData, confidenceScore)

  return new Response(
    JSON.stringify({ 
      success: true,
      fused_data: fusedData,
      confidence_score: confidenceScore,
      insights: insights,
      data_sources: {
        wearable: wearableData?.length || 0,
        activity: activityData?.length || 0,
        environmental: environmentalData?.length || 0,
        current_device: 1
      }
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
}

async function detectAnomaliesInRealTime(supabase: any, userId: string, deviceData: any) {
  // 获取历史数据用于基线比较
  const { data: historicalData } = await supabase
    .from('health_data_processed')
    .select('*')
    .eq('user_id', userId)
    .eq('data_type', deviceData.data_type)
    .order('timestamp', { ascending: false })
    .limit(100)

  const anomalies = detectAnomalies(deviceData, historicalData || [])
  
  // 异常严重程度评估
  const severityAssessedAnomalies = anomalies.map(anomaly => ({
    ...anomaly,
    severity: assessAnomalySeverity(anomaly, deviceData),
    confidence: calculateAnomalyConfidence(anomaly, historicalData || [])
  }))

  // 如果检测到高严重度异常，立即生成预警
  const highSeverityAnomalies = severityAssessedAnomalies.filter(a => a.severity === 'high')
  
  if (highSeverityAnomalies.length > 0) {
    await createRealTimeAlerts(supabase, userId, 
      highSeverityAnomalies.map(anomaly => ({
        alert_type: 'anomaly_detection',
        severity: 'high',
        title: `${deviceData.data_type}异常检测`,
        message: `检测到${anomaly.type}，值: ${anomaly.value}`,
        trigger_data: anomaly
      }))
    )
  }

  return new Response(
    JSON.stringify({ 
      success: true,
      anomalies_detected: anomalies.length,
      high_severity_count: highSeverityAnomalies.length,
      anomalies: severityAssessedAnomalies,
      baseline_comparison: {
        historical_mean: calculateHistoricalMean(historicalData || [], deviceData),
        historical_std: calculateHistoricalStd(historicalData || [], deviceData),
        deviation_score: calculateDeviationScore(deviceData, historicalData || [])
      }
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
}

async function updateHealthTrends(supabase: any, userId: string, deviceData: any) {
  // 获取趋势数据
  const { data: trendData } = await supabase
    .from('health_data_processed')
    .select('*')
    .eq('user_id', userId)
    .eq('data_type', deviceData.data_type)
    .gte('timestamp', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()) // 最近24小时
    .order('timestamp', { ascending: true })

  if (!trendData || trendData.length < 5) {
    return new Response(
      JSON.stringify({ message: 'Insufficient data for trend analysis' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  // 计算趋势
  const trend = calculateTrend(trendData)
  
  // 预测下一个值
  const prediction = predictNextValue(trendData, deviceData)
  
  // 检测趋势变化
  const trendChanges = detectTrendChanges(trendData)

  return new Response(
    JSON.stringify({ 
      success: true,
      current_trend: trend,
      prediction: prediction,
      trend_changes: trendChanges,
      data_points: trendData.length,
      analysis_period: '24_hours'
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
}

// 辅助函数
function assessDataQuality(data: any, dataType: string): number {
  let quality = 100
  
  // 检查数据完整性
  if (!data.value || data.value === null || data.value === undefined) {
    quality -= 30
  }
  
  // 检查时间戳合理性
  if (data.timestamp) {
    const timestamp = new Date(data.timestamp)
    const now = new Date()
    const diffHours = Math.abs(now.getTime() - timestamp.getTime()) / (1000 * 60 * 60)
    
    if (diffHours > 24) {
      quality -= 40
    } else if (diffHours > 1) {
      quality -= 10
    }
  }
  
  // 检查数值合理性
  if (data.value) {
    switch (dataType) {
      case 'heart_rate':
        if (data.value < 30 || data.value > 220) quality -= 50
        break
      case 'blood_pressure':
        if (data.value < 50 || data.value > 250) quality -= 50
        break
      case 'temperature':
        if (data.value < 35 || data.value > 42) quality -= 50
        break
      case 'oxygen_saturation':
        if (data.value < 70 || data.value > 100) quality -= 50
        break
    }
  }
  
  return Math.max(0, quality)
}

function preprocessHealthData(data: any, dataType: string) {
  const processed = { ...data }
  
  switch (dataType) {
    case 'heart_rate':
      // 心率平滑处理
      processed.value = Math.round(processed.value)
      break
    case 'activity_level':
      // 活动水平标准化
      processed.value = Math.max(0, Math.min(100, processed.value))
      break
    case 'sleep_quality':
      // 睡眠质量评分调整
      processed.value = Math.max(0, Math.min(100, processed.value))
      break
  }
  
  return processed
}

function extractFeatures(data: any, dataType: string) {
  const features = {}
  
  switch (dataType) {
    case 'heart_rate':
      features.current_value = data.value
      features.time_of_day = new Date(data.timestamp).getHours()
      break
    case 'activity_level':
      features.activity_intensity = classifyActivityIntensity(data.value)
      features.duration = data.duration || 0
      break
    case 'sleep_quality':
      features.sleep_duration = data.sleep_duration
      features.sleep_efficiency = data.efficiency
      break
  }
  
  return features
}

function classifyActivityIntensity(value: number): string {
  if (value < 20) return 'low'
  if (value < 50) return 'moderate'
  if (value < 80) return 'high'
  return 'very_high'
}

async function getDataTypeId(supabase: any, typeName: string): Promise<string> {
  const { data } = await supabase
    .from('health_data_types')
    .select('id')
    .eq('type_name', typeName)
    .single()
  
  return data?.id || ''
}

async function performQuickAnalysis(supabase: any, userId: string, processedData: any, dataType: string) {
  // 获取最近的相似数据进行快速分析
  const { data: recentData } = await supabase
    .from('health_data_processed')
    .select('*')
    .eq('user_id', userId)
    .eq('data_type', dataType)
    .order('timestamp', { ascending: false })
    .limit(10)

  if (!recentData || recentData.length < 2) {
    return { status: 'insufficient_data' }
  }

  const values = recentData.map(d => d.processed_value?.value || 0)
  const currentValue = processedData.value
  
  // 计算变化率
  const recentMean = values.reduce((sum, val) => sum + val, 0) / values.length
  const changeRate = ((currentValue - recentMean) / recentMean) * 100
  
  // 检测突然变化
  const suddenChange = Math.abs(changeRate) > 20
  
  return {
    change_rate: changeRate,
    sudden_change: suddenChange,
    recent_trend: changeRate > 5 ? 'increasing' : changeRate < -5 ? 'decreasing' : 'stable'
  }
}

function checkForAlerts(processedData: any, analysisResults: any, dataType: string) {
  const alerts = []
  
  // 基于快速分析结果生成预警
  if (analysisResults.sudden_change) {
    alerts.push({
      alert_type: 'sudden_change',
      severity: 'medium',
      title: `${dataType}突然变化`,
      message: `${dataType}值突然变化 ${analysisResults.change_rate.toFixed(1)}%`,
      trigger_data: {
        data_type: dataType,
        current_value: processedData.value,
        change_rate: analysisResults.change_rate
      }
    })
  }
  
  // 基于阈值检查
  switch (dataType) {
    case 'heart_rate':
      if (processedData.value > 120) {
        alerts.push({
          alert_type: 'tachycardia',
          severity: 'high',
          title: '心动过速',
          message: `心率过高: ${processedData.value} bpm`,
          trigger_data: { heart_rate: processedData.value }
        })
      } else if (processedData.value < 50) {
        alerts.push({
          alert_type: 'bradycardia',
          severity: 'high',
          title: '心动过缓',
          message: `心率过低: ${processedData.value} bpm`,
          trigger_data: { heart_rate: processedData.value }
        })
      }
      break
    case 'temperature':
      if (processedData.value > 38.0) {
        alerts.push({
          alert_type: 'fever',
          severity: 'high',
          title: '发热',
          message: `体温异常: ${processedData.value}°C`,
          trigger_data: { temperature: processedData.value }
        })
      } else if (processedData.value < 36.0) {
        alerts.push({
          alert_type: 'hypothermia',
          severity: 'medium',
          title: '体温过低',
          message: `体温偏低: ${processedData.value}°C`,
          trigger_data: { temperature: processedData.value }
        })
      }
      break
  }
  
  return alerts
}

async function createRealTimeAlerts(supabase: any, userId: string, alerts: any[]) {
  if (alerts.length === 0) return
  
  const { error } = await supabase
    .from('health_alerts')
    .insert(
      alerts.map(alert => ({
        user_id: userId,
        alert_type: alert.alert_type,
        severity: alert.severity,
        title: alert.title,
        message: alert.message,
        trigger_data: alert.trigger_data
      }))
    )
  
  if (error) {
    console.error('Failed to create real-time alerts:', error)
  }
}

// 分析函数
async function analyzeHeartRatePattern(recentData: any[], currentData: any) {
  const heartRates = recentData.map(d => d.processed_value?.value || 0)
  const currentHR = currentData.value
  
  const analysis = {
    current_value: currentHR,
    average: heartRates.reduce((sum, hr) => sum + hr, 0) / heartRates.length,
    variability: calculateVariability(heartRates),
    trend: calculateCurrentTrend(heartRates),
    irregularity: detectHeartRateIrregularity(heartRates, currentHR)
  }
  
  return analysis
}

async function analyzeActivityPattern(recentData: any[], currentData: any) {
  const activities = recentData.map(d => d.processed_value?.value || 0)
  
  const analysis = {
    current_level: currentData.value,
    average_level: activities.reduce((sum, act) => sum + act, 0) / activities.length,
    activity_distribution: calculateActivityDistribution(activities),
    peak_periods: identifyPeakPeriods(activities),
    sedentary_periods: identifySedentaryPeriods(activities)
  }
  
  return analysis
}

async function analyzeSleepPattern(recentData: any[], currentData: any) {
  const sleepScores = recentData.map(d => d.processed_value?.value || 0)
  
  const analysis = {
    current_score: currentData.value,
    average_score: sleepScores.reduce((sum, score) => sum + score, 0) / sleepScores.length,
    consistency: calculateSleepConsistency(sleepScores),
    quality_trend: calculateQualityTrend(sleepScores)
  }
  
  return analysis
}

async function analyzeBloodPressurePattern(recentData: any[], currentData: any) {
  const bpReadings = recentData.map(d => d.processed_value?.value || 0)
  
  const analysis = {
    current_value: currentData.value,
    average_value: bpReadings.reduce((sum, bp) => sum + bp, 0) / bpReadings.length,
    variability: calculateBPVariability(bpReadings),
    hypertension_risk: assessHypertensionRisk(currentData.value, bpReadings)
  }
  
  return analysis
}

// 数据融合函数
function performMultimodalFusion(wearableData: any[], activityData: any[], environmentalData: any[], currentData: any) {
  const fusion = {
    physiological_status: {},
    behavioral_pattern: {},
    environmental_influence: {},
    confidence_score: 0
  }
  
  // 生理状态融合
  if (wearableData.length > 0) {
    fusion.physiological_status = {
      heart_rate: wearableData[0]?.processed_value?.value,
      activity_level: activityData[0]?.processed_value?.value,
      timestamp: new Date().toISOString()
    }
  }
  
  // 环境因素影响
  if (environmentalData.length > 0) {
    fusion.environmental_influence = {
      temperature: environmentalData[0]?.processed_value?.value,
      impact_on_physiology: assessEnvironmentalImpact(environmentalData[0]?.processed_value?.value, fusion.physiological_status)
    }
  }
  
  return fusion
}

function calculateFusionConfidence(wearableData: any[], activityData: any[], environmentalData: any[], currentData: any): number {
  let confidence = 0
  let sources = 0
  
  if (wearableData.length > 0) {
    confidence += 0.4
    sources++
  }
  
  if (activityData.length > 0) {
    confidence += 0.3
    sources++
  }
  
  if (environmentalData.length > 0) {
    confidence += 0.3
    sources++
  }
  
  // 考虑数据质量
  if (sources > 0) {
    confidence = confidence * Math.min(sources / 3, 1)
  }
  
  return Math.round(confidence * 100) / 100
}

function generateFusionInsights(fusedData: any, confidenceScore: number) {
  const insights = []
  
  if (fusedData.physiological_status?.heart_rate && fusedData.physiological_status?.activity_level) {
    const hr = fusedData.physiological_status.heart_rate
    const activity = fusedData.physiological_status.activity_level
    
    if (activity > 70 && hr < 90) {
      insights.push('低心率配合高活动，可能是良好的心血管健康状态')
    } else if (activity > 70 && hr > 120) {
      insights.push('高活动对应高心率，心血管系统反应正常')
    }
  }
  
  if (fusedData.environmental_influence?.temperature) {
    const temp = fusedData.environmental_influence.temperature
    if (temp < 18 || temp > 26) {
      insights.push('环境温度可能影响生理指标')
    }
  }
  
  return {
    insights: insights,
    confidence: confidenceScore,
    data_sources_count: Object.keys(fusedData).filter(key => key !== 'confidence_score').length
  }
}

// 异常检测函数
function detectAnomalies(currentData: any, historicalData: any[]) {
  if (historicalData.length < 5) {
    return []
  }
  
  const anomalies = []
  const currentValue = currentData.value
  const historicalValues = historicalData.map(d => d.processed_value?.value || 0)
  
  // 统计异常检测
  const mean = historicalValues.reduce((sum, val) => sum + val, 0) / historicalValues.length
  const std = Math.sqrt(
    historicalValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / historicalValues.length
  )
  
  const zScore = Math.abs((currentValue - mean) / std)
  
  if (zScore > 2) {
    anomalies.push({
      type: 'statistical_anomaly',
      value: currentValue,
      expected_range: [mean - 2 * std, mean + 2 * std],
      z_score: zScore,
      deviation_from_mean: currentValue - mean
    })
  }
  
  // 连续性异常检测
  const recentValues = historicalValues.slice(0, 5)
  if (recentValues.length >= 2) {
    const consecutiveChanges = Math.abs(currentValue - recentValues[0]) > std * 1.5
    if (consecutiveChanges) {
      anomalies.push({
        type: 'sudden_change',
        value: currentValue,
        previous_value: recentValues[0],
        change_magnitude: Math.abs(currentValue - recentValues[0])
      })
    }
  }
  
  return anomalies
}

function assessAnomalySeverity(anomaly: any, currentData: any): string {
  const dataType = currentData.data_type
  
  switch (dataType) {
    case 'heart_rate':
      if (anomaly.value < 40 || anomaly.value > 180) return 'critical'
      if (anomaly.z_score > 3) return 'high'
      break
    case 'blood_pressure':
      if (anomaly.value > 180 || anomaly.value < 80) return 'critical'
      if (anomaly.z_score > 3) return 'high'
      break
    case 'temperature':
      if (anomaly.value > 39 || anomaly.value < 35) return 'high'
      if (anomaly.z_score > 3) return 'medium'
      break
  }
  
  return anomaly.z_score > 3 ? 'high' : 'medium'
}

function calculateAnomalyConfidence(anomaly: any, historicalData: any[]): number {
  if (historicalData.length < 10) return 0.5
  
  return Math.min(0.95, 0.5 + (anomaly.z_score / 6) * 0.45)
}

// 计算函数
function calculateVariability(values: number[]): number {
  if (values.length < 2) return 0
  const mean = values.reduce((sum, val) => sum + val, 0) / values.length
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
  return Math.sqrt(variance)
}

function calculateCurrentTrend(values: number[]): string {
  if (values.length < 3) return 'stable'
  
  const n = values.length
  const recent = values.slice(-3)
  const earlier = values.slice(-6, -3)
  
  const recentAvg = recent.reduce((sum, val) => sum + val, 0) / recent.length
  const earlierAvg = earlier.reduce((sum, val) => sum + val, 0) / earlier.length
  
  const changePercent = ((recentAvg - earlierAvg) / earlierAvg) * 100
  
  if (changePercent > 5) return 'increasing'
  if (changePercent < -5) return 'decreasing'
  return 'stable'
}

function detectHeartRateIrregularity(heartRates: number[], currentHR: number): boolean {
  if (heartRates.length < 5) return false
  
  const differences = []
  for (let i = 1; i < heartRates.length; i++) {
    differences.push(Math.abs(heartRates[i] - heartRates[i-1]))
  }
  
  const avgDifference = differences.reduce((sum, diff) => sum + diff, 0) / differences.length
  const currentDifference = Math.abs(currentHR - heartRates[heartRates.length - 1])
  
  return currentDifference > avgDifference * 2
}

function calculateActivityDistribution(values: number[]): any {
  const ranges = {
    low: values.filter(v => v < 20).length,
    moderate: values.filter(v => v >= 20 && v < 50).length,
    high: values.filter(v => v >= 50 && v < 80).length,
    very_high: values.filter(v => v >= 80).length
  }
  
  const total = values.length
  return {
    low: (ranges.low / total) * 100,
    moderate: (ranges.moderate / total) * 100,
    high: (ranges.high / total) * 100,
    very_high: (ranges.very_high / total) * 100
  }
}

function identifyPeakPeriods(values: number[]): number[] {
  const peaks = []
  const threshold = Math.max(...values) * 0.8
  
  for (let i = 1; i < values.length - 1; i++) {
    if (values[i] > threshold && values[i] > values[i-1] && values[i] > values[i+1]) {
      peaks.push(i)
    }
  }
  
  return peaks
}

function identifySedentaryPeriods(values: number[]): number[] {
  const sedentary = []
  const threshold = 10
  
  for (let i = 0; i < values.length; i++) {
    if (values[i] < threshold) {
      sedentary.push(i)
    }
  }
  
  return sedentary
}

function calculateSleepConsistency(sleepScores: number[]): number {
  if (sleepScores.length < 7) return 0
  
  const recentScores = sleepScores.slice(-7)
  const mean = recentScores.reduce((sum, score) => sum + score, 0) / recentScores.length
  const variance = recentScores.reduce((sum, score) => sum + Math.pow(score - mean, 2), 0) / recentScores.length
  
  return Math.max(0, 1 - (variance / 100))
}

function calculateQualityTrend(sleepScores: number[]): string {
  if (sleepScores.length < 3) return 'stable'
  
  const n = sleepScores.length
  const trend = (sleepScores[n-1] - sleepScores[0]) / n
  
  if (trend > 1) return 'improving'
  if (trend < -1) return 'declining'
  return 'stable'
}

function calculateBPVariability(bpReadings: number[]): number {
  return calculateVariability(bpReadings)
}

function assessHypertensionRisk(currentBP: number, historicalBPs: number[]): string {
  if (currentBP > 140) return 'high'
  if (currentBP > 130) return 'medium'
  if (historicalBPs.length > 5 && historicalBPs.slice(-5).some(bp => bp > 130)) return 'medium'
  return 'low'
}

function assessEnvironmentalImpact(temperature: number, physiologicalStatus: any): string {
  if (!physiologicalStatus) return 'unknown'
  
  const hr = physiologicalStatus.heart_rate
  if (!hr) return 'unknown'
  
  if (temperature < 18 && hr < 60) return 'possible_hypothermia'
  if (temperature > 30 && hr > 100) return 'possible_heat_stress'
  
  return 'normal'
}

function calculateHistoricalMean(historicalData: any[], currentData: any): number {
  if (historicalData.length === 0) return currentData.value
  
  const values = historicalData.map(d => d.processed_value?.value || 0)
  return values.reduce((sum, val) => sum + val, 0) / values.length
}

function calculateHistoricalStd(historicalData: any[], currentData: any): number {
  if (historicalData.length === 0) return 0
  
  const values = historicalData.map(d => d.processed_value?.value || 0)
  return calculateVariability(values)
}

function calculateDeviationScore(currentData: any, historicalData: any[]): number {
  if (historicalData.length === 0) return 0
  
  const mean = calculateHistoricalMean(historicalData, currentData)
  const std = calculateHistoricalStd(historicalData, currentData)
  
  return std > 0 ? Math.abs((currentData.value - mean) / std) : 0
}

function calculateTrend(data: any[]) {
  if (data.length < 2) return 'insufficient_data'
  
  const values = data.map(d => d.processed_value?.value || 0)
  const x = Array.from({ length: values.length }, (_, i) => i)
  
  const n = x.length
  const sumX = x.reduce((sum, val) => sum + val, 0)
  const sumY = values.reduce((sum, val) => sum + val, 0)
  const sumXY = x.reduce((sum, val, i) => sum + val * values[i], 0)
  const sumXX = x.reduce((sum, val) => sum + val * val, 0)
  
  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)
  
  if (slope > 0.5) return 'increasing'
  if (slope < -0.5) return 'decreasing'
  return 'stable'
}

function predictNextValue(data: any[], currentData: any) {
  const values = data.map(d => d.processed_value?.value || 0)
  values.push(currentData.value)
  
  const trend = calculateTrend(data)
  const lastValue = values[values.length - 1]
  
  let prediction = lastValue
  switch (trend) {
    case 'increasing':
      prediction = lastValue + (values[values.length - 1] - values[0]) / data.length
      break
    case 'decreasing':
      prediction = lastValue - (values[0] - values[values.length - 1]) / data.length
      break
    default:
      prediction = lastValue
  }
  
  return {
    predicted_value: prediction,
    confidence: 0.7,
    trend_direction: trend
  }
}

function detectTrendChanges(data: any[]) {
  if (data.length < 6) return []
  
  const values = data.map(d => d.processed_value?.value || 0)
  const changes = []
  
  for (let i = 2; i < values.length - 2; i++) {
    const before = values[i-2] + values[i-1]
    const after = values[i+1] + values[i+2]
    const change = Math.abs(after - before) / Math.max(before, after)
    
    if (change > 0.2) {
      changes.push({
        position: i,
        change_magnitude: change,
        direction: after > before ? 'upward' : 'downward'
      })
    }
  }
  
  return changes
}
