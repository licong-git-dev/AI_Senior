import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface TrackingRequest {
  interventionId: string;
  userId: string;
  feedbackData: {
    adherence: number;
    satisfaction: number;
    difficulties: string;
    additionalComments: string;
    symptoms?: any;
    measurements?: any;
  };
}

serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
  }

  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    const requestData: TrackingRequest = await req.json();
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    );

    // 1. 更新干预效果数据
    const feedbackRecord = await updateInterventionFeedback(supabase, requestData);
    
    // 2. 分析干预效果
    const effectiveness = await analyzeInterventionEffectiveness(supabase, requestData.interventionId);
    
    // 3. 检查是否需要调整方案
    let planAdjustment = null;
    if (effectiveness.needsAdjustment) {
      planAdjustment = await triggerPlanAdjustment(supabase, requestData.interventionId, effectiveness);
    }
    
    // 4. 生成进展报告
    const progressReport = await generateProgressReport(supabase, requestData.userId, requestData.interventionId);
    
    // 5. 更新干预记录状态
    await updateInterventionStatus(supabase, requestData.interventionId, effectiveness);

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          feedbackRecord,
          effectiveness,
          planAdjustment,
          progressReport,
          nextActions: generateNextActions(effectiveness)
        }
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    );

  } catch (error) {
    console.error('干预跟踪处理错误:', error);
    
    return new Response(
      JSON.stringify({ 
        error: {
          code: 'TRACKING_ERROR',
          message: error.message || '处理干预跟踪时发生未知错误'
        }
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});

// 更新干预反馈
async function updateInterventionFeedback(supabase: any, requestData: TrackingRequest) {
  const { data: feedback, error } = await supabase
    .from('intervention_feedback')
    .insert({
      intervention_id: requestData.interventionId,
      user_id: requestData.userId,
      adherence_score: requestData.feedbackData.adherence,
      satisfaction_score: requestData.feedbackData.satisfaction,
      difficulties: requestData.feedbackData.difficulties,
      additional_comments: requestData.feedbackData.additionalComments,
      created_at: new Date().toISOString()
    })
    .select()
    .single();

  if (error) {
    throw new Error(`保存反馈数据失败: ${error.message}`);
  }

  // 同时更新相关的症状和测量数据
  if (requestData.feedbackData.symptoms) {
    await supabase
      .from('health_records')
      .insert({
        user_id: requestData.userId,
        record_type: 'symptom_log',
        record_value: requestData.feedbackData.symptoms,
        recorded_at: new Date().toISOString(),
        source_device: 'intervention_app'
      });
  }

  if (requestData.feedbackData.measurements) {
    for (const [measurementType, value] of Object.entries(requestData.feedbackData.measurements)) {
      await supabase
        .from('health_records')
        .insert({
          user_id: requestData.userId,
          record_type: measurementType,
          record_value: { value, source: 'intervention_tracking' },
          recorded_at: new Date().toISOString(),
          source_device: 'intervention_app'
        });
    }
  }

  return feedback;
}

// 分析干预效果
async function analyzeInterventionEffectiveness(supabase: any, interventionId: string) {
  // 获取干预记录
  const { data: intervention, error: interventionError } = await supabase
    .from('intervention_records')
    .select('*')
    .eq('id', interventionId)
    .single();

  if (interventionError) {
    throw new Error(`获取干预记录失败: ${interventionError.message}`);
  }

  // 获取所有反馈记录
  const { data: feedbacks, error: feedbackError } = await supabase
    .from('intervention_feedback')
    .select('*')
    .eq('intervention_id', interventionId)
    .order('created_at', { ascending: true });

  if (feedbackError) {
    throw new Error(`获取反馈数据失败: ${feedbackError.message}`);
  }

  // 获取相关健康记录
  const { data: healthRecords, error: healthError } = await supabase
    .from('health_records')
    .select('*')
    .eq('user_id', intervention.user_id)
    .gte('recorded_at', intervention.created_at)
    .order('recorded_at', { ascending: true });

  if (healthError) {
    throw new Error(`获取健康记录失败: ${healthError.message}`);
  }

  // 计算各项效果指标
  const metrics = calculateEffectivenessMetrics(intervention, feedbacks || [], healthRecords || []);
  
  // 判断是否需要调整方案
  const needsAdjustment = determineIfAdjustmentNeeded(metrics, intervention);

  // 生成改进建议
  const improvementSuggestions = generateImprovementSuggestions(metrics, feedbacks || []);

  return {
    ...metrics,
    needsAdjustment,
    improvementSuggestions,
    analysisDate: new Date().toISOString(),
    dataPoints: {
      feedbackCount: feedbacks?.length || 0,
      healthRecordCount: healthRecords?.length || 0,
      timeSpanDays: calculateTimeSpan(intervention.created_at, new Date().toISOString())
    }
  };
}

// 计算效果指标
function calculateEffectivenessMetrics(intervention: any, feedbacks: any[], healthRecords: any[]) {
  const adherenceScores = feedbacks.map(f => f.adherence_score);
  const satisfactionScores = feedbacks.map(f => f.satisfaction_score);

  // 计算平均依从性
  const avgAdherence = adherenceScores.length > 0 
    ? adherenceScores.reduce((sum, score) => sum + score, 0) / adherenceScores.length 
    : 0;

  // 计算平均满意度
  const avgSatisfaction = satisfactionScores.length > 0 
    ? satisfactionScores.reduce((sum, score) => sum + score, 0) / satisfactionScores.length 
    : 0;

  // 计算依从性趋势
  const adherenceTrend = calculateTrend(adherenceScores);

  // 计算满意度趋势
  const satisfactionTrend = calculateTrend(satisfactionScores);

  // 分析健康指标变化
  const healthImprovements = analyzeHealthImprovements(healthRecords, intervention.risk_assessment);

  // 计算总体有效性评分
  const overallEffectiveness = calculateOverallEffectiveness(avgAdherence, avgSatisfaction, healthImprovements);

  return {
    avgAdherence: Math.round(avgAdherence * 10) / 10,
    avgSatisfaction: Math.round(avgSatisfaction * 10) / 10,
    adherenceTrend,
    satisfactionTrend,
    healthImprovements,
    overallEffectiveness: Math.round(overallEffectiveness * 100) / 100,
    completionRate: calculateCompletionRate(feedbacks),
    persistenceScore: calculatePersistenceScore(feedbacks),
    riskLevelChange: calculateRiskLevelChange(healthRecords, intervention.risk_assessment)
  };
}

// 计算趋势
function calculateTrend(scores: number[]) {
  if (scores.length < 2) return 'stable';
  
  const firstHalf = scores.slice(0, Math.floor(scores.length / 2));
  const secondHalf = scores.slice(Math.floor(scores.length / 2));
  
  const firstAvg = firstHalf.reduce((sum, score) => sum + score, 0) / firstHalf.length;
  const secondAvg = secondHalf.reduce((sum, score) => sum + score, 0) / secondHalf.length;
  
  const difference = secondAvg - firstAvg;
  
  if (difference > 0.5) return 'improving';
  if (difference < -0.5) return 'declining';
  return 'stable';
}

// 分析健康改善情况
function analyzeHealthImprovements(healthRecords: any[], baselineRiskAssessment: any) {
  const improvements: any = {};
  
  // 按记录类型分组
  const recordsByType: Record<string, any[]> = {};
  healthRecords.forEach(record => {
    if (!recordsByType[record.record_type]) {
      recordsByType[record.record_type] = [];
    }
    recordsByType[record.record_type].push(record);
  });

  // 分析血压改善
  if (recordsByType['blood_pressure']) {
    const bpRecords = recordsByType['blood_pressure'];
    const recentBPs = bpRecords.slice(-7); // 最近7次记录
    const baselineBP = bpRecords[0]?.record_value;
    
    if (baselineBP && recentBPs.length > 0) {
      const recentAvgSystolic = recentBPs.reduce((sum, r) => sum + (r.record_value?.systolic || 0), 0) / recentBPs.length;
      const baselineSystolic = baselineBP.systolic;
      
      improvements.bloodPressure = {
        baseline: baselineSystolic,
        current: Math.round(recentAvgSystolic),
        change: Math.round(recentAvgSystolic - baselineSystolic),
        improvement: recentAvgSystolic < baselineSystolic
      };
    }
  }

  // 分析血糖改善
  if (recordsByType['blood_sugar']) {
    const sugarRecords = recordsByType['blood_sugar'];
    const recentSugars = sugarRecords.slice(-7);
    const baselineSugar = sugarRecords[0]?.record_value;
    
    if (baselineSugar && recentSugars.length > 0) {
      const recentAvgGlucose = recentSugars.reduce((sum, r) => sum + (r.record_value?.glucose || 0), 0) / recentSugars.length;
      const baselineGlucose = baselineSugar.glucose;
      
      improvements.bloodSugar = {
        baseline: baselineGlucose,
        current: Math.round(recentAvgGlucose * 10) / 10,
        change: Math.round((recentAvgGlucose - baselineGlucose) * 10) / 10,
        improvement: recentAvgGlucose < baselineGlucose
      };
    }
  }

  return improvements;
}

// 计算总体有效性
function calculateOverallEffectiveness(avgAdherence: number, avgSatisfaction: number, healthImprovements: any) {
  let effectiveness = 0;
  
  // 依从性权重 40%
  effectiveness += (avgAdherence / 10) * 0.4;
  
  // 满意度权重 20%
  effectiveness += (avgSatisfaction / 10) * 0.2;
  
  // 健康改善权重 40%
  let healthScore = 0;
  const metrics = Object.values(healthImprovements);
  if (metrics.length > 0) {
    healthScore = metrics.filter(m => m.improvement).length / metrics.length;
  }
  effectiveness += healthScore * 0.4;
  
  return Math.min(effectiveness, 1.0);
}

// 判断是否需要调整
function determineIfAdjustmentNeeded(metrics: any, intervention: any) {
  // 低依从性需要调整
  if (metrics.avgAdherence < 6) return true;
  
  // 低满意度需要调整
  if (metrics.avgSatisfaction < 5) return true;
  
  // 下降趋势需要调整
  if (metrics.adherenceTrend === 'declining' || metrics.satisfactionTrend === 'declining') return true;
  
  // 健康指标没有改善
  const healthImprovements = Object.values(metrics.healthImprovements);
  const improvementRate = healthImprovements.filter(m => m.improvement).length / healthImprovements.length;
  if (healthImprovements.length > 0 && improvementRate < 0.5) return true;
  
  // 总体效果低
  if (metrics.overallEffectiveness < 0.6) return true;
  
  return false;
}

// 生成改进建议
function generateImprovementSuggestions(metrics: any, feedbacks: any[]) {
  const suggestions: any[] = [];
  
  // 基于依从性的建议
  if (metrics.avgAdherence < 6) {
    suggestions.push({
      type: 'adherence_enhancement',
      priority: 'high',
      title: '提高执行依从性',
      description: '建议简化执行步骤，提供更多支持和提醒',
      actions: [
        '分解复杂任务为简单步骤',
        '增加提醒频率和方式',
        '提供执行指导视频',
        '设置小奖励机制'
      ]
    });
  }
  
  // 基于满意度的建议
  if (metrics.avgSatisfaction < 5) {
    suggestions.push({
      type: 'satisfaction_improvement',
      priority: 'medium',
      title: '提升用户体验',
      description: '优化建议内容，使其更适合用户偏好',
      actions: [
        '调整建议内容复杂度',
        '提供更多个性化选择',
        '改进界面交互设计',
        '增加鼓励和正面反馈'
      ]
    });
  }
  
  // 基于健康指标的建议
  const healthImprovements = metrics.healthImprovements;
  if (healthImprovements.bloodPressure && !healthImprovements.bloodPressure.improvement) {
    suggestions.push({
      type: 'medical_adjustment',
      priority: 'urgent',
      title: '血压管理调整',
      description: '血压控制效果不佳，建议调整方案或咨询医生',
      actions: [
        '重新评估用药方案',
        '调整饮食和运动计划',
        '增加血压监测频率',
        '安排医生随访'
      ]
    });
  }
  
  return suggestions;
}

// 触发方案调整
async function triggerPlanAdjustment(supabase: any, interventionId: string, effectiveness: any) {
  // 创建新的调整记录
  const { data: adjustment, error } = await supabase
    .from('intervention_adjustments')
    .insert({
      intervention_id: interventionId,
      original_effectiveness: effectiveness.overallEffectiveness,
      adjustment_reason: 'low_effectiveness',
      adjustment_suggestions: effectiveness.improvementSuggestions,
      adjustment_type: 'optimization',
      created_at: new Date().toISOString()
    })
    .select()
    .single();

  if (error) {
    throw new Error(`创建调整记录失败: ${error.message}`);
  }

  // 更新干预状态为需要调整
  await supabase
    .from('intervention_records')
    .update({ 
      status: 'needs_adjustment',
      adjustment_count: supabase.sql`coalesce(adjustment_count, 0) + 1`
    })
    .eq('id', interventionId);

  return adjustment;
}

// 生成进展报告
async function generateProgressReport(supabase: any, userId: string, interventionId: string) {
  // 获取用户基本信息和干预记录
  const { data: userProfile } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('user_id', userId)
    .single();

  const { data: intervention } = await supabase
    .from('intervention_records')
    .select('*')
    .eq('id', interventionId)
    .single();

  // 获取相关反馈和健康数据
  const { data: feedbacks } = await supabase
    .from('intervention_feedback')
    .select('*')
    .eq('intervention_id', interventionId);

  const { data: healthRecords } = await supabase
    .from('health_records')
    .select('*')
    .eq('user_id', userId)
    .gte('recorded_at', intervention.created_at)
    .order('recorded_at', { ascending: false });

  // 生成报告内容
  const report = {
    reportId: `progress_${interventionId}_${Date.now()}`,
    userInfo: {
      name: '用户', // 实际应用中应从用户数据获取
      age: userProfile?.age,
      gender: userProfile?.gender
    },
    interventionInfo: {
      type: intervention.intervention_type,
      startDate: intervention.created_at,
      duration: calculateTimeSpan(intervention.created_at, new Date().toISOString())
    },
    progress: {
      overallScore: calculateOverallEffectiveness(
        feedbacks?.reduce((sum, f) => sum + f.adherence_score, 0) / (feedbacks?.length || 1),
        feedbacks?.reduce((sum, f) => sum + f.satisfaction_score, 0) / (feedbacks?.length || 1),
        {}
      ),
      completionRate: calculateCompletionRate(feedbacks || []),
      keyAchievements: identifyKeyAchievements(healthRecords || [], intervention.risk_assessment),
      areasForImprovement: identifyAreasForImprovement(effectiveness)
    },
    healthMetrics: {
      bloodPressure: analyzeBloodPressureTrend(healthRecords || []),
      bloodSugar: analyzeBloodSugarTrend(healthRecords || []),
      otherMetrics: analyzeOtherMetrics(healthRecords || [])
    },
    recommendations: {
      continueCurrent: effectiveness.overallEffectiveness >= 0.7,
      modifyApproach: effectiveness.needsAdjustment,
      newGoals: generateNewGoals(effectiveness)
    },
    generatedAt: new Date().toISOString()
  };

  // 保存报告记录
  await supabase
    .from('progress_reports')
    .insert({
      user_id: userId,
      intervention_id: interventionId,
      report_data: report,
      created_at: new Date().toISOString()
    });

  return report;
}

// 更新干预状态
async function updateInterventionStatus(supabase: any, interventionId: string, effectiveness: any) {
  let status = 'active';
  
  if (effectiveness.overallEffectiveness >= 0.8) {
    status = 'completed_successfully';
  } else if (effectiveness.overallEffectiveness < 0.4) {
    status = 'low_effectiveness';
  } else if (effectiveness.needsAdjustment) {
    status = 'needs_adjustment';
  }

  await supabase
    .from('intervention_records')
    .update({ 
      status,
      effectiveness_score: effectiveness.overallEffectiveness,
      updated_at: new Date().toISOString()
    })
    .eq('id', interventionId);
}

// 生成后续行动建议
function generateNextActions(effectiveness: any) {
  const actions = [];
  
  if (effectiveness.overallEffectiveness >= 0.8) {
    actions.push({
      action: '维持现状',
      description: '当前方案效果良好，建议继续执行',
      priority: 'low'
    });
  } else if (effectiveness.needsAdjustment) {
    effectiveness.improvementSuggestions.forEach((suggestion: any) => {
      actions.push({
        action: suggestion.title,
        description: suggestion.description,
        priority: suggestion.priority
      });
    });
  } else {
    actions.push({
      action: '优化执行',
      description: '适度调整执行方式，提高效果',
      priority: 'medium'
    });
  }
  
  return actions;
}

// 工具函数
function calculateCompletionRate(feedbacks: any[]) {
  if (feedbacks.length === 0) return 0;
  
  const completedFeedbacks = feedbacks.filter(f => f.adherence_score >= 7);
  return Math.round((completedFeedbacks.length / feedbacks.length) * 100);
}

function calculatePersistenceScore(feedbacks: any[]) {
  if (feedbacks.length < 2) return feedbacks.length > 0 ? 100 : 0;
  
  let consistent = 0;
  for (let i = 1; i < feedbacks.length; i++) {
    if (Math.abs(feedbacks[i].adherence_score - feedbacks[i-1].adherence_score) <= 2) {
      consistent++;
    }
  }
  
  return Math.round((consistent / (feedbacks.length - 1)) * 100);
}

function calculateTimeSpan(startDate: string, endDate: string) {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diffTime = Math.abs(end.getTime() - start.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

function calculateRiskLevelChange(healthRecords: any[], baselineRisk: any) {
  // 实现风险等级变化分析
  return 'stable'; // 简化实现
}

function identifyKeyAchievements(healthRecords: any[], baselineRisk: any) {
  const achievements = [];
  
  const bloodPressureRecords = healthRecords.filter(r => r.record_type === 'blood_pressure');
  if (bloodPressureRecords.length > 1) {
    const latest = bloodPressureRecords[0].record_value?.systolic;
    const baseline = bloodPressureRecords[bloodPressureRecords.length - 1].record_value?.systolic;
    
    if (latest && baseline && latest < baseline) {
      achievements.push('血压有所改善');
    }
  }
  
  return achievements;
}

function identifyAreasForImprovement(effectiveness: any) {
  const areas = [];
  
  if (effectiveness.avgAdherence < 6) {
    areas.push('执行依从性需要提高');
  }
  
  if (effectiveness.avgSatisfaction < 5) {
    areas.push('用户体验有待改善');
  }
  
  return areas;
}

function analyzeBloodPressureTrend(healthRecords: any[]) {
  const bpRecords = healthRecords.filter(r => r.record_type === 'blood_pressure');
  if (bpRecords.length < 2) return null;
  
  const latest = bpRecords[0].record_value?.systolic;
  const previous = bpRecords[1].record_value?.systolic;
  
  if (latest && previous) {
    return {
      trend: latest < previous ? 'improving' : latest > previous ? 'worsening' : 'stable',
      change: latest - previous
    };
  }
  
  return null;
}

function analyzeBloodSugarTrend(healthRecords: any[]) {
  const sugarRecords = healthRecords.filter(r => r.record_type === 'blood_sugar');
  if (sugarRecords.length < 2) return null;
  
  const latest = sugarRecords[0].record_value?.glucose;
  const previous = sugarRecords[1].record_value?.glucose;
  
  if (latest && previous) {
    return {
      trend: latest < previous ? 'improving' : latest > previous ? 'worsening' : 'stable',
      change: Math.round((latest - previous) * 10) / 10
    };
  }
  
  return null;
}

function analyzeOtherMetrics(healthRecords: any[]) {
  return {}; // 简化实现
}

function generateNewGoals(effectiveness: any) {
  const goals = [];
  
  if (effectiveness.avgAdherence < 8) {
    goals.push('提高执行依从性至8分以上');
  }
  
  if (effectiveness.overallEffectiveness < 0.8) {
    goals.push('将总体效果提升至80%以上');
  }
  
  return goals;
}