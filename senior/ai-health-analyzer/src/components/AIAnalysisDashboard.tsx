import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import EChartsReact from 'echarts-for-react';
import { Activity, Brain, TrendingUp, AlertTriangle, Heart, Zap } from 'lucide-react';

interface AnalysisData {
  physiological?: any;
  behavioral?: any;
  predictions?: any;
  realtime?: any;
  anomalies?: any;
}

export default function AIAnalysisDashboard() {
  const [userId, setUserId] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisData, setAnalysisData] = useState<AnalysisData>({});
  const [activeTab, setActiveTab] = useState('overview');

  // 执行多模态数据融合
  const handleMultimodalFusion = async () => {
    if (!userId) {
      alert('请输入用户ID');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('multimodal-data-fusion', {
        body: {
          user_id: userId,
          data_sources: [
            { type: 'wristband' },
            { type: 'mattress' },
            { type: 'camera' },
            { type: 'environment' }
          ],
          time_range: {
            start: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            end: new Date().toISOString()
          }
        }
      });

      if (error) throw error;
      alert('多模态数据融合完成');
      console.log('融合结果:', data);
    } catch (error: any) {
      alert('融合失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 执行生理数据分析
  const handlePhysiologicalAnalysis = async () => {
    if (!userId) {
      alert('请输入用户ID');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('physiological-analyzer', {
        body: {
          user_id: userId,
          analysis_type: 'comprehensive',
          time_range: {
            start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            end: new Date().toISOString()
          }
        }
      });

      if (error) throw error;
      setAnalysisData(prev => ({ ...prev, physiological: data.data }));
      alert('生理数据分析完成');
    } catch (error: any) {
      alert('分析失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 执行行为模式识别
  const handleBehaviorRecognition = async () => {
    if (!userId) {
      alert('请输入用户ID');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('behavior-recognizer', {
        body: {
          user_id: userId,
          analysis_period: 'week'
        }
      });

      if (error) throw error;
      setAnalysisData(prev => ({ ...prev, behavioral: data.data }));
      alert('行为模式识别完成');
    } catch (error: any) {
      alert('识别失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 执行健康预测
  const handleHealthPrediction = async (horizon: '7days' | '30days') => {
    if (!userId) {
      alert('请输入用户ID');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('health-predictor', {
        body: {
          user_id: userId,
          prediction_horizon: horizon,
          prediction_types: ['heart_rate', 'blood_pressure', 'sleep_quality', 'activity_level']
        }
      });

      if (error) throw error;
      setAnalysisData(prev => ({ ...prev, predictions: data.data }));
      alert(`${horizon === '7days' ? '7天' : '30天'}健康预测完成`);
    } catch (error: any) {
      alert('预测失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 执行实时分析
  const handleRealtimeAnalysis = async () => {
    if (!userId) {
      alert('请输入用户ID');
      return;
    }

    setLoading(true);
    try {
      // 模拟实时数据
      const realtimeData = {
        heart_rate: 72,
        blood_pressure: { systolic: 120, diastolic: 80 },
        spo2: 98,
        temperature: 36.5,
        activity: { type: 'walking', intensity: 0.6, steps: 150 }
      };

      const { data, error } = await supabase.functions.invoke('real-time-ai-engine', {
        body: {
          user_id: userId,
          real_time_data: realtimeData,
          analysis_type: 'all'
        }
      });

      if (error) throw error;
      setAnalysisData(prev => ({ ...prev, realtime: data.data }));
      alert(`实时分析完成 (延迟: ${data.data.processing_time_ms}ms)`);
    } catch (error: any) {
      alert('实时分析失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 执行异常检测
  const handleAnomalyDetection = async () => {
    if (!userId) {
      alert('请输入用户ID');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('anomaly-detector', {
        body: {
          user_id: userId,
          detection_scope: 'comprehensive',
          time_window: 24
        }
      });

      if (error) throw error;
      setAnalysisData(prev => ({ ...prev, anomalies: data.data }));
      alert(`异常检测完成，检测到${data.data.detection_summary.total_anomalies}项异常`);
    } catch (error: any) {
      alert('检测失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 心率变异图表配置
  const getHRVChartOption = () => {
    if (!analysisData.physiological?.heart_rate_variability?.status) return null;
    const hrv = analysisData.physiological.heart_rate_variability;
    
    return {
      title: { text: '心率变异性分析', left: 'center' },
      tooltip: { trigger: 'item' },
      series: [{
        type: 'gauge',
        detail: { formatter: '{value}分' },
        data: [{ value: hrv.hrv_score, name: 'HRV评分' }],
        max: 100,
        axisLine: {
          lineStyle: {
            width: 30,
            color: [
              [0.4, '#ff4d4f'],
              [0.6, '#faad14'],
              [0.8, '#52c41a'],
              [1, '#1890ff']
            ]
          }
        }
      }]
    };
  };

  // 血压预测图表配置
  const getBPPredictionChartOption = () => {
    if (!analysisData.physiological?.blood_pressure_prediction?.status) return null;
    const bp = analysisData.physiological.blood_pressure_prediction;
    
    return {
      title: { text: '血压预测趋势', left: 'center' },
      tooltip: { trigger: 'axis' },
      legend: { data: ['收缩压预测', '舒张压预测'], bottom: 10 },
      xAxis: {
        type: 'category',
        data: bp.predictions?.map((p: any) => `第${p.day}天`) || []
      },
      yAxis: { type: 'value', name: 'mmHg' },
      series: [
        {
          name: '收缩压预测',
          type: 'line',
          data: bp.predictions?.map((p: any) => p.predicted_systolic) || [],
          smooth: true,
          itemStyle: { color: '#ff4d4f' }
        },
        {
          name: '舒张压预测',
          type: 'line',
          data: bp.predictions?.map((p: any) => p.predicted_diastolic) || [],
          smooth: true,
          itemStyle: { color: '#1890ff' }
        }
      ]
    };
  };

  // 行为活动图表配置
  const getActivityChartOption = () => {
    if (!analysisData.behavioral?.activity_trajectory?.status) return null;
    const trajectory = analysisData.behavioral.activity_trajectory;
    
    return {
      title: { text: '24小时活动分布', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: Array.from({ length: 24 }, (_, i) => `${i}:00`)
      },
      yAxis: { type: 'value', name: '活动次数' },
      series: [{
        type: 'bar',
        data: trajectory.activity_by_hour || [],
        itemStyle: { color: '#52c41a' }
      }]
    };
  };

  // 健康预测图表配置
  const getPredictionChartOption = () => {
    if (!analysisData.predictions?.predictions) return null;
    const predictions = analysisData.predictions.predictions;
    
    return {
      title: { text: '多指标健康预测', left: 'center' },
      tooltip: { trigger: 'axis' },
      legend: { data: Object.keys(predictions), bottom: 10 },
      xAxis: {
        type: 'category',
        data: predictions[Object.keys(predictions)[0]]?.predictions?.map((p: any) => p.date.split('T')[0]) || []
      },
      yAxis: { type: 'value', name: '预测值' },
      series: Object.entries(predictions).map(([key, pred]: any) => ({
        name: key,
        type: 'line',
        data: pred.predictions?.map((p: any) => p.predicted_value) || [],
        smooth: true
      }))
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 标题 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">AI智能体核心算法系统</h1>
          <p className="text-lg text-gray-600">多模态健康分析与预测平台</p>
        </div>

        {/* 用户ID输入 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <label className="block text-sm font-medium text-gray-700 mb-2">用户ID</label>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="输入老人用户ID"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* 功能按钮组 */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          <button
            onClick={handleMultimodalFusion}
            disabled={loading}
            className="flex flex-col items-center justify-center p-4 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-400 text-white rounded-lg shadow-md transition-all"
          >
            <Zap size={32} className="mb-2" />
            <span className="text-sm font-medium">多模态融合</span>
          </button>

          <button
            onClick={handlePhysiologicalAnalysis}
            disabled={loading}
            className="flex flex-col items-center justify-center p-4 bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white rounded-lg shadow-md transition-all"
          >
            <Heart size={32} className="mb-2" />
            <span className="text-sm font-medium">生理分析</span>
          </button>

          <button
            onClick={handleBehaviorRecognition}
            disabled={loading}
            className="flex flex-col items-center justify-center p-4 bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white rounded-lg shadow-md transition-all"
          >
            <Activity size={32} className="mb-2" />
            <span className="text-sm font-medium">行为识别</span>
          </button>

          <button
            onClick={() => handleHealthPrediction('7days')}
            disabled={loading}
            className="flex flex-col items-center justify-center p-4 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-lg shadow-md transition-all"
          >
            <TrendingUp size={32} className="mb-2" />
            <span className="text-sm font-medium">7天预测</span>
          </button>

          <button
            onClick={handleRealtimeAnalysis}
            disabled={loading}
            className="flex flex-col items-center justify-center p-4 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-400 text-white rounded-lg shadow-md transition-all"
          >
            <Brain size={32} className="mb-2" />
            <span className="text-sm font-medium">实时分析</span>
          </button>

          <button
            onClick={handleAnomalyDetection}
            disabled={loading}
            className="flex flex-col items-center justify-center p-4 bg-yellow-500 hover:bg-yellow-600 disabled:bg-gray-400 text-white rounded-lg shadow-md transition-all"
          >
            <AlertTriangle size={32} className="mb-2" />
            <span className="text-sm font-medium">异常检测</span>
          </button>
        </div>

        {/* 标签切换 */}
        <div className="bg-white rounded-lg shadow-md mb-8">
          <div className="flex border-b">
            {['overview', 'physiological', 'behavioral', 'predictions', 'realtime', 'anomalies'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab === 'overview' && '总览'}
                {tab === 'physiological' && '生理分析'}
                {tab === 'behavioral' && '行为模式'}
                {tab === 'predictions' && '健康预测'}
                {tab === 'realtime' && '实时分析'}
                {tab === 'anomalies' && '异常检测'}
              </button>
            ))}
          </div>

          {/* 内容区域 */}
          <div className="p-6">
            {/* 总览标签 */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">系统功能概览</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-blue-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-blue-900 mb-3">多模态数据融合</h3>
                    <p className="text-gray-700">整合手环、床垫、摄像头、环境传感器等多源数据，提取综合特征进行分析</p>
                  </div>
                  <div className="bg-red-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-red-900 mb-3">生理数据分析</h3>
                    <p className="text-gray-700">心率变异分析、血压预测、睡眠质量评估、生理指标异常检测</p>
                  </div>
                  <div className="bg-green-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-green-900 mb-3">行为模式识别</h3>
                    <p className="text-gray-700">活动轨迹分析、异常行为检测、认知能力评估、日常活动模式识别</p>
                  </div>
                  <div className="bg-purple-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-purple-900 mb-3">健康预测模型</h3>
                    <p className="text-gray-700">7天/30天时间序列预测、个性化风险评估、动态阈值调整、提前预警</p>
                  </div>
                  <div className="bg-orange-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-orange-900 mb-3">实时AI分析</h3>
                    <p className="text-gray-700">边缘计算优化、实时推理引擎、延迟小于100ms、快速响应</p>
                  </div>
                  <div className="bg-yellow-50 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold text-yellow-900 mb-3">异常检测系统</h3>
                    <p className="text-gray-700">多维度异常检测、关联分析、智能预警、覆盖率超98%</p>
                  </div>
                </div>
              </div>
            )}

            {/* 生理分析标签 */}
            {activeTab === 'physiological' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">生理数据分析结果</h2>
                {analysisData.physiological ? (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* HRV图表 */}
                      {getHRVChartOption() && (
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <EChartsReact option={getHRVChartOption()} style={{ height: '300px' }} />
                        </div>
                      )}

                      {/* 血压预测图表 */}
                      {getBPPredictionChartOption() && (
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <EChartsReact option={getBPPredictionChartOption()} style={{ height: '300px' }} />
                        </div>
                      )}
                    </div>

                    {/* AI分析报告 */}
                    {analysisData.physiological.ai_insights && (
                      <div className="bg-blue-50 p-6 rounded-lg">
                        <h3 className="text-lg font-semibold text-blue-900 mb-3">AI综合分析</h3>
                        <p className="text-gray-700 whitespace-pre-wrap">{analysisData.physiological.ai_insights}</p>
                      </div>
                    )}

                    {/* 详细数据 */}
                    <div className="bg-gray-50 p-6 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">详细分析数据</h3>
                      <pre className="text-sm text-gray-700 overflow-auto">
                        {JSON.stringify(analysisData.physiological, null, 2)}
                      </pre>
                    </div>
                  </>
                ) : (
                  <p className="text-gray-500 text-center py-8">暂无生理分析数据，请点击上方"生理分析"按钮开始分析</p>
                )}
              </div>
            )}

            {/* 行为模式标签 */}
            {activeTab === 'behavioral' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">行为模式识别结果</h2>
                {analysisData.behavioral ? (
                  <>
                    {/* 活动轨迹图表 */}
                    {getActivityChartOption() && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <EChartsReact option={getActivityChartOption()} style={{ height: '400px' }} />
                      </div>
                    )}

                    {/* 认知评估 */}
                    {analysisData.behavioral.cognitive_assessment && (
                      <div className="bg-green-50 p-6 rounded-lg">
                        <h3 className="text-lg font-semibold text-green-900 mb-3">认知能力评估</h3>
                        <p className="text-2xl font-bold text-gray-900 mb-2">
                          评分: {(analysisData.behavioral.cognitive_assessment.score * 100).toFixed(0)}/100
                        </p>
                        <p className="text-gray-700">评级: {analysisData.behavioral.cognitive_assessment.level}</p>
                        <p className="text-gray-700 mt-2">{analysisData.behavioral.cognitive_assessment.recommendation}</p>
                      </div>
                    )}

                    {/* AI行为分析 */}
                    {analysisData.behavioral.ai_insights && (
                      <div className="bg-blue-50 p-6 rounded-lg">
                        <h3 className="text-lg font-semibold text-blue-900 mb-3">AI行为分析</h3>
                        <p className="text-gray-700 whitespace-pre-wrap">{analysisData.behavioral.ai_insights}</p>
                      </div>
                    )}

                    {/* 详细数据 */}
                    <div className="bg-gray-50 p-6 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">详细识别数据</h3>
                      <pre className="text-sm text-gray-700 overflow-auto max-h-96">
                        {JSON.stringify(analysisData.behavioral, null, 2)}
                      </pre>
                    </div>
                  </>
                ) : (
                  <p className="text-gray-500 text-center py-8">暂无行为模式数据，请点击上方"行为识别"按钮开始识别</p>
                )}
              </div>
            )}

            {/* 健康预测标签 */}
            {activeTab === 'predictions' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">健康预测结果</h2>
                {analysisData.predictions ? (
                  <>
                    {/* 预测图表 */}
                    {getPredictionChartOption() && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <EChartsReact option={getPredictionChartOption()} style={{ height: '400px' }} />
                      </div>
                    )}

                    {/* 提前预警 */}
                    {analysisData.predictions.early_warning?.triggered && (
                      <div className="bg-red-50 border-l-4 border-red-500 p-6 rounded-lg">
                        <h3 className="text-lg font-semibold text-red-900 mb-3">提前预警</h3>
                        <p className="text-gray-700 mb-2">
                          紧急程度: <span className="font-bold text-red-700">{analysisData.predictions.early_warning.urgency}</span>
                        </p>
                        <p className="text-gray-700 mb-2">触发类型: {analysisData.predictions.early_warning.types.join(', ')}</p>
                        <div className="mt-3">
                          <p className="font-semibold text-gray-900 mb-2">建议行动:</p>
                          <ul className="list-disc list-inside space-y-1">
                            {analysisData.predictions.early_warning.recommended_actions.map((action: string, idx: number) => (
                              <li key={idx} className="text-gray-700">{action}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}

                    {/* AI预测报告 */}
                    {analysisData.predictions.ai_report && (
                      <div className="bg-blue-50 p-6 rounded-lg">
                        <h3 className="text-lg font-semibold text-blue-900 mb-3">AI预测报告</h3>
                        <p className="text-gray-700 whitespace-pre-wrap">{analysisData.predictions.ai_report}</p>
                      </div>
                    )}

                    {/* 详细数据 */}
                    <div className="bg-gray-50 p-6 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">详细预测数据</h3>
                      <pre className="text-sm text-gray-700 overflow-auto max-h-96">
                        {JSON.stringify(analysisData.predictions, null, 2)}
                      </pre>
                    </div>
                  </>
                ) : (
                  <p className="text-gray-500 text-center py-8">暂无预测数据，请点击上方"7天预测"按钮开始预测</p>
                )}
              </div>
            )}

            {/* 实时分析标签 */}
            {activeTab === 'realtime' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">实时AI分析结果</h2>
                {analysisData.realtime ? (
                  <>
                    {/* 性能指标 */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-blue-50 p-6 rounded-lg text-center">
                        <p className="text-sm text-gray-600 mb-2">处理延迟</p>
                        <p className="text-3xl font-bold text-blue-600">{analysisData.realtime.processing_time_ms}ms</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {analysisData.realtime.performance.target_met ? '目标达成' : '超出目标'}
                        </p>
                      </div>
                      <div className="bg-green-50 p-6 rounded-lg text-center">
                        <p className="text-sm text-gray-600 mb-2">健康状态</p>
                        <p className="text-3xl font-bold text-green-600">
                          {analysisData.realtime.real_time_inference?.results?.health_status?.status || 'N/A'}
                        </p>
                      </div>
                      <div className="bg-red-50 p-6 rounded-lg text-center">
                        <p className="text-sm text-gray-600 mb-2">风险等级</p>
                        <p className="text-3xl font-bold text-red-600">
                          {analysisData.realtime.risk_assessment?.overall_risk_level || 'low'}
                        </p>
                      </div>
                    </div>

                    {/* 预警信息 */}
                    {analysisData.realtime.alert_triggered && (
                      <div className="bg-red-50 border-l-4 border-red-500 p-6 rounded-lg">
                        <h3 className="text-lg font-semibold text-red-900 mb-3">实时预警</h3>
                        <ul className="list-disc list-inside space-y-1">
                          {analysisData.realtime.risk_assessment.immediate_actions.map((action: string, idx: number) => (
                            <li key={idx} className="text-gray-700">{action}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* 详细数据 */}
                    <div className="bg-gray-50 p-6 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">详细分析数据</h3>
                      <pre className="text-sm text-gray-700 overflow-auto max-h-96">
                        {JSON.stringify(analysisData.realtime, null, 2)}
                      </pre>
                    </div>
                  </>
                ) : (
                  <p className="text-gray-500 text-center py-8">暂无实时分析数据，请点击上方"实时分析"按钮开始分析</p>
                )}
              </div>
            )}

            {/* 异常检测标签 */}
            {activeTab === 'anomalies' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">异常检测结果</h2>
                {analysisData.anomalies ? (
                  <>
                    {/* 异常统计 */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="bg-red-50 p-4 rounded-lg text-center">
                        <p className="text-sm text-gray-600 mb-1">危急</p>
                        <p className="text-2xl font-bold text-red-600">
                          {analysisData.anomalies.detection_summary.critical}
                        </p>
                      </div>
                      <div className="bg-orange-50 p-4 rounded-lg text-center">
                        <p className="text-sm text-gray-600 mb-1">高风险</p>
                        <p className="text-2xl font-bold text-orange-600">
                          {analysisData.anomalies.detection_summary.high}
                        </p>
                      </div>
                      <div className="bg-yellow-50 p-4 rounded-lg text-center">
                        <p className="text-sm text-gray-600 mb-1">中风险</p>
                        <p className="text-2xl font-bold text-yellow-600">
                          {analysisData.anomalies.detection_summary.medium}
                        </p>
                      </div>
                      <div className="bg-blue-50 p-4 rounded-lg text-center">
                        <p className="text-sm text-gray-600 mb-1">低风险</p>
                        <p className="text-2xl font-bold text-blue-600">
                          {analysisData.anomalies.detection_summary.low}
                        </p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg text-center">
                        <p className="text-sm text-gray-600 mb-1">总计</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {analysisData.anomalies.detection_summary.total_anomalies}
                        </p>
                      </div>
                    </div>

                    {/* 异常列表 */}
                    {analysisData.anomalies.anomalies && analysisData.anomalies.anomalies.length > 0 && (
                      <div className="bg-white border rounded-lg overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">参数</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">值</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">严重程度</th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">描述</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {analysisData.anomalies.anomalies.slice(0, 10).map((anomaly: any, idx: number) => (
                              <tr key={idx}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{anomaly.type}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{anomaly.parameter}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  {typeof anomaly.value === 'object' ? JSON.stringify(anomaly.value) : anomaly.value}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <span className={`px-2 py-1 text-xs rounded-full ${
                                    anomaly.severity === 'critical' ? 'bg-red-100 text-red-800' :
                                    anomaly.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                                    anomaly.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-blue-100 text-blue-800'
                                  }`}>
                                    {anomaly.severity}
                                  </span>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-900">{anomaly.description}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* AI异常分析 */}
                    {analysisData.anomalies.ai_analysis && (
                      <div className="bg-blue-50 p-6 rounded-lg">
                        <h3 className="text-lg font-semibold text-blue-900 mb-3">AI异常分析</h3>
                        <p className="text-gray-700 whitespace-pre-wrap">{analysisData.anomalies.ai_analysis}</p>
                      </div>
                    )}

                    {/* 详细数据 */}
                    <div className="bg-gray-50 p-6 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">详细检测数据</h3>
                      <pre className="text-sm text-gray-700 overflow-auto max-h-96">
                        {JSON.stringify(analysisData.anomalies, null, 2)}
                      </pre>
                    </div>
                  </>
                ) : (
                  <p className="text-gray-500 text-center py-8">暂无异常检测数据，请点击上方"异常检测"按钮开始检测</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Loading遮罩 */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-xl">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-700 font-medium">AI分析处理中...</p>
          </div>
        </div>
      )}
    </div>
  );
}
