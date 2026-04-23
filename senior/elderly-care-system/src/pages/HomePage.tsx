import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { Activity, Heart, Phone, Shield, Users, Bell } from 'lucide-react';

interface HomePageProps {
  session: any;
}

export default function HomePage({ session }: HomePageProps) {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) throw error;

      if (data.user) {
        // 默认跳转到家属端
        navigate('/family');
      }
    } catch (error: any) {
      setError(error.message || '登录失败，请检查邮箱和密码');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async () => {
    setLoading(true);
    setError('');

    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
      });

      if (error) throw error;

      alert('注册成功！请查收邮箱验证邮件。');
    } catch (error: any) {
      setError(error.message || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  if (session) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2 text-center">养老智能体安全监护系统</h1>
            <p className="text-gray-600 mb-8 text-center">武汉市江岸区仁义社区试点项目</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <button
                onClick={() => navigate('/elderly')}
                className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl p-8 shadow-lg transform transition hover:scale-105"
              >
                <Shield className="w-16 h-16 mx-auto mb-4" />
                <h2 className="text-2xl font-bold mb-2">老人端</h2>
                <p className="text-green-50">简化操作，大字体显示</p>
              </button>

              <button
                onClick={() => navigate('/family')}
                className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white rounded-xl p-8 shadow-lg transform transition hover:scale-105"
              >
                <Users className="w-16 h-16 mx-auto mb-4" />
                <h2 className="text-2xl font-bold mb-2">家属端</h2>
                <p className="text-blue-50">实时监控，数据可视化</p>
              </button>

              <button
                onClick={() => navigate('/care')}
                className="bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white rounded-xl p-8 shadow-lg transform transition hover:scale-105"
              >
                <Activity className="w-16 h-16 mx-auto mb-4" />
                <h2 className="text-2xl font-bold mb-2">护理端</h2>
                <p className="text-purple-50">患者管理，报警处理</p>
              </button>
            </div>

            {/* 陪诊管理系统区域 */}
            <div className="mt-8 border-t pt-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-2 text-center">上门陪诊管理系统</h2>
              <p className="text-gray-600 mb-6 text-center">商业增值功能 - 专业陪诊服务</p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <button
                  onClick={() => navigate('/escort/booking')}
                  className="bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-600 hover:to-teal-700 text-white rounded-xl p-6 shadow-lg transform transition hover:scale-105"
                >
                  <Heart className="w-12 h-12 mx-auto mb-3" />
                  <h3 className="text-xl font-bold mb-1">陪诊预约</h3>
                  <p className="text-cyan-50 text-sm">老人端预约陪诊服务</p>
                </button>

                <button
                  onClick={() => navigate('/escort/worker')}
                  className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white rounded-xl p-6 shadow-lg transform transition hover:scale-105"
                >
                  <Users className="w-12 h-12 mx-auto mb-3" />
                  <h3 className="text-xl font-bold mb-1">陪诊师端</h3>
                  <p className="text-orange-50 text-sm">接单管理与服务跟踪</p>
                </button>

                <button
                  onClick={() => navigate('/escort/management')}
                  className="bg-gradient-to-r from-rose-500 to-pink-600 hover:from-rose-600 hover:to-pink-700 text-white rounded-xl p-6 shadow-lg transform transition hover:scale-105"
                >
                  <Activity className="w-12 h-12 mx-auto mb-3" />
                  <h3 className="text-xl font-bold mb-1">管理中心</h3>
                  <p className="text-rose-50 text-sm">订单调度与数据分析</p>
                </button>
              </div>
            </div>

            {/* 健康管理系统区域 */}
            <div className="mt-8 border-t pt-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-2 text-center">健康管理系统</h2>
              <p className="text-gray-600 mb-6 text-center">全面健康监测与慢性病管理</p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <button
                  onClick={() => navigate('/health')}
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl p-6 shadow-lg transform transition hover:scale-105"
                >
                  <Heart className="w-12 h-12 mx-auto mb-3" />
                  <h3 className="text-xl font-bold mb-1">健康仪表盘</h3>
                  <p className="text-green-50 text-sm">慢性病监控与用药管理</p>
                </button>

                <button
                  onClick={() => navigate('/health')}
                  className="bg-gradient-to-r from-blue-500 to-sky-600 hover:from-blue-600 hover:to-sky-700 text-white rounded-xl p-6 shadow-lg transform transition hover:scale-105"
                >
                  <Activity className="w-12 h-12 mx-auto mb-3" />
                  <h3 className="text-xl font-bold mb-1">健康分析</h3>
                  <p className="text-blue-50 text-sm">数据分析与趋势预测</p>
                </button>

                <button
                  onClick={() => navigate('/health')}
                  className="bg-gradient-to-r from-purple-500 to-violet-600 hover:from-purple-600 hover:to-violet-700 text-white rounded-xl p-6 shadow-lg transform transition hover:scale-105"
                >
                  <Users className="w-12 h-12 mx-auto mb-3" />
                  <h3 className="text-xl font-bold mb-1">康复训练</h3>
                  <p className="text-purple-50 text-sm">个性化康复计划指导</p>
                </button>
              </div>
            </div>

            {/* 情感陪伴系统区域 */}
            <div className="mt-8 border-t pt-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-2 text-center">情感陪伴系统</h2>
              <p className="text-gray-600 mb-6 text-center">AI智能陪伴 - 温暖关怀与心理支持</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <button
                  onClick={() => navigate('/companion/chat')}
                  className="bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white rounded-xl p-6 shadow-lg transform transition hover:scale-105"
                >
                  <Heart className="w-12 h-12 mx-auto mb-3" />
                  <h3 className="text-xl font-bold mb-1">AI智能陪伴</h3>
                  <p className="text-blue-50 text-sm">7×24小时温暖对话陪伴</p>
                </button>

                <button
                  onClick={() => navigate('/companion')}
                  className="bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white rounded-xl p-6 shadow-lg transform transition hover:scale-105"
                >
                  <Users className="w-12 h-12 mx-auto mb-3" />
                  <h3 className="text-xl font-bold mb-1">更多功能</h3>
                  <p className="text-purple-50 text-sm">认知训练 · 虚拟宠物 · 内容推荐</p>
                </button>
              </div>
            </div>

            <div className="mt-8 text-center">
              <button
                onClick={() => supabase.auth.signOut()}
                className="text-gray-600 hover:text-gray-800 underline"
              >
                退出登录
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* 演示版本横幅 */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 shadow-lg">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Bell className="h-5 w-5 animate-pulse" />
              <p className="text-sm font-medium">
                想体验完整功能？访问<span className="font-bold mx-1">免登录演示版本</span>，包含50+老人档案、100+健康记录、实时数据可视化
              </p>
            </div>
            <button
              onClick={() => navigate('/demo')}
              className="px-5 py-2 bg-white text-indigo-600 font-semibold rounded-lg hover:bg-indigo-50 transition-colors shadow-md text-sm"
            >
              立即体验演示
            </button>
          </div>
        </div>
      </div>
      
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-6xl mx-auto">
          {/* 头部横幅 */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-800 mb-4">养老智能体安全监护系统</h1>
            <p className="text-xl text-gray-600">武汉市江岸区仁义社区试点项目</p>
            <p className="text-lg text-gray-500 mt-2">为788名老人提供全天候安全监护服务</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* 登录表单 */}
            <div className="bg-white rounded-2xl shadow-2xl p-8">
              <h2 className="text-3xl font-bold text-gray-800 mb-6">系统登录</h2>
              
              <form onSubmit={handleLogin} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    邮箱地址
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-lg"
                    placeholder="请输入邮箱"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    密码
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-lg"
                    placeholder="请输入密码"
                    required
                  />
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg text-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? '登录中...' : '登录'}
                </button>

                <button
                  type="button"
                  onClick={handleSignUp}
                  disabled={loading}
                  className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-3 px-6 rounded-lg text-lg transition disabled:opacity-50"
                >
                  注册新账户
                </button>
              </form>
            </div>

            {/* 功能介绍 */}
            <div className="space-y-6">
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <Heart className="w-12 h-12 text-red-500" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-xl font-bold text-gray-800 mb-2">生命体征监测</h3>
                    <p className="text-gray-600">24小时实时监测血压、心率、血糖等关键健康指标</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <Bell className="w-12 h-12 text-yellow-500" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-xl font-bold text-gray-800 mb-2">跌倒检测报警</h3>
                    <p className="text-gray-600">智能跌倒检测算法，自动触发紧急呼叫</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <Phone className="w-12 h-12 text-green-500" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-xl font-bold text-gray-800 mb-2">紧急呼叫响应</h3>
                    <p className="text-gray-600">一键紧急呼叫，护理人员快速响应</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <Activity className="w-12 h-12 text-indigo-500" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-xl font-bold text-gray-800 mb-2">健康数据分析</h3>
                    <p className="text-gray-600">AI智能分析，生成个性化护理建议</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
