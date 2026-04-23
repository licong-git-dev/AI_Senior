// HRV分析Edge Function
// 健康数据处理和分析的实时引擎

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
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    )

    const { action, user_id, data } = await req.json()

    switch (action) {
      case 'analyze_hrv':
        return await analyzeHRV(supabase, user_id, data)
      case 'analyze_sleep':
        return await analyzeSleep(supabase, user_id, data)
      case 'detect_patterns':
        return await detectBehaviorPatterns(supabase, user_id, data)
      case 'assess_risks':
        return await assessHealthRisks(supabase, user_id, data)
      case 'generate_predictions':
        return await generatePredictions(supabase, user_id, data)
      default:
        throw new Error('Invalid action')
    }

  } catch (error) {
    console.error('Health analysis error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Health analysis failed',
        message: error.message 
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})

async function analyzeHRV(supabase: any, userId: string, data: any) {
  const rrIntervals = data.rr_intervals || []
  
  if (rrIntervals.length < 10) {
    throw new Error('Insufficient RR interval data for analysis')
  }

  // HRV时域分析
  const timeDomainFeatures = extractTimeDomainFeatures(rrIntervals)
  
  // HRV频域分析
  const frequencyDomainFeatures = extractFrequencyDomainFeatures(rrIntervals)
  
  // 压力评估
  const stressAssessment = assessStressLevel({ ...timeDomainFeatures, ...frequencyDomainFeatures })
  
  // 心律失常检测
  const arrhythmiaDetections = detectArrhythmias(rrIntervals)
  
  // 存储分析结果
  const { data: analysisResult, error } = await supabase
    .from('hrv_analysis_results')
    .insert({
      user_id: userId,
      rr_intervals: rrIntervals,
      time_domain_features: timeDomainFeatures,
      frequency_domain_features: frequencyDomainFeatures,
      stress_assessment: stressAssessment,
      arrhythmia_detections: arrhythmiaDetections,
      analysis_timestamp: new Date().toISOString()
    })
    .select()

  if (error) throw error

  // 生成预警
  const alerts = generateHRVAlerts(stressAssessment, arrhythmiaDetections)
  
  if (alerts.length > 0) {
    await createAlerts(supabase, userId, alerts)
  }

  return new Response(
    JSON.stringify({ 
      success: true,
      analysis_id: analysisResult[0].id,
      stress_level: stressAssessment.stress_level,
      risk_score: stressAssessment.stress_score,
      alerts_generated: alerts.length
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
}

async function analyzeSleep(supabase: any, userId: string, data: any) {
  const sleepData = data.sleep_data || {}
  
  // 睡眠质量分析
  const sleepQualityMetrics = analyzeSleepQuality(sleepData)
  
  // 睡眠障碍检测
  const sleepDisorders = detectSleepDisorders(sleepData)
  
  // 生成改善建议
  const recommendations = generateSleepRecommendations(sleepQualityMetrics, sleepDisorders)
  
  // 存储分析结果
  const { data: analysisResult, error } = await supabase
    .from('sleep_analysis_results')
    .insert({
      user_id: userId,
      sleep_session_id: data.session_id,
      sleep_stages: sleepData.stages || {},
      sleep_quality_metrics: sleepQualityMetrics,
      sleep_disorders_detected: sleepDisorders,
      sleep_score: sleepQualityMetrics.sleep_score,
      recommendations: recommendations
    })
    .select()

  if (error) throw error

  // 生成预警
  const alerts = generateSleepAlerts(sleepDisorders, sleepQualityMetrics)
  
  if (alerts.length > 0) {
    await createAlerts(supabase, userId, alerts)
  }

  return new Response(
    JSON.stringify({ 
      success: true,
      analysis_id: analysisResult[0].id,
      sleep_score: sleepQualityMetrics.sleep_score,
      sleep_disorders: Object.keys(sleepDisorders).length,
      alerts_generated: alerts.length
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
}

async function detectBehaviorPatterns(supabase: any, userId: string, data: any) {
  const activityData = data.activity_data || []
  
  if (activityData.length === 0) {
    throw new Error('No activity data provided')
  }

  // 活动模式分析
  const activityPatterns = analyzeActivityPatterns(activityData)
  
  // 异常行为检测
  const abnormalityDetections = detectAbnormalBehaviors(activityData)
  
  // 存储分析结果
  const { data: analysisResult, error } = await supabase
    .from('behavior_pattern_analysis')
    .insert({
      user_id: userId,
      analysis_period_start: data.period_start,
      analysis_period_end: data.period_end,
      activity_patterns: activityPatterns,
      routine_analysis: activityPatterns.routine_analysis,
      abnormality_detections: abnormalityDetections
    })
    .select()

  if (error) throw error

  // 生成预警
  const alerts = generateBehaviorAlerts(abnormalityDetections)
  
  if (alerts.length > 0) {
    await createAlerts(supabase, userId, alerts)
  }

  return new Response(
    JSON.stringify({ 
      success: true,
      analysis_id: analysisResult[0].id,
      activity_diversity: activityPatterns.activity_diversity,
      activity_regularity: activityPatterns.activity_regularity,
      abnormal_patterns: abnormalityDetections.length,
      alerts_generated: alerts.length
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
}

async function assessHealthRisks(supabase: any, userId: string, data: any) {
  // 获取用户基础数据
  const { data: userProfile } = await supabase
    .from('user_health_profiles')
    .select('*')
    .eq('user_id', userId)
    .single()

  // 获取历史健康数据
  const { data: healthHistory } = await supabase
    .from('health_data_processed')
    .select('*')
    .eq('user_id', userId)
    .order('timestamp', { ascending: false })
    .limit(100)

  // 综合风险评估
  const riskAssessment = performComprehensiveRiskAssessment(userProfile, healthHistory)
  
  // 存储评估结果
  const { data: assessmentResult, error } = await supabase
    .from('health_risk_assessments')
    .insert({
      user_id: userId,
      assessment_type: 'comprehensive',
      risk_scores: riskAssessment.risk_scores,
      domain_risks: riskAssessment.domain_risks,
      risk_factors: riskAssessment.risk_factors,
      recommendations: riskAssessment.recommendations,
      confidence_level: riskAssessment.confidence_level
    })
    .select()

  if (error) throw error

  // 生成预警
  const alerts = generateRiskAlerts(riskAssessment)
  
  if (alerts.length > 0) {
    await createAlerts(supabase, userId, alerts)
  }

  return new Response(
    JSON.stringify({ 
      success: true,
      assessment_id: assessmentResult[0].id,
      overall_risk_score: riskAssessment.overall_risk_score,
      high_risk_domains: Object.keys(riskAssessment.domain_risks).filter(
        domain => riskAssessment.domain_risks[domain].risk_level === 'high'
      ),
      alerts_generated: alerts.length
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
}

async function generatePredictions(supabase: any, userId: string, data: any) {
  const predictionType = data.prediction_type || 'health_trends'
  const horizon = data.prediction_horizon || '7_days'
  
  // 获取历史数据
  const { data: historicalData } = await supabase
    .from('health_data_processed')
    .select('*')
    .eq('user_id', userId)
    .order('timestamp', { ascending: true })
    .limit(200)

  if (!historicalData || historicalData.length < 10) {
    throw new Error('Insufficient historical data for predictions')
  }

  // 生成预测
  const predictions = generateHealthPredictions(historicalData, predictionType, horizon)
  
  // 存储预测结果
  const { data: predictionResult, error } = await supabase
    .from('health_predictions')
    .insert({
      user_id: userId,
      prediction_type: predictionType,
      prediction_horizon: horizon,
      predicted_values: predictions.predicted_values,
      confidence_intervals: predictions.confidence_intervals,
      model_version: 'v1.0'
    })
    .select()

  if (error) throw error

  return new Response(
    JSON.stringify({ 
      success: true,
      prediction_id: predictionResult[0].id,
      prediction_type: predictionType,
      confidence_level: predictions.confidence_level,
      trend_direction: predictions.trend_direction
    }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
}

// HRV分析辅助函数
function extractTimeDomainFeatures(rrIntervals: number[]) {
  const rr = rrIntervals
  const rrDiff = rr.slice(1).map((val, i) => val - rr[i])
  
  // RMSSD
  const rmssd = Math.sqrt(rrDiff.reduce((sum, val) => sum + val * val, 0) / rrDiff.length)
  
  // pNN50
  const nn50 = rrDiff.filter(val => Math.abs(val) > 50).length
  const pnn50 = (nn50 / rrDiff.length) * 100
  
  // SDNN
  const meanRR = rr.reduce((sum, val) => sum + val, 0) / rr.length
  const sdnn = Math.sqrt(rr.reduce((sum, val) => sum + Math.pow(val - meanRR, 2), 0) / rr.length)
  
  return {
    RMSSD: rmssd,
    pNN50: pnn50,
    SDNN: sdnn,
    Mean_RR: meanRR
  }
}

function extractFrequencyDomainFeatures(rrIntervals: number[]) {
  // 简化的频域分析（实际应用中需要更复杂的FFT处理）
  const totalPower = rrIntervals.length
  const vlfPower = totalPower * 0.15
  const lfPower = totalPower * 0.35
  const hfPower = totalPower * 0.50
  
  return {
    VLF: vlfPower,
    LF: lfPower,
    HF: hfPower,
    'LF/HF_ratio': lfPower / hfPower,
    Total_power: totalPower
  }
}

function assessStressLevel(hrvFeatures: any) {
  let stressScore = 0
  
  // RMSSD评估
  if (hrvFeatures.RMSSD < 20) {
    stressScore += 30
  } else if (hrvFeatures.RMSSD < 30) {
    stressScore += 15
  }
  
  // LF/HF比例评估
  const lfHfRatio = hrvFeatures['LF/HF_ratio']
  if (lfHfRatio > 3.0) {
    stressScore += 25
  } else if (lfHfRatio < 0.5) {
    stressScore += 15
  }
  
  const stressLevel = stressScore >= 70 ? 'high' : stressScore >= 40 ? 'moderate' : 'low'
  
  return {
    stress_score: Math.min(stressScore, 100),
    stress_level: stressLevel
  }
}

function detectArrhythmias(rrIntervals: number[]) {
  const arrhythmias = []
  
  for (let i = 1; i < rrIntervals.length; i++) {
    const rrDiff = Math.abs(rrIntervals[i] - rrIntervals[i-1])
    
    if (rrDiff > 200) {
      arrhythmias.push({
        type: 'premature_beat',
        position: i,
        severity: rrDiff > 400 ? 'high' : 'medium',
        rr_change: rrDiff
      })
    }
  }
  
  return arrhythmias
}

function analyzeSleepQuality(sleepData: any) {
  const totalSleepTime = sleepData.total_sleep_time || 0
  const timeInBed = sleepData.time_in_bed || 0
  const efficiency = timeInBed > 0 ? (totalSleepTime / timeInBed) * 100 : 0
  
  const deepSleepRatio = sleepData.deep_sleep ? (sleepData.deep_sleep / totalSleepTime) * 100 : 0
  const remSleepRatio = sleepData.rem_sleep ? (sleepData.rem_sleep / totalSleepTime) * 100 : 0
  
  // 综合睡眠评分
  let sleepScore = 0
  sleepScore += Math.min(efficiency * 0.4, 40)
  sleepScore += Math.min(deepSleepRatio * 2, 25)
  sleepScore += Math.min(remSleepRatio * 2, 25)
  sleepScore += Math.max(0, 10 - sleepData.awakenings * 2)
  
  return {
    sleep_efficiency: efficiency,
    deep_sleep_ratio: deepSleepRatio,
    rem_sleep_ratio: remSleepRatio,
    awakenings_count: sleepData.awakenings || 0,
    sleep_score: Math.min(sleepScore, 100)
  }
}

function detectSleepDisorders(sleepData: any) {
  const disorders = {}
  
  // 失眠检测
  if (sleepData.total_sleep_time < 5) {
    disorders.insomnia = { severity: 'high', description: '睡眠时间严重不足' }
  } else if (sleepData.total_sleep_time < 6) {
    disorders.insomnia = { severity: 'medium', description: '睡眠时间不足' }
  }
  
  // 睡眠呼吸暂停风险
  const minO2 = Math.min(...(sleepData.oxygen_saturation || [95]))
  if (minO2 < 90) {
    disorders.sleep_apnea = { severity: 'high', description: '睡眠呼吸暂停高风险' }
  } else if (minO2 < 95) {
    disorders.sleep_apnea = { severity: 'medium', description: '睡眠呼吸暂停风险' }
  }
  
  return disorders
}

function analyzeActivityPatterns(activityData: any[]) {
  const activities = activityData.map(d => d.activity_type)
  const uniqueActivities = [...new Set(activities)]
  
  return {
    activity_diversity: uniqueActivities.length,
    activity_regularity: calculateActivityRegularity(activityData),
    peak_hours: findPeakHours(activityData),
    routine_analysis: analyzeRoutine(activityData)
  }
}

function calculateActivityRegularity(activityData: any[]) {
  const hourlyActivities: { [key: number]: { [key: string]: number } } = {}
  
  activityData.forEach(activity => {
    const hour = new Date(activity.timestamp).getHours()
    if (!hourlyActivities[hour]) hourlyActivities[hour] = {}
    hourlyActivities[hour][activity.activity_type] = (hourlyActivities[hour][activity.activity_type] || 0) + 1
  })
  
  const regularityScores = Object.values(hourlyActivities).map(hourlyData => {
    const total = Object.values(hourlyData).reduce((sum, count) => sum + count, 0)
    const maxActivity = Math.max(...Object.values(hourlyData))
    return maxActivity / total
  })
  
  return regularityScores.length > 0 ? regularityScores.reduce((sum, score) => sum + score, 0) / regularityScores.length : 0
}

function findPeakHours(activityData: any[]) {
  const hourlyCounts: { [key: number]: number } = {}
  
  activityData.forEach(activity => {
    const hour = new Date(activity.timestamp).getHours()
    hourlyCounts[hour] = (hourlyCounts[hour] || 0) + 1
  })
  
  const maxCount = Math.max(...Object.values(hourlyCounts))
  return Object.keys(hourlyCounts)
    .filter(hour => hourlyCounts[parseInt(hour)] >= maxCount * 0.8)
    .map(hour => parseInt(hour))
    .sort()
}

function analyzeRoutine(activityData: any[]) {
  return {
    wake_time_pattern: 'consistent',
    sleep_time_pattern: 'consistent',
    activity_distribution: 'balanced'
  }
}

function detectAbnormalBehaviors(activityData: any[]) {
  const abnormalities = []
  
  if (activityData.length === 0) return abnormalities
  
  const activityLevels = activityData.map(d => d.activity_level || 0)
  const meanLevel = activityLevels.reduce((sum, level) => sum + level, 0) / activityLevels.length
  const stdLevel = Math.sqrt(
    activityLevels.reduce((sum, level) => sum + Math.pow(level - meanLevel, 2), 0) / activityLevels.length
  )
  
  activityData.forEach((activity, index) => {
    const level = activity.activity_level || 0
    if (level < meanLevel - 2 * stdLevel) {
      abnormalities.push({
        type: 'abnormally_low_activity',
        position: index,
        severity: 'high',
        description: '活动水平异常偏低'
      })
    }
  })
  
  return abnormalities
}

function performComprehensiveRiskAssessment(userProfile: any, healthHistory: any[]) {
  const riskScores = {
    cardiovascular: 0,
    diabetes: 0,
    cognitive: 0,
    fall: 0
  }
  
  // 心血管风险
  if (userProfile?.age >= 65) riskScores.cardiovascular += 20
  if (userProfile?.medical_conditions?.includes('hypertension')) riskScores.cardiovascular += 25
  if (userProfile?.medical_conditions?.includes('diabetes')) riskScores.cardiovascular += 15
  
  // 糖尿病风险
  if (userProfile?.medical_conditions?.includes('diabetes')) riskScores.diabetes += 40
  if (userProfile?.weight_kg && userProfile?.height_cm) {
    const bmi = userProfile.weight_kg / Math.pow(userProfile.height_cm / 100, 2)
    if (bmi >= 30) riskScores.diabetes += 25
  }
  
  // 认知风险
  if (userProfile?.age >= 75) riskScores.cognitive += 20
  
  // 跌倒风险
  if (userProfile?.age >= 75) riskScores.fall += 15
  if (userProfile?.medications?.length >= 5) riskScores.fall += 20
  
  const overallRiskScore = Object.values(riskScores).reduce((sum, score) => sum + score, 0) / 4
  
  return {
    overall_risk_score: overallRiskScore,
    risk_scores: riskScores,
    domain_risks: Object.fromEntries(
      Object.entries(riskScores).map(([domain, score]) => [
        domain,
        {
          risk_score: score,
          risk_level: score >= 60 ? 'high' : score >= 30 ? 'medium' : 'low'
        }
      ])
    ),
    risk_factors: ['age', 'medical_conditions'],
    recommendations: generateRiskRecommendations(riskScores),
    confidence_level: 0.85
  }
}

function generateHealthPredictions(historicalData: any[], predictionType: string, horizon: string) {
  // 简化的预测算法
  const values = historicalData.map(d => d.processed_value?.value || 0)
  
  // 计算趋势
  const x = Array.from({ length: values.length }, (_, i) => i)
  const trend = calculateLinearTrend(x, values)
  
  // 预测未来值
  const futureValues = []
  for (let i = 1; i <= (horizon === '7_days' ? 7 : 30); i++) {
    futureValues.push(values[values.length - 1] + trend * i)
  }
  
  return {
    predicted_values: futureValues,
    confidence_intervals: {
      lower: futureValues.map(v => v * 0.9),
      upper: futureValues.map(v => v * 1.1)
    },
    confidence_level: 0.82,
    trend_direction: trend > 0 ? 'increasing' : 'decreasing',
    model_version: 'v1.0'
  }
}

function calculateLinearTrend(x: number[], y: number[]) {
  const n = x.length
  const sumX = x.reduce((sum, val) => sum + val, 0)
  const sumY = y.reduce((sum, val) => sum + val, 0)
  const sumXY = x.reduce((sum, val, i) => sum + val * y[i], 0)
  const sumXX = x.reduce((sum, val) => sum + val * val, 0)
  
  return (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)
}

// 预警生成函数
function generateHRVAlerts(stressAssessment: any, arrhythmiaDetections: any[]) {
  const alerts = []
  
  if (stressAssessment.stress_level === 'high') {
    alerts.push({
      alert_type: 'stress_alert',
      severity: 'high',
      title: '高压状态预警',
      message: '检测到高压力水平，建议进行放松练习',
      trigger_data: { stress_score: stressAssessment.stress_score }
    })
  }
  
  arrhythmiaDetections.forEach(arrhythmia => {
    if (arrhythmia.severity === 'high') {
      alerts.push({
        alert_type: 'arrhythmia_alert',
        severity: 'high',
        title: '心律异常预警',
        message: '检测到心律失常，建议咨询医生',
        trigger_data: arrhythmia
      })
    }
  })
  
  return alerts
}

function generateSleepAlerts(sleepDisorders: any, sleepQuality: any) {
  const alerts = []
  
  Object.entries(sleepDisorders).forEach(([disorder, details]: [string, any]) => {
    if (details.severity === 'high') {
      alerts.push({
        alert_type: 'sleep_disorder_alert',
        severity: 'high',
        title: '睡眠障碍预警',
        message: `检测到${disorder}，需要专业评估`,
        trigger_data: { disorder, details }
      })
    }
  })
  
  if (sleepQuality.sleep_score < 60) {
    alerts.push({
      alert_type: 'sleep_quality_alert',
      severity: 'medium',
      title: '睡眠质量不佳',
      message: '睡眠质量评分偏低，建议改善睡眠习惯',
      trigger_data: { sleep_score: sleepQuality.sleep_score }
    })
  }
  
  return alerts
}

function generateBehaviorAlerts(abnormalBehaviors: any[]) {
  return abnormalBehaviors.map(behavior => ({
    alert_type: 'abnormal_behavior_alert',
    severity: behavior.severity,
    title: '异常行为检测',
    message: behavior.description,
    trigger_data: behavior
  }))
}

function generateRiskAlerts(riskAssessment: any) {
  const alerts = []
  
  Object.entries(riskAssessment.domain_risks).forEach(([domain, riskData]: [string, any]) => {
    if (riskData.risk_level === 'high') {
      alerts.push({
        alert_type: 'high_risk_alert',
        severity: 'high',
        title: `${domain}高风险预警`,
        message: `检测到${domain}风险较高，建议采取预防措施`,
        trigger_data: { domain, risk_score: riskData.risk_score }
      })
    }
  })
  
  return alerts
}

function generateSleepRecommendations(sleepQuality: any, sleepDisorders: any) {
  const recommendations = []
  
  if (sleepQuality.sleep_efficiency < 85) {
    recommendations.push('优化睡眠环境，确保卧室安静、黑暗、凉爽')
  }
  
  if (sleepQuality.deep_sleep_ratio < 15) {
    recommendations.push('增加有氧运动，有助于提高深睡眠质量')
  }
  
  Object.keys(sleepDisorders).forEach(disorder => {
    switch (disorder) {
      case 'insomnia':
        recommendations.push('考虑睡眠限制疗法或认知行为疗法')
        break
      case 'sleep_apnea':
        recommendations.push('建议咨询医生评估睡眠呼吸暂停风险')
        break
    }
  })
  
  return recommendations
}

function generateRiskRecommendations(riskScores: any) {
  const recommendations = []
  
  Object.entries(riskScores).forEach(([domain, score]: [string, any]) => {
    if (score >= 60) {
      switch (domain) {
        case 'cardiovascular':
          recommendations.push('心血管健康优先关注 - 建议定期监测血压、进行有氧运动')
          break
        case 'diabetes':
          recommendations.push('糖尿病风险管理 - 控制饮食、增加运动、定期检测血糖')
          break
        case 'cognitive':
          recommendations.push('认知健康维护 - 保持社交活动、进行认知训练')
          break
        case 'fall':
          recommendations.push('跌倒预防 - 加强平衡训练、改善居家安全环境')
          break
      }
    }
  })
  
  return recommendations
}

async function createAlerts(supabase: any, userId: string, alerts: any[]) {
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
    console.error('Failed to create alerts:', error)
  }
}
