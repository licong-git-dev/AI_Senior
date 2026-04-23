import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Heart, 
  Brain, 
  Activity, 
  AlertTriangle, 
  TrendingUp, 
  Clock, 
  CheckCircle,
  ArrowLeft,
  RefreshCw,
  Zap,
  BarChart3,
  Calendar,
  User,
  Target
} from 'lucide-react';
import { supabase } from '../../lib/supabase';

interface RiskAssessment {
  risk_type: 'cardiovascular' | 'diabetes' | 'fall' | 'cognitive';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_score: number;
  confidence: number;
  factors: Array<{
    factor: string;
    impact_score: number;
    description: string;
  }>;
  recommendations: string[];
  time_horizon: string;
}

interface PredictionResult {
  user_id: string;
  timestamp: string;
  overall_health_score: number;
  risk_assessments: RiskAssessment[];
  data_quality_score: number;
  prediction_confidence: number;
  processing_time_ms: number;
  data_fusion_quality: number;
}

const riskTypeConfig = {
  cardiovascular: {
    title: '心血管疾病风险',
    icon: Heart,
    color: 'from-red-500 to-pink-600',
    bgColor: 'bg-red-50',
    textColor: 'text-red-600',
    description: '评估心脏血管系统疾病风险'
  },
  diabetes: {
    title: '糖尿病风险',
    icon: Zap,
    color: 'from-orange-500 to-amber-600',
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-600',
    description: '评估血糖代谢异常风险'
  },
  fall: {
    title: '跌倒风险',
    icon: AlertTriangle,
    color: 'from-yellow-500 to-orange-600',
    bgColor: 'bg-yellow-50',
    textColor: 'text-yellow-600',
    description: '评估跌倒意外风险概率'
  },
  cognitive: {
    title: '认知功能退化风险',
    icon: Brain,
    color: 'from-purple-500 to-indigo-600',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-600',
    description: '评估认知能力退化风险'
  }
};

const riskLevelConfig = {
  low: { 
    level: '低风险', 
    color: 'text-green-600', 
    bgColor: 'bg-green-100', 
    progressColor: 'bg-green-500',
    description: '风险较低，继续保持健康生活方式'
  },
  medium: { 
    level: '中等风险', 
    color: 'text-yellow-600', 
    bgColor: 'bg-yellow-100', 
    progressColor: 'bg-yellow-500',
    description: '需要关注相关健康指标'
  },
  high: { 
    level: '高风险', 
    color: 'text-orange-600', 
    bgColor: 'bg-orange-100', 
    progressColor: 'bg-orange-500',
    description: '建议及时咨询医疗专家'
  },
  critical: { 
    level: '极高风险', 
    color: 'text-red-600', 
    bgColor: 'bg-red-100', 
    progressColor: 'bg-red-500',
    description: '需要立即就医检查'
  }
};

export default function HealthRiskPrediction({ session }: { session: any }) {
  const navigate = useNavigate();
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  const userId = session?.user?.id;

  const performRiskPrediction = async () => {
    if (!userId) return;

    setLoading(true);
    setError(null);

    try {
      const { data, error } = await supabase.functions.invoke('health-risk-prediction', {
        body: {
          user_id: userId,
          data_sources: ['health_data', 'device_data', 'profile_data'],
          include_detailed_analysis: true
        }
      });

      if (error) throw error;

      setPredictionResult(data.data);
      setLastUpdate(new Date().toLocaleString('zh-CN'));
    } catch (err) {
      setError(err instanceof Error ? err.message : '预测分析失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) {
      performRiskPrediction();
    }
  }, [userId]);

  const getRiskIcon = (riskType: string) => {
    const config = riskTypeConfig[riskType as keyof typeof riskTypeConfig];
    const Icon = config.icon;
    return <Icon className="w-6 h-6" />;
  };

  const getRiskLevelInfo = (level: string) => {
    return riskLevelConfig[level as keyof typeof riskLevelConfig];
  };

  const getOverallHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getOverallHealthBg = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    if (score >= 40) return 'bg-orange-100';
    return 'bg-red-100';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => navigate('/health')}
            className="inline-flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            返回健康仪表盘
          </button>
          
          <button
            onClick={performRiskPrediction}
            disabled={loading}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            {loading ? '分析中...' : '重新分析'}
          </button>
        </div>

        {/* 页面标题 */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <BarChart3 className="w-10 h-10 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-800">智能健康风险预测</h1>
          </div>
          <p className="text-xl text-gray-600">基于AI的多维度健康风险评估系统</p>
          <div className="mt-4 flex items-center justify-center gap-6 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              <span>准确率 ≥95%</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>响应时间 ≤2分钟</span>
            </div>
            {lastUpdate && (
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>最后更新: {lastUpdate}</span>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </div>
        )}

        {predictionResult && (
          <div className="space-y-8">
            {/* 整体健康评分 */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-4 mb-6">
                <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
                  <User className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">整体健康评分</h2>
                  <p className="text-gray-600">综合评估您的健康风险状况</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className={`p-6 rounded-lg ${getOverallHealthBg(predictionResult.overall_health_score)}`}>
                  <div className="text-center">
                    <div className={`text-4xl font-bold ${getOverallHealthColor(predictionResult.overall_health_score)}`}>
                      {predictionResult.overall_health_score}
                    </div>
                    <div className="text-gray-600 mt-2">总体健康分</div>
                  </div>
                </div>

                <div className="p-6 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-blue-600">
                      {Math.round(predictionResult.prediction_confidence * 100)}%
                    </div>
                    <div className="text-gray-600 mt-2">预测置信度</div>
                  </div>
                </div>

                <div className="p-6 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-green-600">
                      {predictionResult.data_quality_score}
                    </div>
                    <div className="text-gray-600 mt-2">数据质量分</div>
                  </div>
                </div>

                <div className="p-6 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-purple-600">
                      {predictionResult.processing_time_ms}ms
                    </div>
                    <div className="text-gray-600 mt-2">分析耗时</div>
                  </div>
                </div>
              </div>
            </div>

            {/* 风险评估卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {predictionResult.risk_assessments.map((risk, index) => {
                const config = riskTypeConfig[risk.risk_type];
                const levelConfig = getRiskLevelInfo(risk.risk_level);
                const Icon = config.icon;

                return (
                  <div key={index} className="bg-white rounded-xl shadow-lg overflow-hidden">
                    <div className={`h-2 bg-gradient-to-r ${config.color}`}></div>
                    
                    <div className="p-6">
                      <div className="flex items-center gap-4 mb-4">
                        <div className={`p-3 bg-gradient-to-r ${config.color} rounded-lg`}>
                          <Icon className="w-6 h-6 text-white" />
                        </div>
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-gray-800">{config.title}</h3>
                          <p className="text-gray-600 text-sm">{config.description}</p>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${levelConfig.bgColor} ${levelConfig.color}`}>
                          {levelConfig.level}
                        </div>
                      </div>

                      {/* 风险评分进度条 */}
                      <div className="mb-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-gray-600">风险评分</span>
                          <span className="text-sm font-semibold text-gray-800">{risk.risk_score}/100</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div 
                            className={`h-3 rounded-full ${levelConfig.progressColor} transition-all duration-500`}
                            style={{ width: `${risk.risk_score}%` }}
                          ></div>
                        </div>
                      </div>

                      {/* 置信度 */}
                      <div className="flex items-center gap-2 mb-4">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span className="text-sm text-gray-600">预测置信度: </span>
                        <span className="text-sm font-semibold text-gray-800">
                          {Math.round(risk.confidence * 100)}%
                        </span>
                      </div>

                      {/* 风险因素 */}
                      <div className="mb-4">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">主要风险因素</h4>
                        <div className="space-y-2">
                          {risk.factors.slice(0, 3).map((factor, idx) => (
                            <div key={idx} className="flex items-center gap-2">
                              <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                              <span className="text-sm text-gray-600">{factor.factor}</span>
                              <span className="text-xs text-red-500">({Math.round(factor.impact_score * 100)}%)</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 建议 */}
                      {risk.recommendations.length > 0 && (
                        <div className="mb-4">
                          <h4 className="text-sm font-semibold text-gray-700 mb-2">健康建议</h4>
                          <div className="space-y-1">
                            {risk.recommendations.slice(0, 2).map((rec, idx) => (
                              <div key={idx} className="text-sm text-gray-600 bg-gray-50 rounded p-2">
                                • {rec}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 时间范围 */}
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Calendar className="w-4 h-4" />
                        <span>评估周期: {risk.time_horizon}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* 数据质量报告 */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">数据质量分析</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-2">
                    {predictionResult.data_quality_score}
                  </div>
                  <div className="text-gray-600">数据完整度</div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${predictionResult.data_quality_score}%` }}
                    ></div>
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 mb-2">
                    {predictionResult.data_fusion_quality}
                  </div>
                  <div className="text-gray-600">数据融合质量</div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${predictionResult.data_fusion_quality}%` }}
                    ></div>
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600 mb-2">
                    {Math.round(predictionResult.prediction_confidence * 100)}%
                  </div>
                  <div className="text-gray-600">整体置信度</div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className="bg-purple-500 h-2 rounded-full"
                      style={{ width: `${predictionResult.prediction_confidence * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {!predictionResult && !loading && (
          <div className="text-center py-12">
            <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-600 mb-2">暂无风险预测数据</h3>
            <p className="text-gray-500 mb-6">请点击"重新分析"开始您的健康风险评估</p>
            <button
              onClick={performRiskPrediction}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all"
            >
              <TrendingUp className="w-5 h-5" />
              开始分析
            </button>
          </div>
        )}
      </div>
    </div>
  );
}