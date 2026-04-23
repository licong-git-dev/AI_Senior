import React from 'react';
import { Brain, Mic, AlertTriangle, BarChart3, Smartphone, Sparkles, Shield, Zap } from 'lucide-react';

const HomePage = () => {
  const features = [
    {
      icon: Brain,
      title: '智能推荐引擎',
      description: '基于AI算法的个性化健康建议、服务推荐和内容推荐系统',
      status: '开发中',
      color: 'blue'
    },
    {
      icon: Mic,
      title: '语音助手系统',
      description: '语音交互、语音识别和语音合成的全功能语音助手',
      status: '开发中',
      color: 'green'
    },
    {
      icon: AlertTriangle,
      title: '智能预警系统',
      description: '健康风险预测、异常行为检测和预防性告警功能',
      status: '开发中',
      color: 'red'
    },
    {
      icon: BarChart3,
      title: '数据分析仪表盘',
      description: '实时数据分析、趋势预测和可视化报表展示',
      status: '开发中',
      color: 'purple'
    },
    {
      icon: Smartphone,
      title: '移动端应用',
      description: '基于React Native开发的跨平台移动APP',
      status: '计划中',
      color: 'indigo'
    }
  ];

  const stats = [
    { label: '功能模块', value: '5+', icon: Sparkles },
    { label: 'AI算法', value: '10+', icon: Brain },
    { label: '数据源', value: '15+', icon: Shield },
    { label: '实时处理', value: '24/7', icon: Zap }
  ];

  return (
    <div className="space-y-8">
      {/* 欢迎区域 */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          智能化新功能平台
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          基于人工智能的养老智能体系统增强模块，提供个性化推荐、语音交互、
          智能预警和数据分析等全方位智能化服务
        </p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-lg shadow-lg p-6 text-center">
            <stat.icon className="h-8 w-8 text-blue-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
            <div className="text-gray-600">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* 功能模块展示 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feature, index) => (
          <div key={index} className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <feature.icon className={`h-10 w-10 text-${feature.color}-600`} />
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  feature.status === '开发中' 
                    ? 'bg-blue-100 text-blue-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {feature.status}
                </span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600">
                {feature.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* 技术特色 */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-8 text-white">
        <h2 className="text-2xl font-bold text-center mb-6">技术特色</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <Brain className="h-12 w-12 mx-auto mb-3" />
            <h3 className="text-lg font-semibold mb-2">AI驱动</h3>
            <p className="text-blue-100">
              运用机器学习和深度学习技术，实现智能决策和个性化服务
            </p>
          </div>
          <div className="text-center">
            <Shield className="h-12 w-12 mx-auto mb-3" />
            <h3 className="text-lg font-semibold mb-2">安全可靠</h3>
            <p className="text-blue-100">
              多层安全防护机制，确保用户数据安全和隐私保护
            </p>
          </div>
          <div className="text-center">
            <Zap className="h-12 w-12 mx-auto mb-3" />
            <h3 className="text-lg font-semibold mb-2">实时响应</h3>
            <p className="text-blue-100">
              高性能架构设计，实现毫秒级响应和实时数据处理
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;