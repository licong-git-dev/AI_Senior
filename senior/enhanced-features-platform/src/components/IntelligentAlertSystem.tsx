import React, { useState, useEffect } from 'react';
import { AlertTriangle, Heart, Activity, Shield, Clock, TrendingUp, Bell, CheckCircle, XCircle, Pause } from 'lucide-react';

const IntelligentAlertSystem = () => {
  const [activeTab, setActiveTab] = useState('health');
  const [alerts, setAlerts] = useState({
    health: [
      {
        id: 1,
        type: 'health',
        severity: 'high',
        title: '血压异常预警',
        description: '连续3天血压值偏高，建议立即就医检查',
        user: '王大爷',
        timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30分钟前
        status: 'active',
        details: {
          metric: '血压',
          current: '145/92 mmHg',
          threshold: '140/90 mmHg',
          trend: 'up',
          duration: '3天'
        },
        actions: ['立即通知家属', '建议就医', '记录观察']
      },
      {
        id: 2,
        type: 'health',
        severity: 'medium',
        title: '心率监测提醒',
        description: '静息心率较平时略快，建议注意休息',
        user: '李奶奶',
        timestamp: new Date(Date.now() - 1000 * 60 * 120), // 2小时前
        status: 'acknowledged',
        details: {
          metric: '心率',
          current: '85 bpm',
          threshold: '75 bpm',
          trend: 'up',
          duration: '1天'
        },
        actions: ['注意休息', '监测心率', '咨询医生']
      }
    ],
    behavior: [
      {
        id: 3,
        type: 'behavior',
        severity: 'high',
        title: '异常活动模式',
        description: '检测到用户活动量显著减少，可能存在健康风险',
        user: '张爷爷',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2小时前
        status: 'active',
        details: {
          metric: '活动量',
          current: '1,200步',
          threshold: '5,000步',
          trend: 'down',
          duration: '2天'
        },
        actions: ['联系用户', '健康评估', '调整计划']
      },
      {
        id: 4,
        type: 'behavior',
        severity: 'medium',
        title: '睡眠质量下降',
        description: '连续2晚睡眠时间少于6小时，建议关注',
        user: '陈奶奶',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4), // 4小时前
        status: 'resolved',
        details: {
          metric: '睡眠时间',
          current: '5.5小时',
          threshold: '7小时',
          trend: 'down',
          duration: '2天'
        },
        actions: ['改善睡眠', '环境调整', '医疗咨询']
      }
    ],
    emergency: [
      {
        id: 5,
        type: 'emergency',
        severity: 'critical',
        title: '紧急呼叫触发',
        description: '用户按下紧急按钮，正在呼叫急救中心',
        user: '刘大爷',
        timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5分钟前
        status: 'active',
        details: {
          location: '客厅',
          responders: ['120急救', '家属', '社区服务'],
          estimated_arrival: '8分钟'
        },
        actions: ['联系120', '通知家属', '准备接待']
      }
    ]
  });

  const [systemStatus, setSystemStatus] = useState({
    total_alerts: 5,
    active_alerts: 2,
    resolved_today: 8,
    accuracy_rate: 96.8,
    response_time: '2.3分钟'
  });

  const tabs = [
    { id: 'health', name: '健康预警', icon: Heart },
    { id: 'behavior', name: '行为检测', icon: Activity },
    { id: 'emergency', name: '紧急告警', icon: AlertTriangle }
  ];

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSeverityText = (severity) => {
    switch (severity) {
      case 'critical': return '紧急';
      case 'high': return '高';
      case 'medium': return '中';
      case 'low': return '低';
      default: return '普通';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <Bell className="h-4 w-4 text-red-600" />;
      case 'acknowledged': return <Pause className="h-4 w-4 text-yellow-600" />;
      case 'resolved': return <CheckCircle className="h-4 w-4 text-green-600" />;
      default: return <XCircle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'active': return '处理中';
      case 'acknowledged': return '已确认';
      case 'resolved': return '已解决';
      default: return '未知';
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-red-600" />;
      case 'down': return <TrendingUp className="h-4 w-4 text-red-600 transform rotate-180" />;
      default: return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  const formatTime = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    
    if (minutes < 60) {
      return `${minutes}分钟前`;
    } else if (hours < 24) {
      return `${hours}小时前`;
    } else {
      return timestamp.toLocaleDateString();
    }
  };

  const handleAlertAction = (alertId, action) => {
    // 模拟处理告警
    setAlerts(prev => {
      const updated = { ...prev };
      Object.keys(updated).forEach(key => {
        updated[key] = updated[key].map(alert => 
          alert.id === alertId ? { ...alert, status: 'acknowledged' } : alert
        );
      });
      return updated;
    });
    
    console.log(`处理告警 ${alertId}: ${action}`);
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <AlertTriangle className="h-8 w-8 mr-3 text-red-600" />
            智能预警系统
          </h1>
          <p className="text-gray-600 mt-2">
            基于AI的健康风险预测、异常行为检测和预防性告警系统
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            systemStatus.active_alerts > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
          }`}>
            {systemStatus.active_alerts > 0 ? `有${systemStatus.active_alerts}个活动告警` : '系统正常'}
          </div>
        </div>
      </div>

      {/* 系统状态统计 */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">总告警数</p>
              <p className="text-2xl font-semibold text-gray-900">{systemStatus.total_alerts}</p>
            </div>
            <AlertTriangle className="h-8 w-8 text-orange-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">活动告警</p>
              <p className="text-2xl font-semibold text-red-600">{systemStatus.active_alerts}</p>
            </div>
            <Bell className="h-8 w-8 text-red-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">今日已解决</p>
              <p className="text-2xl font-semibold text-green-600">{systemStatus.resolved_today}</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">预测准确率</p>
              <p className="text-2xl font-semibold text-blue-600">{systemStatus.accuracy_rate}%</p>
            </div>
            <Shield className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">平均响应时间</p>
              <p className="text-2xl font-semibold text-purple-600">{systemStatus.response_time}</p>
            </div>
            <Clock className="h-8 w-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* 告警分类标签 */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                  activeTab === tab.id
                    ? 'border-red-500 text-red-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="h-4 w-4 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* 告警列表 */}
        <div className="p-6">
          <div className="space-y-4">
            {alerts[activeTab]?.map((alert) => (
              <div
                key={alert.id}
                className={`border rounded-lg p-6 ${getSeverityColor(alert.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 mt-1">
                      {getStatusIcon(alert.status)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {alert.title}
                        </h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          getSeverityColor(alert.severity)
                        }`}>
                          {getSeverityText(alert.severity)}风险
                        </span>
                        <span className="text-xs text-gray-500">
                          {getStatusText(alert.status)}
                        </span>
                      </div>
                      <p className="text-gray-700 mb-3">
                        {alert.description}
                      </p>
                      
                      {/* 详细信息 */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        {alert.details.metric && (
                          <div>
                            <p className="text-xs text-gray-500">当前值</p>
                            <div className="flex items-center space-x-2">
                              <span className="font-medium">{alert.details.current}</span>
                              {getTrendIcon(alert.details.trend)}
                            </div>
                          </div>
                        )}
                        {alert.details.threshold && (
                          <div>
                            <p className="text-xs text-gray-500">阈值</p>
                            <p className="font-medium">{alert.details.threshold}</p>
                          </div>
                        )}
                        {alert.details.duration && (
                          <div>
                            <p className="text-xs text-gray-500">持续时间</p>
                            <p className="font-medium">{alert.details.duration}</p>
                          </div>
                        )}
                        {alert.details.responders && (
                          <div>
                            <p className="text-xs text-gray-500">响应人员</p>
                            <p className="font-medium">{alert.details.responders.length}人</p>
                          </div>
                        )}
                      </div>

                      {/* 建议操作 */}
                      <div className="flex flex-wrap gap-2">
                        {alert.actions.map((action, index) => (
                          <button
                            key={index}
                            onClick={() => handleAlertAction(alert.id, action)}
                            className="px-3 py-1 bg-white border border-gray-300 rounded-full text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                          >
                            {action}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-sm text-gray-500">
                    {formatTime(alert.timestamp)}
                    <br />
                    <span className="text-xs">用户: {alert.user}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 预测模型说明 */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">AI预测模型</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700">
          <div>
            <h4 className="font-medium mb-2">健康风险预测</h4>
            <p>基于生理指标趋势分析，预测潜在健康风险</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">行为模式识别</h4>
            <p>学习用户日常行为模式，识别异常变化</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">紧急事件检测</h4>
            <p>实时监控异常情况，及时触发紧急响应</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntelligentAlertSystem;