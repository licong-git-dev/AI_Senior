import React, { useEffect, useState } from 'react';
import { supabase } from '../../lib/supabase';
import { Activity, Pill, Target, Heart } from 'lucide-react';

// 老人端：超大字体、高对比度、简化操作
export default function HealthSimplified() {
  const [loading, setLoading] = useState(true);
  const [conditions, setConditions] = useState<any[]>([]);
  const [medications, setMedications] = useState<any[]>([]);
  const [goals, setGoals] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [userId, setUserId] = useState<string>('');

  useEffect(() => {
    loadHealthData();
  }, []);

  const loadHealthData = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;
      
      setUserId(user.id);

      // 加载慢性病
      const { data: condData } = await supabase
        .from('chronic_conditions')
        .select('*')
        .eq('user_id', user.id)
        .eq('current_status', 'active')
        .limit(3);
      
      // 加载今日用药
      const { data: medData } = await supabase
        .from('medication_management')
        .select('*')
        .eq('user_id', user.id)
        .eq('status', 'active')
        .limit(5);

      // 加载健康目标
      const { data: goalData } = await supabase
        .from('health_goals')
        .select('*')
        .eq('user_id', user.id)
        .eq('status', 'in_progress')
        .limit(2);

      // 加载健康预警
      const { data: alertData } = await supabase
        .from('health_alerts')
        .select('*')
        .eq('user_id', user.id)
        .eq('resolved', false)
        .order('created_at', { ascending: false })
        .limit(3);

      setConditions(condData || []);
      setMedications(medData || []);
      setGoals(goalData || []);
      setAlerts(alertData || []);
    } catch (error) {
      console.error('加载健康数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-4xl font-bold text-gray-600">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white p-6">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* 页面标题 - 超大字体 */}
        <div className="text-center">
          <h1 className="text-6xl font-bold text-gray-800 mb-4">我的健康</h1>
          <p className="text-3xl text-gray-600">{new Date().toLocaleDateString('zh-CN', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            weekday: 'long'
          })}</p>
        </div>

        {/* 健康预警 - 高对比度红色 */}
        {alerts.length > 0 && (
          <div className="bg-red-100 border-4 border-red-500 rounded-3xl p-8 shadow-2xl">
            <div className="flex items-center gap-4 mb-6">
              <Heart className="w-16 h-16 text-red-600" />
              <h2 className="text-5xl font-bold text-red-700">健康提醒</h2>
            </div>
            <div className="space-y-4">
              {alerts.map((alert, index) => (
                <div key={index} className="bg-white rounded-2xl p-6 border-2 border-red-300">
                  <p className="text-3xl font-semibold text-red-800">{alert.indicator_name}异常</p>
                  <p className="text-2xl text-gray-700 mt-2">数值：{alert.abnormal_value}</p>
                  <p className="text-2xl text-gray-600 mt-2">正常范围：{alert.normal_range}</p>
                  <p className="text-3xl font-bold text-red-600 mt-4">{alert.recommended_actions}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 今日用药 - 大按钮 */}
        <div className="bg-white rounded-3xl p-8 shadow-2xl border-4 border-blue-200">
          <div className="flex items-center gap-4 mb-6">
            <Pill className="w-16 h-16 text-blue-600" />
            <h2 className="text-5xl font-bold text-gray-800">今日用药</h2>
          </div>
          <div className="space-y-4">
            {medications.length > 0 ? (
              medications.map((med, index) => (
                <div key={index} className="bg-blue-50 rounded-2xl p-6 border-2 border-blue-300">
                  <p className="text-4xl font-bold text-blue-900">{med.medication_name}</p>
                  <div className="mt-4 space-y-2">
                    <p className="text-3xl text-gray-700">用量：<span className="font-semibold text-blue-700">{med.dosage}</span></p>
                    <p className="text-3xl text-gray-700">频率：<span className="font-semibold text-blue-700">{med.frequency}</span></p>
                    <p className="text-3xl text-gray-700">时间：<span className="font-semibold text-blue-700">{med.intake_time}</span></p>
                    {med.stock_quantity <= med.low_stock_threshold && (
                      <p className="text-3xl font-bold text-orange-600 mt-3">⚠️ 药品不足，请及时补充</p>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-3xl text-gray-500 text-center py-8">暂无用药记录</p>
            )}
          </div>
        </div>

        {/* 我的疾病 */}
        <div className="bg-white rounded-3xl p-8 shadow-2xl border-4 border-purple-200">
          <div className="flex items-center gap-4 mb-6">
            <Activity className="w-16 h-16 text-purple-600" />
            <h2 className="text-5xl font-bold text-gray-800">我的疾病</h2>
          </div>
          <div className="space-y-4">
            {conditions.length > 0 ? (
              conditions.map((cond, index) => (
                <div key={index} className="bg-purple-50 rounded-2xl p-6 border-2 border-purple-300">
                  <p className="text-4xl font-bold text-purple-900">
                    {cond.condition_type === 'hypertension' ? '高血压' :
                     cond.condition_type === 'diabetes' ? '糖尿病' :
                     cond.condition_type === 'heart_disease' ? '心脏病' :
                     cond.condition_type === 'arthritis' ? '关节炎' : cond.condition_type}
                  </p>
                  <div className="mt-4 space-y-2">
                    <p className="text-3xl text-gray-700">严重程度：
                      <span className={`font-bold ml-2 ${
                        cond.severity_level === 'severe' ? 'text-red-600' :
                        cond.severity_level === 'moderate' ? 'text-orange-600' :
                        'text-green-600'
                      }`}>
                        {cond.severity_level === 'severe' ? '严重' :
                         cond.severity_level === 'moderate' ? '中等' : '轻度'}
                      </span>
                    </p>
                    <p className="text-3xl text-gray-700">主治医生：<span className="font-semibold">{cond.doctor_name}</span></p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-3xl text-gray-500 text-center py-8">暂无疾病记录</p>
            )}
          </div>
        </div>

        {/* 健康目标 */}
        <div className="bg-white rounded-3xl p-8 shadow-2xl border-4 border-green-200">
          <div className="flex items-center gap-4 mb-6">
            <Target className="w-16 h-16 text-green-600" />
            <h2 className="text-5xl font-bold text-gray-800">健康目标</h2>
          </div>
          <div className="space-y-4">
            {goals.length > 0 ? (
              goals.map((goal, index) => (
                <div key={index} className="bg-green-50 rounded-2xl p-6 border-2 border-green-300">
                  <p className="text-4xl font-bold text-green-900">
                    {goal.goal_type === 'blood_pressure' ? '血压控制' :
                     goal.goal_type === 'blood_glucose' ? '血糖控制' :
                     goal.goal_type === 'weight' ? '体重管理' :
                     goal.goal_type === 'steps' ? '每日步数' : goal.goal_type}
                  </p>
                  <div className="mt-4">
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-3xl text-gray-700">当前：<span className="font-bold text-gray-900">{goal.current_value}</span></span>
                      <span className="text-3xl text-gray-700">目标：<span className="font-bold text-green-700">{goal.target_value}</span></span>
                    </div>
                    <div className="bg-gray-200 rounded-full h-8 overflow-hidden">
                      <div 
                        className="bg-green-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(goal.achievement_rate, 100)}%` }}
                      ></div>
                    </div>
                    <p className="text-3xl text-center mt-3 font-bold text-green-700">
                      完成 {Math.round(goal.achievement_rate)}%
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-3xl text-gray-500 text-center py-8">暂无健康目标</p>
            )}
          </div>
        </div>

        {/* 紧急联系按钮 */}
        <div className="grid grid-cols-2 gap-6 mt-12">
          <button className="bg-red-500 hover:bg-red-600 text-white rounded-3xl py-12 shadow-2xl transform transition hover:scale-105">
            <p className="text-5xl font-bold">📞 呼叫家人</p>
          </button>
          <button className="bg-orange-500 hover:bg-orange-600 text-white rounded-3xl py-12 shadow-2xl transform transition hover:scale-105">
            <p className="text-5xl font-bold">🚑 紧急求助</p>
          </button>
        </div>
      </div>
    </div>
  );
}
