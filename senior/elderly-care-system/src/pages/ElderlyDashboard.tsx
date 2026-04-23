import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase, HealthData, EmergencyCall } from '../lib/supabase';
import { Phone, Heart, Activity, Home, LogOut, AlertCircle } from 'lucide-react';

interface ElderlyDashboardProps {
  session: any;
}

export default function ElderlyDashboard({ session }: ElderlyDashboardProps) {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<any>(null);
  const [latestHealth, setLatestHealth] = useState<HealthData | null>(null);
  const [emergencyCalls, setEmergencyCalls] = useState<EmergencyCall[]>([]);
  const [calling, setCalling] = useState(false);

  useEffect(() => {
    loadUserData();
  }, [session]);

  const loadUserData = async () => {
    if (!session?.user?.id) return;

    // 加载用户档案
    const { data: profileData } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', session.user.id)
      .maybeSingle();

    if (profileData) {
      setProfile(profileData);
    }

    // 加载最新健康数据
    const { data: healthData } = await supabase
      .from('health_data')
      .select('*')
      .eq('user_id', session.user.id)
      .order('measurement_time', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (healthData) {
      setLatestHealth(healthData);
    }

    // 加载紧急呼叫记录
    const { data: callsData } = await supabase
      .from('emergency_calls')
      .select('*')
      .eq('user_id', session.user.id)
      .order('call_time', { ascending: false })
      .limit(5);

    if (callsData) {
      setEmergencyCalls(callsData);
    }
  };

  const handleEmergencyCall = async () => {
    if (calling) return;
    
    setCalling(true);
    try {
      const { data, error } = await supabase.functions.invoke('emergency-call-handler', {
        body: {
          action: 'create',
          user_id: session.user.id,
          call_type: 'manual_emergency',
          severity_level: 3
        }
      });

      if (error) throw error;

      alert('紧急呼叫已发送！护理人员将尽快响应。');
      loadUserData();
    } catch (error) {
      console.error('紧急呼叫失败:', error);
      alert('呼叫失败，请重试或直接拨打紧急联系人电话');
    } finally {
      setCalling(false);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* 顶部导航 */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-gray-800">老人端</h1>
              <p className="text-2xl text-gray-600 mt-2">
                您好，{profile?.real_name || '用户'}
              </p>
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 px-6 py-3 bg-gray-100 hover:bg-gray-200 rounded-xl text-xl"
              >
                <Home className="w-6 h-6" />
                <span>首页</span>
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-6 py-3 bg-gray-100 hover:bg-gray-200 rounded-xl text-xl"
              >
                <LogOut className="w-6 h-6" />
                <span>退出</span>
              </button>
            </div>
          </div>
        </div>

        {/* 紧急呼叫按钮 */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
          <button
            onClick={handleEmergencyCall}
            disabled={calling}
            className="w-full bg-red-500 hover:bg-red-600 text-white rounded-2xl p-12 shadow-2xl transform transition hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Phone className="w-24 h-24 mx-auto mb-4" />
            <h2 className="text-5xl font-bold mb-2">
              {calling ? '呼叫中...' : '紧急呼叫'}
            </h2>
            <p className="text-2xl text-red-50">点击此处发送紧急求助</p>
          </button>
        </div>

        {/* 健康状态卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex items-center mb-4">
              <Heart className="w-12 h-12 text-red-500 mr-3" />
              <h3 className="text-3xl font-bold text-gray-800">最新健康数据</h3>
            </div>
            
            {latestHealth ? (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-2xl text-gray-600">数据类型</span>
                  <span className="text-2xl font-semibold">{latestHealth.data_type}</span>
                </div>
                {latestHealth.systolic_pressure && (
                  <div className="flex justify-between items-center">
                    <span className="text-2xl text-gray-600">血压</span>
                    <span className="text-2xl font-semibold">
                      {latestHealth.systolic_pressure}/{latestHealth.diastolic_pressure} mmHg
                    </span>
                  </div>
                )}
                {latestHealth.heart_rate && (
                  <div className="flex justify-between items-center">
                    <span className="text-2xl text-gray-600">心率</span>
                    <span className="text-2xl font-semibold">{latestHealth.heart_rate} 次/分</span>
                  </div>
                )}
                <div className="flex justify-between items-center">
                  <span className="text-2xl text-gray-600">测量时间</span>
                  <span className="text-xl text-gray-500">
                    {new Date(latestHealth.measurement_time).toLocaleString('zh-CN')}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-2xl text-gray-500">暂无健康数据</p>
            )}
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex items-center mb-4">
              <Activity className="w-12 h-12 text-green-500 mr-3" />
              <h3 className="text-3xl font-bold text-gray-800">今日状态</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-2xl text-gray-600">健康评分</span>
                <span className="text-3xl font-bold text-green-600">良好</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-2xl text-gray-600">异常提醒</span>
                <span className="text-2xl font-semibold">{emergencyCalls.length} 条</span>
              </div>
            </div>
          </div>
        </div>

        {/* 紧急联系人 */}
        {profile?.emergency_contact_name && (
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h3 className="text-3xl font-bold text-gray-800 mb-6">紧急联系人</h3>
            <div className="flex justify-between items-center">
              <div>
                <p className="text-2xl font-semibold">{profile.emergency_contact_name}</p>
                <p className="text-xl text-gray-600 mt-2">{profile.emergency_contact_phone}</p>
              </div>
              <a
                href={`tel:${profile.emergency_contact_phone}`}
                className="bg-green-500 hover:bg-green-600 text-white px-8 py-4 rounded-xl text-2xl font-bold"
              >
                拨打电话
              </a>
            </div>
          </div>
        )}

        {/* 最近呼叫记录 */}
        {emergencyCalls.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-8 mt-6">
            <h3 className="text-3xl font-bold text-gray-800 mb-6">最近呼叫记录</h3>
            <div className="space-y-4">
              {emergencyCalls.map((call) => (
                <div key={call.id} className="border-l-4 border-red-500 pl-6 py-4 bg-red-50 rounded-r-xl">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-xl font-semibold text-gray-800">{call.call_type}</p>
                      <p className="text-lg text-gray-600 mt-1">
                        {new Date(call.call_time).toLocaleString('zh-CN')}
                      </p>
                    </div>
                    <span className={`px-4 py-2 rounded-lg text-lg font-semibold ${
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
        )}
      </div>
    </div>
  );
}
