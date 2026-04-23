import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { ArrowLeft, Users, AlertTriangle, FileText, TrendingUp, Download } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

export default function GovernmentDashboard() {
  const [stats, setStats] = useState({
    totalElders: 0,
    activeUsers: 0,
    emergencyEvents: 0,
    platformUtilization: 85.5
  });
  const [alerts, setAlerts] = useState<any[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // 调用政府数据聚合函数
      const { data: aggregatedData } = await supabase.functions.invoke('government-data-aggregator', {
        body: { time_period: 'current' }
      });

      if (aggregatedData?.data) {
        setStats({
          totalElders: aggregatedData.data.total_elderly || 0,
          activeUsers: aggregatedData.data.active_users || 0,
          emergencyEvents: aggregatedData.data.emergency_events || 0,
          platformUtilization: aggregatedData.data.platform_utilization_rate || 85.5
        });
      }

      // 加载监管预警
      const { data: alertsData } = await supabase
        .from('regulatory_alerts')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10);

      setAlerts(alertsData || []);

      // 加载政策文件
      const { data: policiesData } = await supabase
        .from('policy_documents')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(8);

      setPolicies(policiesData || []);

    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    try {
      const { data } = await supabase.functions.invoke('regulatory-report-generator', {
        body: {
          report_type: 'monthly',
          reporting_period: new Date().toISOString().slice(0, 7)
        }
      });

      if (data?.data) {
        alert('报告生成成功！报告ID: ' + data.data.report_id);
      }
    } catch (error) {
      console.error('生成报告失败:', error);
      alert('生成报告失败');
    }
  };

  const trendChartOption = {
    title: { text: '平台使用率趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月']
    },
    yAxis: { type: 'value', name: '使用率(%)' },
    series: [{
      data: [75, 78, 80, 82, 83, 84, 85, 86, 85.5, 86.2, 85.5],
      type: 'line',
      smooth: true,
      itemStyle: { color: '#3b82f6' }
    }]
  };

  const severityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-2xl text-gray-600">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link to="/" className="text-blue-600 hover:text-blue-700">
              <ArrowLeft className="w-6 h-6" />
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">政府监管端</h1>
          </div>
          <button
            onClick={generateReport}
            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download className="w-5 h-5" />
            <span>生成监管报告</span>
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* 数据总览 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">老人总数</p>
                <p className="text-3xl font-bold text-blue-600">{stats.totalElders}</p>
              </div>
              <Users className="w-12 h-12 text-blue-300" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">活跃用户</p>
                <p className="text-3xl font-bold text-green-600">{stats.activeUsers}</p>
              </div>
              <TrendingUp className="w-12 h-12 text-green-300" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">紧急事件</p>
                <p className="text-3xl font-bold text-orange-600">{stats.emergencyEvents}</p>
              </div>
              <AlertTriangle className="w-12 h-12 text-orange-300" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">平台使用率</p>
                <p className="text-3xl font-bold text-purple-600">{stats.platformUtilization}%</p>
              </div>
              <FileText className="w-12 h-12 text-purple-300" />
            </div>
          </div>
        </div>

        {/* 趋势图表 */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <ReactECharts option={trendChartOption} style={{ height: '400px' }} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 监管预警 */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <AlertTriangle className="w-6 h-6 mr-2 text-orange-600" />
              监管预警
            </h2>
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div key={alert.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${severityColor(alert.severity)}`}>
                      {alert.severity === 'high' ? '高' : alert.severity === 'medium' ? '中' : '低'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{alert.description}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    {new Date(alert.created_at).toLocaleDateString('zh-CN')}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* 政策文件 */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <FileText className="w-6 h-6 mr-2 text-blue-600" />
              政策文件
            </h2>
            <div className="space-y-3">
              {policies.map((policy) => (
                <div key={policy.id} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-1">{policy.title}</h3>
                  <p className="text-sm text-gray-600 mb-2">{policy.content?.substring(0, 80)}...</p>
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>生效日期: {policy.effective_date}</span>
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">{policy.category}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
