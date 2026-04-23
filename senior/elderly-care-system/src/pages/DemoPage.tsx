import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as echarts from 'echarts';
import ReactECharts from 'echarts-for-react';
import { 
  mockElderly, 
  mockHealthData, 
  mockDevices, 
  mockEmergencyCalls, 
  mockStats,
  MockHealthData 
} from '../data/mockData';
import { 
  Activity, 
  Users, 
  Heart, 
  AlertTriangle, 
  Smartphone,
  TrendingUp,
  MapPin,
  Phone,
  RefreshCw,
  Play,
  Pause
} from 'lucide-react';

export default function DemoPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'family' | 'care' | 'elderly'>('overview');
  const [selectedElder, setSelectedElder] = useState(mockElderly[0]);
  const [demoMode, setDemoMode] = useState<'running' | 'paused'>('paused');
  const [demoStep, setDemoStep] = useState(0);
  const [simulatedEvents, setSimulatedEvents] = useState<Array<{id: string, type: string, message: string, time: Date}>>([]);
  const [realtimeData, setRealtimeData] = useState({
    heartRate: 72,
    bloodPressure: { systolic: 120, diastolic: 80 },
    steps: 3580,
    temperature: 36.5
  });

  // 演示场景步骤
  const demoScenarios = [
    { title: '场景1：日常健康监测', description: '展示老人日常健康数据监控' },
    { title: '场景2：异常数据预警', description: '模拟血压异常触发预警' },
    { title: '场景3：跌倒检测', description: '模拟跌倒检测和紧急响应' },
    { title: '场景4：数据分析', description: '展示健康趋势和风险评估' }
  ];

  // 获取选中老人的健康数据
  const elderHealthData = mockHealthData.filter(h => h.userId === selectedElder.id);
  
  // 血压趋势数据（最近7天）
  const bloodPressureData = elderHealthData
    .filter(h => h.dataType === 'blood_pressure')
    .slice(0, 7)
    .reverse();

  const bloodPressureOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['收缩压', '舒张压'],
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: bloodPressureData.map(d => 
        new Date(d.measurementTime).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
      )
    },
    yAxis: {
      type: 'value',
      name: '血压 (mmHg)',
      min: 60,
      max: 160
    },
    series: [
      {
        name: '收缩压',
        type: 'line',
        data: bloodPressureData.map(d => d.systolicPressure),
        smooth: true,
        itemStyle: { color: '#ef4444' },
        areaStyle: { opacity: 0.1 }
      },
      {
        name: '舒张压',
        type: 'line',
        data: bloodPressureData.map(d => d.diastolicPressure),
        smooth: true,
        itemStyle: { color: '#3b82f6' },
        areaStyle: { opacity: 0.1 }
      }
    ]
  };

  // 心率趋势数据
  const heartRateData = elderHealthData
    .filter(h => h.dataType === 'heart_rate' && h.heartRate)
    .slice(0, 7)
    .reverse();

  const heartRateOption = {
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: heartRateData.map(d => 
        new Date(d.measurementTime).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
      )
    },
    yAxis: {
      type: 'value',
      name: '心率 (bpm)',
      min: 50,
      max: 100
    },
    series: [{
      name: '心率',
      type: 'line',
      data: heartRateData.map(d => d.heartRate),
      smooth: true,
      itemStyle: { color: '#10b981' },
      areaStyle: { opacity: 0.2 }
    }]
  };

  // 启动/暂停演示
  const toggleDemo = () => {
    if (demoMode === 'paused') {
      setDemoMode('running');
      setDemoStep(0);
    } else {
      setDemoMode('paused');
    }
  };

  // 演示步骤自动推进
  useEffect(() => {
    if (demoMode === 'running') {
      const timer = setTimeout(() => {
        if (demoStep < demoScenarios.length - 1) {
          setDemoStep(demoStep + 1);
        } else {
          setDemoMode('paused');
          setDemoStep(0);
        }
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [demoMode, demoStep]);

  // 实时数据更新模拟
  useEffect(() => {
    const interval = setInterval(() => {
      setRealtimeData(prev => ({
        heartRate: prev.heartRate + Math.floor(Math.random() * 6 - 3), // ±3 bpm
        bloodPressure: {
          systolic: Math.max(110, Math.min(140, prev.bloodPressure.systolic + Math.floor(Math.random() * 4 - 2))),
          diastolic: Math.max(70, Math.min(90, prev.bloodPressure.diastolic + Math.floor(Math.random() * 4 - 2)))
        },
        steps: prev.steps + Math.floor(Math.random() * 20),
        temperature: Number((prev.temperature + (Math.random() * 0.2 - 0.1)).toFixed(1))
      }));
    }, 3000); // 每3秒更新一次

    return () => clearInterval(interval);
  }, []);

  // 模拟跌倒事件
  const simulateFallDetection = () => {
    const event = {
      id: Date.now().toString(),
      type: 'fall',
      message: '⚠️ 跌倒检测报警！系统检测到异常加速度变化，已自动通知紧急联系人',
      time: new Date()
    };
    setSimulatedEvents(prev => [event, ...prev]);
    // 切换到护理管理端展示紧急呼叫
    setTimeout(() => {
      setActiveTab('care');
    }, 2000);
  };

  // 模拟紧急呼叫
  const simulateEmergencyCall = () => {
    const event = {
      id: Date.now().toString(),
      type: 'emergency',
      message: '🚨 紧急呼叫已发送！正在联系家属和护理人员...',
      time: new Date()
    };
    setSimulatedEvents(prev => [event, ...prev]);
  };

  // 模拟健康数据上传
  const simulateHealthDataUpload = () => {
    const event = {
      id: Date.now().toString(),
      type: 'data',
      message: `✅ 健康数据上传成功！心率: ${realtimeData.heartRate} bpm, 血压: ${realtimeData.bloodPressure.systolic}/${realtimeData.bloodPressure.diastolic} mmHg`,
      time: new Date()
    };
    setSimulatedEvents(prev => [event, ...prev]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* 顶部导航栏 */}
      <nav className="bg-white shadow-md border-b-2 border-indigo-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Activity className="h-8 w-8 text-indigo-600" />
                <h1 className="text-2xl font-bold text-gray-900">
                  养老智能体安全监护系统
                  <span className="ml-2 text-sm font-normal text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
                    演示版本
                  </span>
                </h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
              >
                返回首页
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* 演示控制面板 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl shadow-xl p-6 text-white mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2">演示控制面板</h2>
              <p className="text-indigo-100">
                {demoMode === 'running' 
                  ? `正在演示：${demoScenarios[demoStep].title} - ${demoScenarios[demoStep].description}`
                  : '点击开始按钮体验自动演示，或手动切换标签页浏览不同功能'}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleDemo}
                className="flex items-center space-x-2 px-6 py-3 bg-white text-indigo-600 rounded-lg font-semibold hover:bg-indigo-50 transition-colors shadow-lg"
              >
                {demoMode === 'running' ? (
                  <>
                    <Pause className="h-5 w-5" />
                    <span>暂停演示</span>
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5" />
                    <span>开始演示</span>
                  </>
                )}
              </button>
              <button
                onClick={() => window.location.reload()}
                className="flex items-center space-x-2 px-4 py-3 bg-white bg-opacity-20 rounded-lg font-medium hover:bg-opacity-30 transition-colors"
              >
                <RefreshCw className="h-5 w-5" />
                <span>重置</span>
              </button>
            </div>
          </div>
        </div>

        {/* 标签页导航 */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {[
                { id: 'overview', name: '系统概览', icon: Activity },
                { id: 'elderly', name: '老人端', icon: Smartphone },
                { id: 'family', name: '家属监控端', icon: Heart },
                { id: 'care', name: '护理管理端', icon: Users }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <tab.icon className="h-5 w-5" />
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* 系统概览标签 */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* 统计卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-indigo-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">在管老人总数</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{mockStats.totalElderly}</p>
                  </div>
                  <Users className="h-12 w-12 text-indigo-500 opacity-80" />
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">在线设备</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">
                      {mockStats.onlineDevices}/{mockStats.totalDevices}
                    </p>
                  </div>
                  <Smartphone className="h-12 w-12 text-green-500 opacity-80" />
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">健康记录</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{mockStats.totalHealthRecords}</p>
                  </div>
                  <Activity className="h-12 w-12 text-blue-500 opacity-80" />
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-red-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">异常事件</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{mockStats.abnormalRecords}</p>
                  </div>
                  <AlertTriangle className="h-12 w-12 text-red-500 opacity-80" />
                </div>
              </div>
            </div>

            {/* 风险分布 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">健康风险分布</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-red-50 rounded-lg border-2 border-red-200">
                  <p className="text-3xl font-bold text-red-600">{mockStats.highRiskElderly}</p>
                  <p className="text-sm text-gray-600 mt-2">高风险老人</p>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg border-2 border-yellow-200">
                  <p className="text-3xl font-bold text-yellow-600">{mockStats.mediumRiskElderly}</p>
                  <p className="text-sm text-gray-600 mt-2">中风险老人</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg border-2 border-green-200">
                  <p className="text-3xl font-bold text-green-600">{mockStats.lowRiskElderly}</p>
                  <p className="text-sm text-gray-600 mt-2">低风险老人</p>
                </div>
              </div>
            </div>

            {/* 社区分布 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">社区分布</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Array.from(new Set(mockElderly.map(e => e.community))).map(community => {
                  const count = mockElderly.filter(e => e.community === community).length;
                  return (
                    <div key={community} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <MapPin className="h-5 w-5 text-indigo-600" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{community}</p>
                        <p className="text-xs text-gray-600">{count}人</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* 老人端标签 */}
        {activeTab === 'elderly' && (
          <div className="space-y-6">
            {/* 实时健康监测 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Activity className="h-5 w-5 mr-2 text-green-500 animate-pulse" />
                实时健康监测
                <span className="ml-2 text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">实时更新中</span>
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-red-50 to-pink-50 rounded-lg p-4 border-2 border-red-200">
                  <div className="flex items-center justify-between mb-2">
                    <Heart className="h-6 w-6 text-red-500" />
                    <span className="text-xs text-gray-600">心率</span>
                  </div>
                  <p className="text-3xl font-bold text-gray-900">{realtimeData.heartRate}</p>
                  <p className="text-xs text-gray-600 mt-1">bpm</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border-2 border-blue-200">
                  <div className="flex items-center justify-between mb-2">
                    <Activity className="h-6 w-6 text-blue-500" />
                    <span className="text-xs text-gray-600">血压</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-900">
                    {realtimeData.bloodPressure.systolic}/{realtimeData.bloodPressure.diastolic}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">mmHg</p>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border-2 border-green-200">
                  <div className="flex items-center justify-between mb-2">
                    <TrendingUp className="h-6 w-6 text-green-500" />
                    <span className="text-xs text-gray-600">步数</span>
                  </div>
                  <p className="text-3xl font-bold text-gray-900">{realtimeData.steps}</p>
                  <p className="text-xs text-gray-600 mt-1">步</p>
                </div>
                <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-lg p-4 border-2 border-yellow-200">
                  <div className="flex items-center justify-between mb-2">
                    <Activity className="h-6 w-6 text-yellow-500" />
                    <span className="text-xs text-gray-600">体温</span>
                  </div>
                  <p className="text-3xl font-bold text-gray-900">{realtimeData.temperature}</p>
                  <p className="text-xs text-gray-600 mt-1">℃</p>
                </div>
              </div>
            </div>

            {/* 功能按钮区 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">一键操作</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={simulateFallDetection}
                  className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-red-500 to-red-600 text-white rounded-xl hover:from-red-600 hover:to-red-700 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  <AlertTriangle className="h-12 w-12 mb-3" />
                  <span className="text-lg font-semibold">模拟跌倒检测</span>
                  <span className="text-xs mt-1 opacity-90">测试自动报警功能</span>
                </button>
                
                <button
                  onClick={simulateEmergencyCall}
                  className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-orange-500 to-orange-600 text-white rounded-xl hover:from-orange-600 hover:to-orange-700 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  <Phone className="h-12 w-12 mb-3" />
                  <span className="text-lg font-semibold">紧急呼叫</span>
                  <span className="text-xs mt-1 opacity-90">一键联系家属/护理</span>
                </button>
                
                <button
                  onClick={simulateHealthDataUpload}
                  className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-green-500 to-green-600 text-white rounded-xl hover:from-green-600 hover:to-green-700 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  <Activity className="h-12 w-12 mb-3" />
                  <span className="text-lg font-semibold">上传健康数据</span>
                  <span className="text-xs mt-1 opacity-90">同步最新监测数据</span>
                </button>
              </div>
            </div>

            {/* 事件日志 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">操作记录</h3>
              {simulatedEvents.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>暂无操作记录</p>
                  <p className="text-sm mt-2">点击上方按钮开始演示功能</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {simulatedEvents.map(event => (
                    <div 
                      key={event.id} 
                      className={`p-4 rounded-lg border-l-4 ${
                        event.type === 'fall' ? 'bg-red-50 border-red-500' :
                        event.type === 'emergency' ? 'bg-orange-50 border-orange-500' :
                        'bg-green-50 border-green-500'
                      }`}
                    >
                      <p className="text-sm font-medium text-gray-900">{event.message}</p>
                      <p className="text-xs text-gray-600 mt-1">
                        {event.time.toLocaleTimeString('zh-CN')}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 使用提示 */}
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 border-2 border-indigo-200">
              <h4 className="text-base font-semibold text-gray-900 mb-2">💡 使用说明</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• 实时健康监测数据每3秒自动更新，模拟真实设备采集</li>
                <li>• 点击"模拟跌倒检测"按钮会触发自动报警，并跳转到护理管理端查看</li>
                <li>• "紧急呼叫"按钮模拟老人主动求助场景</li>
                <li>• "上传健康数据"按钮模拟设备数据同步到云端</li>
              </ul>
            </div>
          </div>
        )}

        {/* 家属监控端标签 */}
        {activeTab === 'family' && (
          <div className="space-y-6">
            {/* 老人选择器 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">选择老人</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {mockElderly.slice(0, 10).map(elder => (
                  <button
                    key={elder.id}
                    onClick={() => setSelectedElder(elder)}
                    className={`p-3 rounded-lg text-left transition-colors ${
                      selectedElder.id === elder.id
                        ? 'bg-indigo-100 border-2 border-indigo-500'
                        : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                    }`}
                  >
                    <p className="font-medium text-gray-900">{elder.name}</p>
                    <p className="text-xs text-gray-600">{elder.age}岁</p>
                  </button>
                ))}
              </div>
            </div>

            {/* 老人基本信息 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-600">姓名</p>
                  <p className="text-base font-medium text-gray-900">{selectedElder.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">年龄/性别</p>
                  <p className="text-base font-medium text-gray-900">{selectedElder.age}岁 / {selectedElder.gender}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">所属社区</p>
                  <p className="text-base font-medium text-gray-900">{selectedElder.community}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">风险等级</p>
                  <p className={`text-base font-medium ${
                    selectedElder.riskLevel === 3 ? 'text-red-600' :
                    selectedElder.riskLevel === 2 ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    {selectedElder.riskLevel === 3 ? '高风险' :
                     selectedElder.riskLevel === 2 ? '中风险' : '低风险'}
                  </p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-gray-600">慢性病史</p>
                  <p className="text-base font-medium text-gray-900">{selectedElder.chronicDiseases.join('、')}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-gray-600">紧急联系人</p>
                  <p className="text-base font-medium text-gray-900">{selectedElder.emergencyContact} / {selectedElder.emergencyPhone}</p>
                </div>
              </div>
            </div>

            {/* 健康趋势图表 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">血压趋势（最近7天）</h3>
                {/* @ts-ignore */}
                <ReactECharts option={bloodPressureOption} echarts={echarts} style={{ height: '300px' }} />
              </div>
              <div className="bg-white rounded-xl shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">心率趋势（最近7天）</h3>
                {/* @ts-ignore */}
                <ReactECharts option={heartRateOption} echarts={echarts} style={{ height: '300px' }} />
              </div>
            </div>

            {/* 最新健康记录 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">最新健康记录</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">数值</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {elderHealthData.slice(0, 10).map(record => (
                      <tr key={record.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(record.measurementTime).toLocaleString('zh-CN')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {record.dataType === 'blood_pressure' ? '血压' :
                           record.dataType === 'heart_rate' ? '心率' :
                           record.dataType === 'blood_sugar' ? '血糖' : record.dataType}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {record.dataType === 'blood_pressure' && 
                            `${record.systolicPressure}/${record.diastolicPressure} mmHg`}
                          {record.dataType === 'heart_rate' && `${record.heartRate} bpm`}
                          {record.dataType === 'blood_sugar' && `${record.bloodSugar} mmol/L`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            record.abnormalFlag === 1 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {record.abnormalFlag === 1 ? '异常' : '正常'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 护理管理端标签 */}
        {activeTab === 'care' && (
          <div className="space-y-6">
            {/* 紧急呼叫列表 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">紧急呼叫记录</h3>
              <div className="space-y-4">
                {mockEmergencyCalls.slice(0, 10).map(call => (
                  <div key={call.id} className="border-l-4 border-red-500 bg-red-50 p-4 rounded-r-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <p className="text-lg font-semibold text-gray-900">{call.userName}</p>
                          <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                            call.priorityLevel === 3 ? 'bg-red-200 text-red-800' :
                            call.priorityLevel === 2 ? 'bg-yellow-200 text-yellow-800' :
                            'bg-green-200 text-green-800'
                          }`}>
                            {call.priorityLevel === 3 ? '紧急' :
                             call.priorityLevel === 2 ? '重要' : '一般'}
                          </span>
                          <span className="px-3 py-1 text-xs font-medium rounded-full bg-gray-200 text-gray-800">
                            {call.callType === 'manual' ? '手动呼叫' :
                             call.callType === 'auto_fall' ? '跌倒检测' : '健康预警'}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-1">
                          <MapPin className="inline h-4 w-4 mr-1" />
                          {call.location}
                        </p>
                        <p className="text-sm text-gray-600 mb-1">
                          呼叫时间：{new Date(call.callTime).toLocaleString('zh-CN')}
                        </p>
                        {call.responseTime && (
                          <p className="text-sm text-gray-600 mb-1">
                            响应时间：{new Date(call.responseTime).toLocaleString('zh-CN')}
                          </p>
                        )}
                        <p className="text-sm text-gray-700 mt-2">{call.notes}</p>
                      </div>
                      <div className="ml-4">
                        <span className="px-4 py-2 bg-green-100 text-green-800 text-sm font-medium rounded-lg">
                          已完成
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 高风险老人列表 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">高风险老人重点关注</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mockElderly.filter(e => e.riskLevel === 3).map(elder => (
                  <div key={elder.id} className="border-2 border-red-200 bg-red-50 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-lg font-semibold text-gray-900">{elder.name}</h4>
                      <span className="px-2 py-1 bg-red-200 text-red-800 text-xs font-medium rounded-full">
                        高风险
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">{elder.age}岁 / {elder.gender}</p>
                    <p className="text-sm text-gray-600 mb-1">{elder.community}</p>
                    <p className="text-sm text-gray-700">慢性病：{elder.chronicDiseases.join('、')}</p>
                    <div className="mt-3 flex items-center space-x-2">
                      <button className="flex-1 px-3 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700">
                        查看详情
                      </button>
                      <button className="px-3 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700">
                        <Phone className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
