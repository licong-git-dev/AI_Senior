import React, { useEffect, useState } from 'react';
import { supabase } from '../../lib/supabase';
import { Users, FileText, TrendingUp, Calendar, Stethoscope, AlertCircle } from 'lucide-react';

// 医生端：患者管理、健康数据分析
export default function PatientManagement() {
  const [patients, setPatients] = useState<any[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<any>(null);
  const [patientDetails, setPatientDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPatients();
  }, []);

  useEffect(() => {
    if (selectedPatient) {
      loadPatientDetails(selectedPatient.user_id);
    }
  }, [selectedPatient]);

  const loadPatients = async () => {
    try {
      // 获取所有有健康记录的患者
      const { data: conditionsData } = await supabase
        .from('chronic_conditions')
        .select('user_id, profiles(*)');

      // 去重并获取患者列表
      const uniquePatients = Array.from(
        new Map(
          (conditionsData || [])
            .filter(item => item.profiles)
            .map(item => [item.user_id, item.profiles])
        ).values()
      );

      setPatients(uniquePatients);
      if (uniquePatients.length > 0) {
        setSelectedPatient(uniquePatients[0]);
      }
    } catch (error) {
      console.error('加载患者列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPatientDetails = async (userId: string) => {
    try {
      // 加载患者所有健康信息
      const [conditions, medications, goals, alerts, healthData, rehabPlans] = await Promise.all([
        supabase.from('chronic_conditions').select('*').eq('user_id', userId),
        supabase.from('medication_management').select('*').eq('user_id', userId).eq('status', 'active'),
        supabase.from('health_goals').select('*').eq('user_id', userId),
        supabase.from('health_alerts').select('*').eq('user_id', userId).eq('resolved', false),
        supabase.from('health_data').select('*').eq('user_id', userId).order('recorded_at', { ascending: false }).limit(30),
        supabase.from('rehabilitation_plans').select('*').eq('user_id', userId).eq('status', 'active')
      ]);

      setPatientDetails({
        conditions: conditions.data || [],
        medications: medications.data || [],
        goals: goals.data || [],
        alerts: alerts.data || [],
        healthData: healthData.data || [],
        rehabPlans: rehabPlans.data || []
      });
    } catch (error) {
      console.error('加载患者详情失败:', error);
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
              <Stethoscope className="w-8 h-8 text-blue-600" />
              医生工作台 - 患者管理系统
            </h1>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600">今日日期:</span>
              <span className="font-semibold text-gray-800">
                {new Date().toLocaleDateString('zh-CN')}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* 左侧：患者列表 */}
          <div className="col-span-12 md:col-span-4 lg:col-span-3">
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-600" />
                患者列表 ({patients.length})
              </h2>
              <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto">
                {patients.map((patient, index) => (
                  <div
                    key={index}
                    onClick={() => setSelectedPatient(patient)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedPatient?.user_id === patient.user_id
                        ? 'bg-blue-50 border-2 border-blue-500'
                        : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                    }`}
                  >
                    <p className="font-semibold text-gray-800">
                      {patient.full_name || '患者' + patient.user_id?.substring(0, 8)}
                    </p>
                    <p className="text-sm text-gray-600">
                      ID: {patient.user_id?.substring(0, 12)}...
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 右侧：患者详情 */}
          <div className="col-span-12 md:col-span-8 lg:col-span-9">
            {patientDetails ? (
              <div className="space-y-6">
                {/* 患者基本信息和健康预警 */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white rounded-lg p-4 shadow-md">
                    <p className="text-sm text-gray-600 mb-1">慢性病数量</p>
                    <p className="text-3xl font-bold text-purple-600">{patientDetails.conditions.length}</p>
                  </div>
                  <div className="bg-white rounded-lg p-4 shadow-md">
                    <p className="text-sm text-gray-600 mb-1">当前用药</p>
                    <p className="text-3xl font-bold text-blue-600">{patientDetails.medications.length}</p>
                  </div>
                  <div className="bg-white rounded-lg p-4 shadow-md">
                    <p className="text-sm text-gray-600 mb-1">待处理预警</p>
                    <p className="text-3xl font-bold text-red-600">{patientDetails.alerts.length}</p>
                  </div>
                </div>

                {/* 健康预警详情 */}
                {patientDetails.alerts.length > 0 && (
                  <div className="bg-white rounded-lg p-6 shadow-md">
                    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                      <AlertCircle className="w-6 h-6 text-red-600" />
                      健康预警
                    </h2>
                    <div className="space-y-3">
                      {patientDetails.alerts.map((alert: any, index: number) => (
                        <div key={index} className="border-l-4 border-red-500 bg-red-50 p-4 rounded">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <p className="font-semibold text-gray-800">{alert.indicator_name} - {alert.alert_type}</p>
                              <p className="text-sm text-gray-600 mt-1">
                                异常值: {alert.abnormal_value} (正常范围: {alert.normal_range})
                              </p>
                              <p className="text-sm text-gray-700 mt-2">
                                <span className="font-semibold">风险评估：</span>{alert.risk_assessment}
                              </p>
                              <p className="text-sm text-blue-600 mt-1">
                                <span className="font-semibold">建议措施：</span>{alert.recommended_actions}
                              </p>
                            </div>
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${
                              alert.severity === 'high' ? 'bg-red-100 text-red-800' :
                              alert.severity === 'medium' ? 'bg-orange-100 text-orange-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {alert.severity === 'high' ? '高风险' :
                               alert.severity === 'medium' ? '中风险' : '低风险'}
                            </span>
                          </div>
                          <div className="mt-3 flex gap-2">
                            <button className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
                              处理预警
                            </button>
                            <button className="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300">
                              查看详情
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 慢性病诊断 */}
                <div className="bg-white rounded-lg p-6 shadow-md">
                  <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <FileText className="w-6 h-6 text-purple-600" />
                    慢性病诊断记录
                  </h2>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">疾病类型</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">严重程度</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">诊断日期</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">主治医生</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">医院</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {patientDetails.conditions.map((cond: any, index: number) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span className="font-medium text-gray-900">
                                {cond.condition_type === 'hypertension' ? '高血压' :
                                 cond.condition_type === 'diabetes' ? '糖尿病' :
                                 cond.condition_type === 'heart_disease' ? '心脏病' :
                                 cond.condition_type === 'arthritis' ? '关节炎' : cond.condition_type}
                              </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                                cond.severity_level === 'severe' ? 'bg-red-100 text-red-800' :
                                cond.severity_level === 'moderate' ? 'bg-orange-100 text-orange-800' :
                                'bg-green-100 text-green-800'
                              }`}>
                                {cond.severity_level === 'severe' ? '严重' :
                                 cond.severity_level === 'moderate' ? '中等' : '轻度'}
                              </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                              {cond.diagnosis_date}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                              {cond.doctor_name}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                              {cond.hospital_name}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                              <button className="text-blue-600 hover:text-blue-800 font-medium">
                                编辑
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* 用药方案 */}
                <div className="bg-white rounded-lg p-6 shadow-md">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">用药方案</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {patientDetails.medications.map((med: any, index: number) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-3">
                          <h3 className="font-semibold text-gray-800">{med.medication_name}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            med.stock_quantity <= med.low_stock_threshold 
                              ? 'bg-orange-100 text-orange-800' 
                              : 'bg-green-100 text-green-800'
                          }`}>
                            库存: {med.stock_quantity}
                          </span>
                        </div>
                        <div className="space-y-1 text-sm text-gray-600">
                          <p>用量: {med.dosage}</p>
                          <p>频率: {med.frequency}</p>
                          <p>服用时间: {med.intake_time}</p>
                          <p>开始日期: {med.start_date}</p>
                        </div>
                        <div className="mt-3 flex gap-2">
                          <button className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
                            调整剂量
                          </button>
                          <button className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                            查看详情
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 康复计划 */}
                {patientDetails.rehabPlans.length > 0 && (
                  <div className="bg-white rounded-lg p-6 shadow-md">
                    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                      <Calendar className="w-6 h-6 text-green-600" />
                      康复训练计划
                    </h2>
                    <div className="space-y-4">
                      {patientDetails.rehabPlans.map((plan: any, index: number) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <h3 className="font-semibold text-gray-800">{plan.plan_name}</h3>
                              <p className="text-sm text-gray-600 mt-1">
                                {plan.exercise_type} · {plan.intensity_level} · {plan.duration_minutes}分钟/次 · 每周{plan.frequency_per_week}次
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-2xl font-bold text-green-600">{Math.round(plan.completion_rate)}%</p>
                              <p className="text-xs text-gray-500">完成度</p>
                            </div>
                          </div>
                          <div className="bg-gray-100 rounded p-3 text-sm text-gray-700">
                            <p className="font-semibold mb-1">训练指导：</p>
                            <p className="whitespace-pre-line">{plan.instructions}</p>
                          </div>
                          <div className="mt-2 bg-yellow-50 rounded p-3 text-sm text-gray-700">
                            <p className="font-semibold mb-1">注意事项：</p>
                            <p>{plan.precautions}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg p-12 shadow-md text-center">
                <p className="text-gray-500">请从左侧选择患者</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
