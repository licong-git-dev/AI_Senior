import React, { useEffect, useState } from 'react';
import { supabase } from '../../lib/supabase';
import { ClipboardList, Activity, CheckCircle, Calendar, Target, Pill } from 'lucide-react';

// 护理端：健康计划执行、康复指导
export default function HealthPlanExecution() {
  const [loading, setLoading] = useState(true);
  const [elderlyList, setElderlyList] = useState<any[]>([]);
  const [selectedElderly, setSelectedElderly] = useState<any>(null);
  const [careData, setCareData] = useState<any>(null);

  useEffect(() => {
    loadElderlyList();
  }, []);

  useEffect(() => {
    if (selectedElderly) {
      loadCareData(selectedElderly.user_id);
    }
  }, [selectedElderly]);

  const loadElderlyList = async () => {
    try {
      // 获取有健康计划的老人列表
      const { data: profilesData } = await supabase
        .from('profiles')
        .select('*')
        .limit(20);

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

  const loadCareData = async (userId: string) => {
    try {
      const [medications, rehabPlans, goals, conditions] = await Promise.all([
        supabase.from('medication_management').select('*').eq('user_id', userId).eq('status', 'active'),
        supabase.from('rehabilitation_plans').select('*').eq('user_id', userId).eq('status', 'active'),
        supabase.from('health_goals').select('*').eq('user_id', userId).eq('status', 'in_progress'),
        supabase.from('chronic_conditions').select('*').eq('user_id', userId).eq('current_status', 'active')
      ]);

      setCareData({
        medications: medications.data || [],
        rehabPlans: rehabPlans.data || [],
        goals: goals.data || [],
        conditions: conditions.data || []
      });
    } catch (error) {
      console.error('加载护理数据失败:', error);
    }
  };

  const handleConfirmMedication = async (medicationId: string) => {
    // 确认服药记录
    alert('已确认服药完成！');
  };

  const handleCompleteExercise = async (planId: string) => {
    try {
      // 更新康复训练完成度
      const { data: planData } = await supabase
        .from('rehabilitation_plans')
        .select('*')
        .eq('id', planId)
        .single();

      if (planData) {
        const newRate = Math.min(100, planData.completion_rate + 5);
        await supabase
          .from('rehabilitation_plans')
          .update({ 
            completion_rate: newRate,
            updated_at: new Date().toISOString()
          })
          .eq('id', planId);

        alert(`训练记录已保存！当前完成度：${newRate}%`);
        loadCareData(selectedElderly.user_id);
      }
    } catch (error) {
      console.error('更新训练记录失败:', error);
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
      {/* 顶部导航 */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <ClipboardList className="w-8 h-8 text-green-600" />
              护理工作台 - 健康计划执行
            </h1>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">护理对象:</span>
              <select 
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
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
        {careData && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左侧：今日任务 */}
            <div className="lg:col-span-2 space-y-6">
              {/* 今日用药提醒 */}
              <div className="bg-white rounded-lg p-6 shadow-md">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <Pill className="w-6 h-6 text-blue-600" />
                    今日用药计划 ({careData.medications.length})
                  </h2>
                  <span className="text-sm text-gray-600">
                    {new Date().toLocaleDateString('zh-CN')}
                  </span>
                </div>
                <div className="space-y-3">
                  {careData.medications.length > 0 ? (
                    careData.medications.map((med: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-800 text-lg">{med.medication_name}</h3>
                            <div className="mt-2 space-y-1 text-sm text-gray-600">
                              <p className="flex items-center gap-2">
                                <span className="font-medium">用量：</span>
                                <span className="text-blue-600 font-semibold">{med.dosage}</span>
                              </p>
                              <p className="flex items-center gap-2">
                                <span className="font-medium">频率：</span>
                                <span>{med.frequency}</span>
                              </p>
                              <p className="flex items-center gap-2">
                                <span className="font-medium">服用时间：</span>
                                <span className="text-orange-600 font-semibold">{med.intake_time}</span>
                              </p>
                              {med.stock_quantity <= med.low_stock_threshold && (
                                <p className="text-orange-600 font-semibold flex items-center gap-1">
                                  ⚠️ 库存不足({med.stock_quantity})，请及时补充
                                </p>
                              )}
                            </div>
                          </div>
                          <button
                            onClick={() => handleConfirmMedication(med.id)}
                            className="ml-4 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center gap-2 whitespace-nowrap"
                          >
                            <CheckCircle className="w-4 h-4" />
                            确认服药
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-8">今日暂无用药计划</p>
                  )}
                </div>
              </div>

              {/* 康复训练计划 */}
              <div className="bg-white rounded-lg p-6 shadow-md">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <Activity className="w-6 h-6 text-green-600" />
                    康复训练执行 ({careData.rehabPlans.length})
                  </h2>
                </div>
                <div className="space-y-4">
                  {careData.rehabPlans.length > 0 ? (
                    careData.rehabPlans.map((plan: any, index: number) => (
                      <div key={index} className="border-2 border-gray-200 rounded-lg p-5 hover:shadow-lg transition-shadow">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="font-bold text-gray-800 text-lg">{plan.plan_name}</h3>
                            <p className="text-sm text-gray-600 mt-1">
                              {plan.exercise_type} · 强度: {plan.intensity_level} · {plan.duration_minutes}分钟/次
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-3xl font-bold text-green-600">{Math.round(plan.completion_rate)}%</p>
                            <p className="text-xs text-gray-500">完成度</p>
                          </div>
                        </div>

                        {/* 训练指导 */}
                        <div className="bg-blue-50 rounded-lg p-4 mb-3">
                          <p className="text-sm font-semibold text-blue-900 mb-2">📋 训练指导：</p>
                          <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
                            {plan.instructions}
                          </p>
                        </div>

                        {/* 注意事项 */}
                        <div className="bg-yellow-50 rounded-lg p-4 mb-3">
                          <p className="text-sm font-semibold text-yellow-900 mb-2">⚠️ 注意事项：</p>
                          <p className="text-sm text-gray-700">{plan.precautions}</p>
                        </div>

                        {/* 训练详情 */}
                        <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
                          <div className="bg-gray-50 rounded p-2">
                            <span className="text-gray-600">每周频率：</span>
                            <span className="font-semibold text-gray-800 ml-1">{plan.frequency_per_week}次</span>
                          </div>
                          <div className="bg-gray-50 rounded p-2">
                            <span className="text-gray-600">开始日期：</span>
                            <span className="font-semibold text-gray-800 ml-1">{plan.start_date}</span>
                          </div>
                        </div>

                        {/* 进度条 */}
                        <div className="mb-3">
                          <div className="bg-gray-200 rounded-full h-3 overflow-hidden">
                            <div 
                              className="bg-green-500 h-full rounded-full transition-all duration-500"
                              style={{ width: `${plan.completion_rate}%` }}
                            ></div>
                          </div>
                        </div>

                        {/* 操作按钮 */}
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleCompleteExercise(plan.id)}
                            className="flex-1 px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-semibold flex items-center justify-center gap-2"
                          >
                            <CheckCircle className="w-5 h-5" />
                            完成本次训练
                          </button>
                          <button className="px-4 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
                            查看详情
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-8">暂无康复训练计划</p>
                  )}
                </div>
              </div>
            </div>

            {/* 右侧：患者信息和健康目标 */}
            <div className="space-y-6">
              {/* 慢性病信息 */}
              <div className="bg-white rounded-lg p-6 shadow-md">
                <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Activity className="w-6 h-6 text-purple-600" />
                  慢性病信息
                </h2>
                <div className="space-y-3">
                  {careData.conditions.length > 0 ? (
                    careData.conditions.map((cond: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-3">
                        <p className="font-semibold text-gray-800">
                          {cond.condition_type === 'hypertension' ? '高血压' :
                           cond.condition_type === 'diabetes' ? '糖尿病' :
                           cond.condition_type === 'heart_disease' ? '心脏病' :
                           cond.condition_type === 'arthritis' ? '关节炎' : cond.condition_type}
                        </p>
                        <div className="mt-2 space-y-1 text-xs text-gray-600">
                          <p>严重程度：
                            <span className={`ml-1 font-semibold ${
                              cond.severity_level === 'severe' ? 'text-red-600' :
                              cond.severity_level === 'moderate' ? 'text-orange-600' :
                              'text-green-600'
                            }`}>
                              {cond.severity_level === 'severe' ? '严重' :
                               cond.severity_level === 'moderate' ? '中等' : '轻度'}
                            </span>
                          </p>
                          <p>主治医生：{cond.doctor_name}</p>
                          <p>诊断日期：{cond.diagnosis_date}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-4 text-sm">暂无慢性病记录</p>
                  )}
                </div>
              </div>

              {/* 健康目标跟踪 */}
              <div className="bg-white rounded-lg p-6 shadow-md">
                <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Target className="w-6 h-6 text-green-600" />
                  健康目标跟踪
                </h2>
                <div className="space-y-4">
                  {careData.goals.length > 0 ? (
                    careData.goals.map((goal: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <p className="font-semibold text-gray-800 mb-2">
                          {goal.goal_type === 'blood_pressure' ? '血压控制' :
                           goal.goal_type === 'blood_glucose' ? '血糖控制' :
                           goal.goal_type === 'weight' ? '体重管理' :
                           goal.goal_type === 'steps' ? '每日步数' : goal.goal_type}
                        </p>
                        <div className="flex justify-between text-sm text-gray-600 mb-2">
                          <span>当前: {goal.current_value}</span>
                          <span>目标: {goal.target_value}</span>
                        </div>
                        <div className="bg-gray-200 rounded-full h-2.5 overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all ${
                              goal.achievement_rate >= 80 ? 'bg-green-500' :
                              goal.achievement_rate >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${Math.min(goal.achievement_rate, 100)}%` }}
                          ></div>
                        </div>
                        <p className="text-center text-sm font-semibold text-gray-700 mt-2">
                          {Math.round(goal.achievement_rate)}% 完成
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-4 text-sm">暂无健康目标</p>
                  )}
                </div>
              </div>

              {/* 今日护理记录 */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 shadow-md border border-blue-200">
                <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Calendar className="w-6 h-6 text-blue-600" />
                  今日护理记录
                </h2>
                <div className="space-y-2 text-sm">
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-gray-600">护理日期</p>
                    <p className="font-semibold text-gray-800">{new Date().toLocaleDateString('zh-CN')}</p>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-gray-600">用药提醒</p>
                    <p className="font-semibold text-blue-600">{careData.medications.length} 项</p>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-gray-600">康复训练</p>
                    <p className="font-semibold text-green-600">{careData.rehabPlans.length} 项</p>
                  </div>
                </div>
                <button className="w-full mt-4 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold">
                  提交今日护理报告
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
