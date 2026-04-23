import React, { useEffect, useState } from 'react';
import { supabase } from '../../lib/supabase';
import { Activity, TrendingUp, TrendingDown, AlertTriangle, Users, Heart, Pill, Target } from 'lucide-react';

// 家属端：健康监控仪表盘、数据可视化
export default function HealthMonitor() {
  const [loading, setLoading] = useState(true);
  const [elderlyList, setElderlyList] = useState<any[]>([]);
  const [selectedElderly, setSelectedElderly] = useState<any>(null);
  const [healthSummary, setHealthSummary] = useState<any>(null);
  const [aiInsights, setAiInsights] = useState<string>('');

  useEffect(() => {
    loadElderlyList();
  }, []);

  useEffect(() => {
    if (selectedElderly) {
      loadHealthSummary(selectedElderly.user_id);
    }
  }, [selectedElderly]);

  const loadElderlyList = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      // 获取当前家属关联的老人列表（假设通过profiles表的relationship字段）
      // 这里简化处理，获取所有有健康数据的用户
      const { data: profilesData } = await supabase
        .from('profiles')
        .select('*')
        .limit(10);

      setElderlyList(profilesData || []);
      if (profilesData && profilesData.length > 0) {
        setSelectedElderly(profilesData[0]);
      }
    } catch (error) {
      console.error('加载老人列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadHealthSummary = async (userId: string) => {
    try {
      // 加载慢性病
      const { data: conditions } = await supabase
        .from('chronic_conditions')
        .select('*')
        .eq('user_id', userId)
        .eq('current_status', 'active');

      // 加载用药
      const { data: medications } = await supabase
        .from('medication_management')
        .select('*')
        .eq('user_id', userId)
        .eq('status', 'active');

      // 加载健康目标
      const { data: goals } = await supabase
        .from('health_goals')
        .select('*')
        .eq('user_id', userId)
        .eq('status', 'in_progress');

      // 加载健康预警
      const { data: alerts } = await supabase
        .from('health_alerts')
        .select('*')
        .eq('user_id', userId)
        .eq('resolved', false)
        .order('created_at', { ascending: false });

      // 加载康复计划
      const { data: rehabPlans } = await supabase
        .from('rehabilitation_plans')
        .select('*')
        .eq('user_id', userId)
        .eq('status', 'active');

      setHealthSummary({
        conditions: conditions || [],
        medications: medications || [],
        goals: goals || [],
        alerts: alerts || [],
        rehabPlans: rehabPlans || []
      });

      // 调用AI分析
      await getAIAnalysis(userId);
    } catch (error) {
      console.error('加载健康摘要失败:', error);
    }
  };

  const getAIAnalysis = async (userId: string) => {
    try {
      const { data, error } = await supabase.functions.invoke('chronic-disease-monitor', {
        body: { user_id: userId, action: 'analyze_risk' }
      });

      if (data && data.data) {
        const insights = `风险等级：${data.data.risk_level}\n风险因素：${data.data.risk_factors.join('、')}\n\n建议措施：\n${data.data.recommendations.join('\n')}`;
        setAiInsights(insights);
      }
    } catch (error) {
      console.error('AI分析失败:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl text-gray-600">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <div className="bg-white shadow-md border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <Users className="w-8 h-8 text-blue-600" />
              家属健康监控中心
            </h1>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">监护对象:</span>
              <select 
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={selectedElderly?.user_id || ''}
                onChange={(e) => {
                  const elderly = elderlyList.find(el => el.user_id === e.target.value);
                  setSelectedElderly(elderly);
                }}
              >
                {elderlyList.map((elderly) => (
                  <option key={elderly.user_id} value={elderly.user_id}>
                    {elderly.full_name || '老人' + elderly.user_id?.substring(0, 8)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {healthSummary && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左侧：关键指标卡片 */}
            <div className="lg:col-span-2 space-y-6">
              {/* 健康预警 */}
              {healthSummary.alerts.length > 0 && (
                <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-6 shadow-md">
                  <div className="flex items-center gap-3 mb-4">
                    <AlertTriangle className="w-6 h-6 text-red-600" />
                    <h2 className="text-xl font-bold text-red-800">健康预警 ({healthSummary.alerts.length})</h2>
                  </div>
                  <div className="space-y-3">
                    {healthSummary.alerts.map((alert: any, index: number) => (
                      <div key={index} className="bg-white rounded-lg p-4 border border-red-200">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-semibold text-gray-800">{alert.indicator_name}异常</p>
                            <p className="text-sm text-gray-600 mt-1">数值：{alert.abnormal_value} (正常：{alert.normal_range})</p>
                            <p className="text-sm text-red-600 mt-2">{alert.recommended_actions}</p>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            alert.severity === 'high' ? 'bg-red-100 text-red-800' :
                            alert.severity === 'medium' ? 'bg-orange-100 text-orange-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {alert.severity === 'high' ? '高风险' :
                             alert.severity === 'medium' ? '中风险' : '低风险'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 统计卡片 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg p-4 shadow-md border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">慢性病</p>
                      <p className="text-2xl font-bold text-gray-800">{healthSummary.conditions.length}</p>
                    </div>
                    <Activity className="w-10 h-10 text-purple-500" />
                  </div>
                </div>
                
                <div className="bg-white rounded-lg p-4 shadow-md border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">用药种类</p>
                      <p className="text-2xl font-bold text-gray-800">{healthSummary.medications.length}</p>
                    </div>
                    <Pill className="w-10 h-10 text-blue-500" />
                  </div>
                </div>

                <div className="bg-white rounded-lg p-4 shadow-md border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">健康目标</p>
                      <p className="text-2xl font-bold text-gray-800">{healthSummary.goals.length}</p>
                    </div>
                    <Target className="w-10 h-10 text-green-500" />
                  </div>
                </div>

                <div className="bg-white rounded-lg p-4 shadow-md border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">健康预警</p>
                      <p className="text-2xl font-bold text-red-600">{healthSummary.alerts.length}</p>
                    </div>
                    <AlertTriangle className="w-10 h-10 text-red-500" />
                  </div>
                </div>
              </div>

              {/* 健康目标进度 */}
              <div className="bg-white rounded-lg p-6 shadow-md">
                <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Target className="w-6 h-6 text-green-600" />
                  健康目标进度
                </h2>
                <div className="space-y-4">
                  {healthSummary.goals.length > 0 ? (
                    healthSummary.goals.map((goal: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-semibold text-gray-800">
                            {goal.goal_type === 'blood_pressure' ? '血压控制' :
                             goal.goal_type === 'blood_glucose' ? '血糖控制' :
                             goal.goal_type === 'weight' ? '体重管理' :
                             goal.goal_type === 'steps' ? '每日步数' : goal.goal_type}
                          </span>
                          <span className="text-sm text-gray-600">
                            当前: {goal.current_value} / 目标: {goal.target_value} {goal.unit}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
                            <div 
                              className={`h-full rounded-full transition-all duration-500 ${
                                goal.achievement_rate >= 80 ? 'bg-green-500' :
                                goal.achievement_rate >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${Math.min(goal.achievement_rate, 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-semibold text-gray-700 min-w-[50px]">
                            {Math.round(goal.achievement_rate)}%
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-4">暂无健康目标</p>
                  )}
                </div>
              </div>

              {/* 用药清单 */}
              <div className="bg-white rounded-lg p-6 shadow-md">
                <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Pill className="w-6 h-6 text-blue-600" />
                  当前用药清单
                </h2>
                <div className="space-y-3">
                  {healthSummary.medications.length > 0 ? (
                    healthSummary.medications.map((med: any, index: number) => (
                      <div key={index} className="flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                        <div className="flex-1">
                          <p className="font-semibold text-gray-800">{med.medication_name}</p>
                          <p className="text-sm text-gray-600 mt-1">
                            {med.dosage} · {med.frequency} · {med.intake_time}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className={`text-sm font-semibold ${
                            med.stock_quantity <= med.low_stock_threshold ? 'text-orange-600' : 'text-green-600'
                          }`}>
                            库存: {med.stock_quantity}
                          </p>
                          {med.stock_quantity <= med.low_stock_threshold && (
                            <p className="text-xs text-orange-600">需要补充</p>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-4">暂无用药记录</p>
                  )}
                </div>
              </div>
            </div>

            {/* 右侧：AI分析和慢性病信息 */}
            <div className="space-y-6">
              {/* AI智能分析 */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 shadow-md border border-blue-200">
                <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Heart className="w-6 h-6 text-red-500" />
                  AI健康分析
                </h2>
                {aiInsights ? (
                  <div className="bg-white rounded-lg p-4 whitespace-pre-line text-sm text-gray-700 leading-relaxed">
                    {aiInsights}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-4">分析中...</p>
                )}
                <div className="mt-4 text-xs text-gray-500 flex items-center gap-1">
                  <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                  由阿里云AI提供技术支持
                </div>
              </div>

              {/* 慢性病管理 */}
              <div className="bg-white rounded-lg p-6 shadow-md">
                <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Activity className="w-6 h-6 text-purple-600" />
                  慢性病管理
                </h2>
                <div className="space-y-3">
                  {healthSummary.conditions.length > 0 ? (
                    healthSummary.conditions.map((cond: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-semibold text-gray-800">
                              {cond.condition_type === 'hypertension' ? '高血压' :
                               cond.condition_type === 'diabetes' ? '糖尿病' :
                               cond.condition_type === 'heart_disease' ? '心脏病' :
                               cond.condition_type === 'arthritis' ? '关节炎' : cond.condition_type}
                            </p>
                            <p className="text-sm text-gray-600 mt-1">
                              主治医生：{cond.doctor_name}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              诊断日期：{cond.diagnosis_date}
                            </p>
                          </div>
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            cond.severity_level === 'severe' ? 'bg-red-100 text-red-800' :
                            cond.severity_level === 'moderate' ? 'bg-orange-100 text-orange-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {cond.severity_level === 'severe' ? '严重' :
                             cond.severity_level === 'moderate' ? '中等' : '轻度'}
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-4">暂无慢性病记录</p>
                  )}
                </div>
              </div>

              {/* 康复训练 */}
              {healthSummary.rehabPlans.length > 0 && (
                <div className="bg-white rounded-lg p-6 shadow-md">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">康复训练计划</h2>
                  <div className="space-y-3">
                    {healthSummary.rehabPlans.map((plan: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <p className="font-semibold text-gray-800">{plan.plan_name}</p>
                        <p className="text-sm text-gray-600 mt-1">
                          {plan.exercise_type} · {plan.duration_minutes}分钟 · 每周{plan.frequency_per_week}次
                        </p>
                        <div className="mt-3">
                          <div className="flex justify-between text-xs text-gray-600 mb-1">
                            <span>完成度</span>
                            <span>{Math.round(plan.completion_rate)}%</span>
                          </div>
                          <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
                            <div 
                              className="bg-blue-500 h-full rounded-full"
                              style={{ width: `${plan.completion_rate}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
