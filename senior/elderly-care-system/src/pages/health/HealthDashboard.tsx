import { useNavigate } from 'react-router-dom';
import { Heart, Users, Stethoscope, ClipboardList, ArrowLeft, Sparkles } from 'lucide-react';

export default function HealthDashboard({ session }: { session: any }) {
  const navigate = useNavigate();

  const roles = [
    {
      id: 'elderly',
      title: '老人端',
      description: '简化操作，大字体显示',
      features: ['健康数据查看', '用药提醒', '一键求助'],
      icon: Heart,
      color: 'from-rose-500 to-pink-600',
      bgColor: 'bg-rose-50',
      path: '/health/elderly'
    },
    {
      id: 'family',
      title: '家属端',
      description: '实时监控，数据可视化',
      features: ['健康监控仪表盘', 'AI智能分析', '预警提醒'],
      icon: Users,
      color: 'from-blue-500 to-cyan-600',
      bgColor: 'bg-blue-50',
      path: '/health/family'
    },
    {
      id: 'doctor',
      title: '医生端',
      description: '患者管理，专业分析',
      features: ['患者档案管理', '健康数据分析', '用药方案管理'],
      icon: Stethoscope,
      color: 'from-green-500 to-emerald-600',
      bgColor: 'bg-green-50',
      path: '/health/doctor'
    },
    {
      id: 'caregiver',
      title: '护理端',
      description: '任务执行，康复指导',
      features: ['护理任务清单', '用药执行确认', '康复训练指导'],
      icon: ClipboardList,
      color: 'from-purple-500 to-violet-600',
      bgColor: 'bg-purple-50',
      path: '/health/caregiver'
    },
    {
      id: 'prediction',
      title: 'AI风险预测',
      description: '智能健康风险评估',
      features: ['多维度风险评估', '95%预测准确率', '个性化健康建议'],
      icon: Sparkles,
      color: 'from-cyan-500 to-blue-600',
      bgColor: 'bg-cyan-50',
      path: '/health/prediction'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-cyan-50 to-blue-50">
      <div className="container mx-auto px-4 py-12">
        {/* 头部 */}
        <div className="text-center mb-12">
          <button
            onClick={() => navigate('/')}
            className="inline-flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            返回首页
          </button>
          
          <div className="inline-flex items-center gap-3 mb-4">
            <Sparkles className="w-10 h-10 text-teal-600" />
            <h1 className="text-4xl font-bold text-gray-800">智能健康管理系统</h1>
          </div>
          <p className="text-xl text-gray-600">AI赋能 · 多角色协同 · 全方位健康管理</p>
          <div className="mt-4 inline-block px-4 py-2 bg-teal-100 text-teal-800 rounded-full text-sm font-medium">
            已集成阿里云通义千问AI · 170+条健康数据
          </div>
        </div>

        {/* 角色选择卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {roles.map((role) => {
            const Icon = role.icon;
            return (
              <div
                key={role.id}
                className={`${role.bgColor} rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 cursor-pointer overflow-hidden group`}
                onClick={() => navigate(role.path)}
              >
                <div className={`h-2 bg-gradient-to-r ${role.color}`}></div>
                <div className="p-8">
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`p-4 bg-gradient-to-r ${role.color} rounded-xl shadow-lg group-hover:scale-110 transition-transform`}>
                      <Icon className="w-8 h-8 text-white" />
                    </div>
                    <div className="flex-1">
                      <h2 className="text-2xl font-bold text-gray-800 mb-2">{role.title}</h2>
                      <p className="text-gray-600">{role.description}</p>
                    </div>
                  </div>

                  <div className="space-y-3 mb-6">
                    {role.features.map((feature, index) => (
                      <div key={index} className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${role.color}`}></div>
                        <span className="text-gray-700">{feature}</span>
                      </div>
                    ))}
                  </div>

                  <button 
                    className={`w-full py-3 bg-gradient-to-r ${role.color} text-white rounded-lg font-semibold hover:shadow-lg transition-all`}
                  >
                    进入{role.title}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* 功能亮点 */}
        <div className="mt-16 max-w-4xl mx-auto">
          <h3 className="text-2xl font-bold text-center text-gray-800 mb-8">核心功能特性</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-teal-500 to-cyan-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">AI智能分析</h4>
              <p className="text-sm text-gray-600">阿里云通义千问AI驱动，智能健康风险评估与个性化建议</p>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">实时健康监测</h4>
              <p className="text-sm text-gray-600">慢性病监测、用药管理、康复计划全方位覆盖</p>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-6 h-6 text-white" />
              </div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">多角色协同</h4>
              <p className="text-sm text-gray-600">老人、家属、医生、护理四端协同，提供全方位健康管理</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
