import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase, EmergencyCall, CarePlan, HealthData } from '../lib/supabase';
import { Home, LogOut, Users, AlertCircle, CheckCircle, Clock, FileText } from 'lucide-react';

interface CareDashboardProps {
  session: any;
}

export default function CareDashboard({ session }: CareDashboardProps) {
  const navigate = useNavigate();
  const [emergencyCalls, setEmergencyCalls] = useState<EmergencyCall[]>([]);
  const [carePlans, setCarePlans] = useState<CarePlan[]>([]);
  const [allHealthData, setAllHealthData] = useState<HealthData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCall, setSelectedCall] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();

    // 订阅实时更新
    const callsChannel = supabase
      .channel('care_emergency_calls')
      .on('postgres_changes',
        { event: '*', schema: 'public', table: 'emergency_calls' },
        () => loadEmergencyCalls()
      )
      .subscribe();

    return () => {
      callsChannel.unsubscribe();
    };
  }, []);

  const loadDashboardData = async () => {
    await Promise.all([
      loadEmergencyCalls(),
      loadCarePlans(),
      loadAllHealthData()
    ]);
    setLoading(false);
  };

  const loadEmergencyCalls = async () => {
    const { data } = await supabase
      .from('emergency_calls')
      .select('*')
      .order('call_time', { ascending: false })
      .limit(50);

    if (data) {
      setEmergencyCalls(data);
    }
  };

  const loadCarePlans = async () => {
    const { data } = await supabase
      .from('care_plans')
      .select('*')
      .eq('status', 1)
      .order('created_at', { ascending: false });

    if (data) {
      setCarePlans(data);
    }
  };

  const loadAllHealthData = async () => {
    const { data } = await supabase
      .from('health_data')
      .select('*')
      .gte('abnormal_flag', 1)
      .order('measurement_time', { ascending: false })
      .limit(100);

    if (data) {
      setAllHealthData(data);
    }
  };

  const handleRespondToCall = async (callId: string) => {
    try {
      const { error } = await supabase.functions.invoke('emergency-call-handler', {
        body: {
          action: 'respond',
          call_id: callId,
          responder_id: session.user.id
        }
      });

      if (error) throw error;

      alert('已成功响应呼叫');
      loadEmergencyCalls();
    } catch (error) {
      console.error('响应呼叫失败:', error);
      alert('响应失败，请重试');
    }
  };

  const handleCompleteCall = async (callId: string) => {
    try {
      const { error } = await supabase.functions.invoke('emergency-call-handler', {
        body: {
          action: 'complete',
          call_id: callId
        }
      });

      if (error) throw error;

      alert('已标记为完成');
      loadEmergencyCalls();
    } catch (error) {
      console.error('完成呼叫失败:', error);
      alert('操作失败，请重试');
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-pink-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 text-lg">加载数据中...</p>
        </div>
      </div>
    );
  }

  const urgentCalls = emergencyCalls.filter(c => c.response_status === 1);
  const respondedCalls = emergencyCalls.filter(c => c.response_status === 2);
  const completedCalls = emergencyCalls.filter(c => c.response_status === 4);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* 顶部导航 */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">护理管理端</h1>
              <p className="text-gray-600 mt-1">患者监护与紧急响应管理</p>
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                <Home className="w-5 h-5" />
                <span>首页</span>
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                <LogOut className="w-5 h-5" />
                <span>退出</span>
              </button>
            </div>
          </div>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">待响应</p>
                <p className="text-3xl font-bold text-red-600 mt-1">{urgentCalls.length}</p>
              </div>
              <AlertCircle className="w-12 h-12 text-red-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">处理中</p>
                <p className="text-3xl font-bold text-blue-600 mt-1">{respondedCalls.length}</p>
              </div>
              <Clock className="w-12 h-12 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">已完成</p>
                <p className="text-3xl font-bold text-green-600 mt-1">{completedCalls.length}</p>
              </div>
              <CheckCircle className="w-12 h-12 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">护理计划</p>
                <p className="text-3xl font-bold text-purple-600 mt-1">{carePlans.length}</p>
              </div>
              <FileText className="w-12 h-12 text-purple-500" />
            </div>
          </div>
        </div>

        {/* 紧急呼叫处理 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <AlertCircle className="w-6 h-6 text-red-500 mr-2" />
            紧急呼叫管理
          </h3>
          
          <div className="space-y-4">
            {urgentCalls.length === 0 ? (
              <p className="text-gray-500 text-center py-8">暂无待处理的紧急呼叫</p>
            ) : (
              urgentCalls.map((call) => (
                <div key={call.id} className="border-2 border-red-500 rounded-lg p-4 bg-red-50">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="px-3 py-1 bg-red-600 text-white rounded-full text-sm font-bold">
                          紧急
                        </span>
                        <h4 className="text-lg font-bold text-gray-800">{call.call_type}</h4>
                      </div>
                      <p className="text-gray-700 mb-1">
                        <strong>呼叫时间:</strong> {new Date(call.call_time).toLocaleString('zh-CN')}
                      </p>
                      <p className="text-gray-700 mb-1">
                        <strong>触发源:</strong> {call.trigger_source}
                      </p>
                      <p className="text-gray-700">
                        <strong>严重程度:</strong> {call.severity_level === 3 ? '高' : call.severity_level === 2 ? '中' : '低'}
                      </p>
                      {call.location_latitude && call.location_longitude && (
                        <p className="text-gray-700 mt-1">
                          <strong>位置:</strong> {call.location_latitude.toFixed(6)}, {call.location_longitude.toFixed(6)}
                        </p>
                      )}
                      {call.health_data_snapshot && (
                        <div className="mt-2 p-3 bg-white rounded border">
                          <p className="text-sm font-semibold text-gray-700 mb-1">健康数据快照:</p>
                          <pre className="text-xs text-gray-600 overflow-x-auto">
                            {JSON.stringify(call.health_data_snapshot, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => handleRespondToCall(call.id)}
                      className="ml-4 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-bold whitespace-nowrap"
                    >
                      立即响应
                    </button>
                  </div>
                </div>
              ))
            )}

            {respondedCalls.length > 0 && (
              <>
                <h4 className="text-lg font-bold text-gray-700 mt-6 mb-3">处理中的呼叫</h4>
                {respondedCalls.map((call) => (
                  <div key={call.id} className="border border-blue-300 rounded-lg p-4 bg-blue-50">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="px-3 py-1 bg-blue-600 text-white rounded-full text-sm font-bold">
                            处理中
                          </span>
                          <h4 className="text-lg font-bold text-gray-800">{call.call_type}</h4>
                        </div>
                        <p className="text-gray-700">
                          <strong>响应时间:</strong> {call.response_time ? new Date(call.response_time).toLocaleString('zh-CN') : '-'}
                        </p>
                      </div>
                      <button
                        onClick={() => handleCompleteCall(call.id)}
                        className="ml-4 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-bold whitespace-nowrap"
                      >
                        标记完成
                      </button>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>

        {/* 异常健康数据监控 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">异常健康数据监控</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-gray-600">时间</th>
                  <th className="text-left py-3 px-4 text-gray-600">患者ID</th>
                  <th className="text-left py-3 px-4 text-gray-600">数据类型</th>
                  <th className="text-left py-3 px-4 text-gray-600">数值</th>
                  <th className="text-left py-3 px-4 text-gray-600">异常等级</th>
                  <th className="text-left py-3 px-4 text-gray-600">AI分析</th>
                </tr>
              </thead>
              <tbody>
                {allHealthData.slice(0, 20).map((data) => (
                  <tr key={data.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm">
                      {new Date(data.measurement_time).toLocaleString('zh-CN')}
                    </td>
                    <td className="py-3 px-4 text-sm font-mono">
                      {data.user_id.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-4">{data.data_type}</td>
                    <td className="py-3 px-4">
                      {data.systolic_pressure && data.diastolic_pressure
                        ? `${data.systolic_pressure}/${data.diastolic_pressure}`
                        : data.heart_rate || data.data_value || '-'}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        data.abnormal_flag === 2 ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {data.abnormal_flag === 2 ? '严重异常' : '预警'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm max-w-xs truncate">
                      {data.ai_analysis_result && typeof data.ai_analysis_result === 'object'
                        ? JSON.stringify(data.ai_analysis_result)
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 护理计划列表 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <FileText className="w-6 h-6 text-purple-500 mr-2" />
            活跃护理计划
          </h3>
          <div className="space-y-4">
            {carePlans.length === 0 ? (
              <p className="text-gray-500 text-center py-8">暂无活跃的护理计划</p>
            ) : (
              carePlans.map((plan) => (
                <div key={plan.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-lg font-bold text-gray-800">{plan.plan_name}</h4>
                      <p className="text-gray-600 mt-1">
                        <strong>类型:</strong> {
                          plan.plan_type === 1 ? '健康护理' :
                          plan.plan_type === 2 ? '生活照料' :
                          plan.plan_type === 3 ? '康复训练' : '心理关怀'
                        }
                      </p>
                      <p className="text-gray-600">
                        <strong>开始日期:</strong> {new Date(plan.start_date).toLocaleDateString('zh-CN')}
                      </p>
                      {plan.description && (
                        <p className="text-gray-600 mt-2">{plan.description}</p>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-lg text-sm font-semibold ${
                      plan.risk_level === 3 ? 'bg-red-100 text-red-800' :
                      plan.risk_level === 2 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {plan.risk_level === 3 ? '高风险' :
                       plan.risk_level === 2 ? '中风险' : '低风险'}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
