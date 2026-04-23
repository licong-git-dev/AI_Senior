import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase, HealthData, EmergencyCall, Device } from '../lib/supabase';
import { Home, LogOut, Users, Activity, Bell, TrendingUp, Heart, AlertCircle } from 'lucide-react';
import * as echarts from 'echarts';
import ReactECharts from 'echarts-for-react';

interface FamilyDashboardProps {
  session: any;
}

export default function FamilyDashboard({ session }: FamilyDashboardProps) {
  const navigate = useNavigate();
  const [healthData, setHealthData] = useState<HealthData[]>([]);
  const [emergencyCalls, setEmergencyCalls] = useState<EmergencyCall[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    
    // 订阅实时更新
    const healthChannel = supabase
      .channel('health_data_changes')
      .on('postgres_changes', 
        { event: '*', schema: 'public', table: 'health_data' },
        () => loadHealthData()
      )
      .subscribe();

    const callsChannel = supabase
      .channel('emergency_calls_changes')
      .on('postgres_changes',
        { event: '*', schema: 'public', table: 'emergency_calls' },
        () => loadEmergencyCalls()
      )
      .subscribe();

    return () => {
      healthChannel.unsubscribe();
      callsChannel.unsubscribe();
    };
  }, [session]);

  const loadDashboardData = async () => {
    await Promise.all([
      loadHealthData(),
      loadEmergencyCalls(),
      loadDevices()
    ]);
    setLoading(false);
  };

  const loadHealthData = async () => {
    const { data } = await supabase
      .from('health_data')
      .select('*')
      .eq('user_id', session.user.id)
      .order('measurement_time', { ascending: false })
      .limit(50);

    if (data) {
      setHealthData(data);
    }
  };

  const loadEmergencyCalls = async () => {
    const { data } = await supabase
      .from('emergency_calls')
      .select('*')
      .eq('user_id', session.user.id)
      .order('call_time', { ascending: false })
      .limit(10);

    if (data) {
      setEmergencyCalls(data);
    }
  };

  const loadDevices = async () => {
    const { data } = await supabase
      .from('devices')
      .select('*')
      .eq('user_id', session.user.id);

    if (data) {
      setDevices(data);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  // 血压趋势图表配置
  const getBloodPressureChartOption = () => {
    const bpData = healthData
      .filter(d => d.data_type === 'blood_pressure' && d.systolic_pressure && d.diastolic_pressure)
      .reverse();

    return {
      title: {
        text: '血压趋势',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['收缩压', '舒张压'],
        top: 30
      },
      xAxis: {
        type: 'category',
        data: bpData.map(d => new Date(d.measurement_time).toLocaleDateString('zh-CN'))
      },
      yAxis: {
        type: 'value',
        name: 'mmHg'
      },
      series: [
        {
          name: '收缩压',
          type: 'line',
          data: bpData.map(d => d.systolic_pressure),
          itemStyle: { color: '#ef4444' }
        },
        {
          name: '舒张压',
          type: 'line',
          data: bpData.map(d => d.diastolic_pressure),
          itemStyle: { color: '#3b82f6' }
        }
      ]
    };
  };

  // 心率趋势图表配置
  const getHeartRateChartOption = () => {
    const hrData = healthData
      .filter(d => d.data_type === 'heart_rate' && d.heart_rate)
      .reverse();

    return {
      title: {
        text: '心率趋势',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: hrData.map(d => new Date(d.measurement_time).toLocaleDateString('zh-CN'))
      },
      yAxis: {
        type: 'value',
        name: '次/分'
      },
      series: [
        {
          name: '心率',
          type: 'line',
          data: hrData.map(d => d.heart_rate),
          itemStyle: { color: '#10b981' },
          areaStyle: { opacity: 0.3 }
        }
      ]
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 text-lg">加载数据中...</p>
        </div>
      </div>
    );
  }

  const urgentCalls = emergencyCalls.filter(c => c.response_status === 1);
  const abnormalData = healthData.filter(d => d.abnormal_flag && d.abnormal_flag > 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* 顶部导航 */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">家属监控端</h1>
              <p className="text-gray-600 mt-1">实时监控老人健康状况</p>
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

        {/* 警报通知 */}
        {urgentCalls.length > 0 && (
          <div className="bg-red-50 border-l-4 border-red-500 p-6 mb-6 rounded-lg">
            <div className="flex items-center">
              <AlertCircle className="w-8 h-8 text-red-500 mr-3" />
              <div>
                <h3 className="text-xl font-bold text-red-800">紧急警报</h3>
                <p className="text-red-700">有 {urgentCalls.length} 条待处理的紧急呼叫</p>
              </div>
            </div>
          </div>
        )}

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">健康记录</p>
                <p className="text-3xl font-bold text-gray-800 mt-1">{healthData.length}</p>
              </div>
              <Activity className="w-12 h-12 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">异常数据</p>
                <p className="text-3xl font-bold text-yellow-600 mt-1">{abnormalData.length}</p>
              </div>
              <TrendingUp className="w-12 h-12 text-yellow-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">紧急呼叫</p>
                <p className="text-3xl font-bold text-red-600 mt-1">{emergencyCalls.length}</p>
              </div>
              <Bell className="w-12 h-12 text-red-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">设备状态</p>
                <p className="text-3xl font-bold text-green-600 mt-1">{devices.length}</p>
              </div>
              <Users className="w-12 h-12 text-green-500" />
            </div>
          </div>
        </div>

        {/* 健康数据图表 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {healthData.some(d => d.data_type === 'blood_pressure') && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              {/* @ts-ignore */}
              <ReactECharts 
                option={getBloodPressureChartOption()} 
                style={{ height: '300px' }} 
                echarts={echarts}
              />
            </div>
          )}

          {healthData.some(d => d.data_type === 'heart_rate') && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              {/* @ts-ignore */}
              <ReactECharts 
                option={getHeartRateChartOption()} 
                style={{ height: '300px' }} 
                echarts={echarts}
              />
            </div>
          )}
        </div>

        {/* 最新健康数据列表 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">最新健康数据</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-gray-600">时间</th>
                  <th className="text-left py-3 px-4 text-gray-600">类型</th>
                  <th className="text-left py-3 px-4 text-gray-600">数值</th>
                  <th className="text-left py-3 px-4 text-gray-600">状态</th>
                </tr>
              </thead>
              <tbody>
                {healthData.slice(0, 10).map((data) => (
                  <tr key={data.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm">
                      {new Date(data.measurement_time).toLocaleString('zh-CN')}
                    </td>
                    <td className="py-3 px-4">{data.data_type}</td>
                    <td className="py-3 px-4">
                      {data.systolic_pressure && data.diastolic_pressure
                        ? `${data.systolic_pressure}/${data.diastolic_pressure} mmHg`
                        : data.heart_rate
                        ? `${data.heart_rate} 次/分`
                        : data.data_value
                        ? `${data.data_value} ${data.unit || ''}`
                        : '-'}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        data.abnormal_flag === 2 ? 'bg-red-100 text-red-800' :
                        data.abnormal_flag === 1 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {data.abnormal_flag === 2 ? '异常' :
                         data.abnormal_flag === 1 ? '预警' : '正常'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 紧急呼叫记录 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">紧急呼叫记录</h3>
          <div className="space-y-3">
            {emergencyCalls.map((call) => (
              <div key={call.id} className="border-l-4 border-red-500 pl-4 py-3 bg-red-50 rounded-r-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold text-gray-800">{call.call_type}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      {new Date(call.call_time).toLocaleString('zh-CN')}
                    </p>
                    {call.health_data_snapshot && (
                      <p className="text-xs text-gray-500 mt-1">
                        {JSON.stringify(call.health_data_snapshot).slice(0, 100)}...
                      </p>
                    )}
                  </div>
                  <span className={`px-3 py-1 rounded-lg text-sm font-semibold ${
                    call.response_status === 4 ? 'bg-green-100 text-green-800' :
                    call.response_status === 2 ? 'bg-blue-100 text-blue-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {call.response_status === 4 ? '已完成' :
                     call.response_status === 2 ? '已响应' : '待响应'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
