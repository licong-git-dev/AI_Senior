import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, Activity, Calendar, Download, Filter, RefreshCw } from 'lucide-react';

const DataAnalyticsDashboard = () => {
  const [activeView, setActiveView] = useState('overview');
  const [timeRange, setTimeRange] = useState('7d');
  const [refreshing, setRefreshing] = useState(false);

  const [analyticsData, setAnalyticsData] = useState({
    overview: {
      total_users: 1258,
      active_users: 1089,
      health_alerts: 23,
      service_orders: 156,
      trend: '+12.5%',
      health_score: 87.3,
      satisfaction: 4.7
    },
    health: {
      avg_bp_systolic: 128,
      avg_bp_diastolic: 82,
      avg_heart_rate: 72,
      sleep_quality: 7.8,
      activity_level: 8234,
      medication_compliance: 94.2
    },
    services: {
      nursing_visits: 45,
      escort_services: 28,
      medical_consultations: 67,
      rehabilitation_sessions: 34,
      emergency_calls: 8,
      satisfaction_rate: 96.1
    },
    trends: {
      health_improvement: 15.2,
      service_utilization: 8.7,
      user_retention: 89.3,
      emergency_reduction: -23.4,
      cost_efficiency: 12.1
    }
  });

  const mockChartData = {
    healthTrends: [
      { date: '01-15', bp_systolic: 125, bp_diastolic: 80, heart_rate: 68 },
      { date: '01-16', bp_systolic: 128, bp_diastolic: 82, heart_rate: 72 },
      { date: '01-17', bp_systolic: 130, bp_diastolic: 84, heart_rate: 75 },
      { date: '01-18', bp_systolic: 127, bp_diastolic: 81, heart_rate: 70 },
      { date: '01-19', bp_systolic: 129, bp_diastolic: 83, heart_rate: 73 },
      { date: '01-20', bp_systolic: 126, bp_diastolic: 82, heart_rate: 71 },
      { date: '01-21', bp_systolic: 128, bp_diastolic: 82, heart_rate: 72 }
    ],
    serviceUsage: [
      { service: '护理服务', usage: 85, satisfaction: 4.8 },
      { service: '陪护服务', usage: 72, satisfaction: 4.6 },
      { service: '医疗咨询', usage: 91, satisfaction: 4.9 },
      { service: '康复训练', usage: 65, satisfaction: 4.7 },
      { service: '紧急救援', usage: 45, satisfaction: 4.5 }
    ],
    alertTrends: [
      { date: '01-15', alerts: 5, resolved: 4 },
      { date: '01-16', alerts: 3, resolved: 3 },
      { date: '01-17', alerts: 7, resolved: 6 },
      { date: '01-18', alerts: 2, resolved: 2 },
      { date: '01-19', alerts: 6, resolved: 5 },
      { date: '01-20', alerts: 4, resolved: 4 },
      { date: '01-21', alerts: 8, resolved: 7 }
    ]
  };

  const views = [
    { id: 'overview', name: '总览', icon: BarChart3 },
    { id: 'health', name: '健康分析', icon: Activity },
    { id: 'services', name: '服务分析', icon: Users },
    { id: 'trends', name: '趋势预测', icon: TrendingUp }
  ];

  const handleRefresh = () => {
    setRefreshing(true);
    // 模拟刷新数据
    setTimeout(() => {
      setRefreshing(false);
    }, 2000);
  };

  const downloadReport = () => {
    // 模拟导出报表
    console.log('正在生成报表...');
  };

  const getMetricColor = (value, type) => {
    if (type === 'trend') {
      return value.startsWith('+') || value.startsWith('-') 
        ? value.startsWith('-') ? 'text-red-600' : 'text-green-600'
        : 'text-gray-600';
    }
    return 'text-gray-900';
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">总用户数</p>
              <p className="text-2xl font-semibold text-gray-900">{analyticsData.overview.total_users.toLocaleString()}</p>
              <p className="text-sm text-green-600 flex items-center mt-1">
                <TrendingUp className="h-3 w-3 mr-1" />
                {analyticsData.overview.trend}
              </p>
            </div>
            <Users className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">活跃用户</p>
              <p className="text-2xl font-semibold text-gray-900">{analyticsData.overview.active_users.toLocaleString()}</p>
              <p className="text-sm text-blue-600 mt-1">
                活跃率 {((analyticsData.overview.active_users / analyticsData.overview.total_users) * 100).toFixed(1)}%
              </p>
            </div>
            <Activity className="h-8 w-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">健康评分</p>
              <p className="text-2xl font-semibold text-gray-900">{analyticsData.overview.health_score}</p>
              <p className="text-sm text-purple-600 mt-1">优秀</p>
            </div>
            <Activity className="h-8 w-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">满意度</p>
              <p className="text-2xl font-semibold text-gray-900">{analyticsData.overview.satisfaction}/5.0</p>
              <p className="text-sm text-yellow-600 mt-1">非常满意</p>
            </div>
            <TrendingUp className="h-8 w-8 text-yellow-600" />
          </div>
        </div>
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 健康趋势图 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">健康指标趋势</h3>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-center text-gray-500">
              <BarChart3 className="h-12 w-12 mx-auto mb-2" />
              <p>健康指标趋势图表</p>
              <p className="text-sm">显示7天内血压和心率变化</p>
            </div>
          </div>
        </div>

        {/* 服务使用情况 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">服务使用情况</h3>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-center text-gray-500">
              <Users className="h-12 w-12 mx-auto mb-2" />
              <p>服务使用统计图表</p>
              <p className="text-sm">显示各服务类型的使用频次</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderHealthAnalysis = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">平均血压</h4>
          <div className="text-2xl font-bold text-gray-900">
            {analyticsData.health.avg_bp_systolic}/{analyticsData.health.avg_bp_diastolic}
          </div>
          <p className="text-sm text-gray-600">收缩压/舒张压 mmHg</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">平均心率</h4>
          <div className="text-2xl font-bold text-gray-900">{analyticsData.health.avg_heart_rate}</div>
          <p className="text-sm text-gray-600">次/分钟</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">睡眠质量</h4>
          <div className="text-2xl font-bold text-gray-900">{analyticsData.health.sleep_quality}/10</div>
          <p className="text-sm text-gray-600">综合评分</p>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">详细健康数据</h3>
        <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
          <div className="text-center text-gray-500">
            <Activity className="h-12 w-12 mx-auto mb-2" />
            <p>详细健康数据分析图表</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderServiceAnalysis = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">护理服务</h4>
          <div className="text-2xl font-bold text-blue-600">{analyticsData.services.nursing_visits}</div>
          <p className="text-sm text-gray-600">本月服务次数</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">陪护服务</h4>
          <div className="text-2xl font-bold text-green-600">{analyticsData.services.escort_services}</div>
          <p className="text-sm text-gray-600">本月服务次数</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">医疗咨询</h4>
          <div className="text-2xl font-bold text-purple-600">{analyticsData.services.medical_consultations}</div>
          <p className="text-sm text-gray-600">本月咨询次数</p>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">服务分析详情</h3>
        <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
          <div className="text-center text-gray-500">
            <Users className="h-12 w-12 mx-auto mb-2" />
            <p>服务分析详细图表</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderTrends = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">健康改善</h4>
          <div className="text-2xl font-bold text-green-600">+{analyticsData.trends.health_improvement}%</div>
          <p className="text-sm text-gray-600">本月较上月</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">服务利用</h4>
          <div className="text-2xl font-bold text-blue-600">+{analyticsData.trends.service_utilization}%</div>
          <p className="text-sm text-gray-600">本月较上月</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">用户留存</h4>
          <div className="text-2xl font-bold text-purple-600">{analyticsData.trends.user_retention}%</div>
          <p className="text-sm text-gray-600">用户留存率</p>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">趋势预测图表</h3>
        <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
          <div className="text-center text-gray-500">
            <TrendingUp className="h-12 w-12 mx-auto mb-2" />
            <p>未来30天趋势预测图表</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* 页面标题和控制 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <BarChart3 className="h-8 w-8 mr-3 text-purple-600" />
            数据分析仪表盘
          </h1>
          <p className="text-gray-600 mt-2">
            实时数据分析、趋势预测和可视化报表展示
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="1d">最近1天</option>
            <option value="7d">最近7天</option>
            <option value="30d">最近30天</option>
            <option value="90d">最近90天</option>
          </select>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 inline mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            刷新数据
          </button>
          <button
            onClick={downloadReport}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Download className="h-4 w-4 inline mr-2" />
            导出报表
          </button>
        </div>
      </div>

      {/* 视图切换标签 */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {views.map((view) => (
              <button
                key={view.id}
                onClick={() => setActiveView(view.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                  activeView === view.id
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <view.icon className="h-4 w-4 mr-2" />
                {view.name}
              </button>
            ))}
          </nav>
        </div>

        {/* 内容区域 */}
        <div className="p-6">
          {activeView === 'overview' && renderOverview()}
          {activeView === 'health' && renderHealthAnalysis()}
          {activeView === 'services' && renderServiceAnalysis()}
          {activeView === 'trends' && renderTrends()}
        </div>
      </div>

      {/* 数据源说明 */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">数据分析说明</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700">
          <div>
            <h4 className="font-medium mb-2">实时数据处理</h4>
            <p>每分钟更新数据，提供最新的健康状态和服务情况</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">AI预测模型</h4>
            <p>基于机器学习算法预测健康趋势和服务需求</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">可视化报表</h4>
            <p>多种图表类型展示，支持自定义时间范围和数据维度</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataAnalyticsDashboard;