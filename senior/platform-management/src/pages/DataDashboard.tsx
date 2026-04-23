import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { ArrowLeft, TrendingUp, Users, Activity, AlertCircle } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

export default function DataDashboard() {
  const [analytics, setAnalytics] = useState<any[]>([]);
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalCommunities: 0,
    totalProviders: 0,
    platformUtilization: 85.5
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // 加载数据分析记录
      const { data: analyticsData } = await supabase
        .from('data_analytics')
        .select('*')
        .order('analysis_date', { ascending: false })
        .limit(100);

      setAnalytics(analyticsData || []);

      // 加载统计数据
      const [usersResult, communitiesResult, providersResult] = await Promise.all([
        supabase.from('profiles').select('count'),
        supabase.from('communities').select('count'),
        supabase.from('service_providers').select('count')
      ]);

      setStats({
        totalUsers: usersResult.data?.[0]?.count || 0,
        totalCommunities: communitiesResult.data?.[0]?.count || 10,
        totalProviders: providersResult.data?.[0]?.count || 8,
        platformUtilization: 85.5
      });

      // 调用实时大屏更新函数
      await supabase.functions.invoke('real-time-dashboard-updater', {
        body: { metrics: ['all'] }
      });

    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 用户活跃度趋势图
  const userActivityOption = {
    title: { text: '用户活跃度趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月']
    },
    yAxis: { type: 'value', name: '活跃用户数' },
    series: [{
      data: [120, 145, 168, 185, 195, 210, 225, 240, 235, 250, 260],
      type: 'line',
      smooth: true,
      areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
      itemStyle: { color: '#3b82f6' }
    }]
  };

  // 服务质量评分
  const serviceQualityOption = {
    title: { text: '各社区服务质量评分', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ['仁义', '百步亭', '后湖', '塔子湖', '永清', '四唯', '劳动', '车站', '大智', '一元'],
      axisLabel: { rotate: 45 }
    },
    yAxis: { type: 'value', name: '评分', max: 5 },
    series: [{
      data: [4.8, 4.7, 4.5, 4.6, 4.3, 4.5, 4.2, 4.4, 4.3, 4.4],
      type: 'bar',
      itemStyle: {
        color: new (window as any).echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#10b981' },
          { offset: 1, color: '#059669' }
        ])
      }
    }]
  };

  // 紧急事件处理统计
  const emergencyEventsOption = {
    title: { text: '紧急事件处理统计', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['总事件数', '已处理'], bottom: 0 },
    xAxis: {
      type: 'category',
      data: ['7月', '8月', '9月', '10月', '11月']
    },
    yAxis: { type: 'value', name: '事件数' },
    series: [
      {
        name: '总事件数',
        data: [25, 28, 22, 26, 24],
        type: 'bar',
        itemStyle: { color: '#f59e0b' }
      },
      {
        name: '已处理',
        data: [24, 27, 21, 25, 23],
        type: 'bar',
        itemStyle: { color: '#10b981' }
      }
    ]
  };

  // 平台使用率分布
  const utilizationOption = {
    title: { text: '平台功能使用率分布', left: 'center' },
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: 35, name: '安全监护', itemStyle: { color: '#3b82f6' } },
        { value: 25, name: '陪诊管理', itemStyle: { color: '#10b981' } },
        { value: 20, name: '健康管理', itemStyle: { color: '#f59e0b' } },
        { value: 15, name: '情感陪伴', itemStyle: { color: '#8b5cf6' } },
        { value: 5, name: '其他服务', itemStyle: { color: '#6b7280' } }
      ],
      label: {
        formatter: '{b}: {c}%'
      }
    }]
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-2xl text-white">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-full px-6 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <Link to="/" className="text-blue-400 hover:text-blue-300 mr-4">
              <ArrowLeft className="w-6 h-6" />
            </Link>
            <h1 className="text-2xl font-bold">江岸区智慧养老数据大屏</h1>
          </div>
          <div className="text-gray-400 text-sm">
            更新时间: {new Date().toLocaleString('zh-CN')}
          </div>
        </div>
      </header>

      <main className="max-w-full px-6 py-6">
        {/* 核心指标卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-sm mb-1">服务老人总数</p>
                <p className="text-4xl font-bold">7,958</p>
              </div>
              <Users className="w-14 h-14 text-blue-300 opacity-50" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-200 text-sm mb-1">社区覆盖</p>
                <p className="text-4xl font-bold">{stats.totalCommunities}</p>
              </div>
              <Activity className="w-14 h-14 text-green-300 opacity-50" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm mb-1">服务商数量</p>
                <p className="text-4xl font-bold">{stats.totalProviders}</p>
              </div>
              <TrendingUp className="w-14 h-14 text-purple-300 opacity-50" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-600 to-orange-700 rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-200 text-sm mb-1">平台使用率</p>
                <p className="text-4xl font-bold">{stats.platformUtilization}%</p>
              </div>
              <AlertCircle className="w-14 h-14 text-orange-300 opacity-50" />
            </div>
          </div>
        </div>

        {/* 图表区域 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-800 rounded-xl shadow-lg p-6">
            <ReactECharts option={userActivityOption} style={{ height: '350px' }} />
          </div>

          <div className="bg-gray-800 rounded-xl shadow-lg p-6">
            <ReactECharts option={serviceQualityOption} style={{ height: '350px' }} />
          </div>

          <div className="bg-gray-800 rounded-xl shadow-lg p-6">
            <ReactECharts option={emergencyEventsOption} style={{ height: '350px' }} />
          </div>

          <div className="bg-gray-800 rounded-xl shadow-lg p-6">
            <ReactECharts option={utilizationOption} style={{ height: '350px' }} />
          </div>
        </div>
      </main>
    </div>
  );
}
