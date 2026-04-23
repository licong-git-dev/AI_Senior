import React, { useState, useEffect } from 'react';
import { Brain, Heart, Book, Coffee, Activity, Star, Filter, TrendingUp } from 'lucide-react';

const SmartRecommendationEngine = () => {
  const [activeTab, setActiveTab] = useState('health');
  const [recommendations, setRecommendations] = useState({
    health: [],
    service: [],
    content: []
  });

  const mockRecommendations = {
    health: [
      {
        id: 1,
        title: '晨练太极拳推荐',
        description: '根据您的健康状况，建议每天早上7-8点进行太极拳锻炼，有助于改善平衡能力和心血管健康',
        type: '运动建议',
        priority: 'high',
        estimatedBenefit: '提升平衡能力20%',
        icon: Activity,
        tags: ['太极拳', '平衡训练', '心血管']
      },
      {
        id: 2,
        title: '营养膳食搭配',
        description: '基于您的血压状况，推荐低钠高钾的饮食方案，有助于血压控制',
        type: '营养建议',
        priority: 'medium',
        estimatedBenefit: '血压控制改善15%',
        icon: Heart,
        tags: ['营养', '血压控制', '膳食']
      },
      {
        id: 3,
        title: '睡眠质量优化',
        description: '建议在晚上9-10点进行冥想放松，睡前避免使用电子设备',
        type: '睡眠建议',
        priority: 'medium',
        estimatedBenefit: '睡眠质量提升25%',
        icon: Star,
        tags: ['睡眠', '冥想', '作息']
      }
    ],
    service: [
      {
        id: 4,
        title: '专业护理服务',
        description: '根据您的护理需求，推荐附近5km内的专业护理服务机构',
        type: '护理服务',
        priority: 'high',
        rating: 4.8,
        distance: '2.3km',
        price: '¥120/小时',
        icon: Heart,
        tags: ['专业护理', '上门服务', '持证护士']
      },
      {
        id: 5,
        title: '康复理疗服务',
        description: '针对您的关节问题，推荐中医理疗和物理治疗服务',
        type: '康复服务',
        priority: 'medium',
        rating: 4.6,
        distance: '1.8km',
        price: '¥80/次',
        icon: Activity,
        tags: ['康复理疗', '中医治疗', '关节护理']
      },
      {
        id: 6,
        title: '心理咨询服务',
        description: '关注您的心理健康，推荐专业心理咨询师进行定期沟通',
        type: '心理服务',
        priority: 'low',
        rating: 4.9,
        distance: '在线服务',
        price: '¥200/小时',
        icon: Star,
        tags: ['心理咨询', '情感支持', '心理健康']
      }
    ],
    content: [
      {
        id: 7,
        title: '春季养生指南',
        description: '针对春季养生特点，为老年人群定制的详细养生指导',
        type: '养生内容',
        priority: 'medium',
        views: '12.5k',
        duration: '8分钟',
        icon: Book,
        tags: ['春季养生', '健康科普', '生活指导']
      },
      {
        id: 8,
        title: '认知训练游戏',
        description: '科学设计的认知训练小游戏，有助于预防和延缓认知衰退',
        type: '娱乐内容',
        priority: 'high',
        views: '8.9k',
        duration: '15分钟',
        icon: Coffee,
        tags: ['认知训练', '游戏娱乐', '脑力锻炼']
      },
      {
        id: 9,
        title: '家庭关系和谐之道',
        description: '与子女沟通的技巧和方法，建立更和谐的家庭关系',
        type: '家庭教育',
        priority: 'low',
        views: '6.7k',
        duration: '12分钟',
        icon: Heart,
        tags: ['家庭关系', '沟通技巧', '心理疏导']
      }
    ]
  };

  useEffect(() => {
    // 模拟API调用
    setRecommendations(mockRecommendations);
  }, []);

  const tabs = [
    { id: 'health', name: '健康建议', icon: Heart },
    { id: 'service', name: '服务推荐', icon: Activity },
    { id: 'content', name: '内容推荐', icon: Book }
  ];

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityText = (priority) => {
    switch (priority) {
      case 'high': return '高优先级';
      case 'medium': return '中优先级';
      case 'low': return '低优先级';
      default: return '普通';
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Brain className="h-8 w-8 mr-3 text-blue-600" />
            智能推荐引擎
          </h1>
          <p className="text-gray-600 mt-2">
            基于AI算法的个性化推荐系统，为您提供定制化的健康建议、服务推荐和内容推荐
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <Filter className="h-4 w-4 inline mr-2" />
            智能筛选
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">今日推荐</p>
              <p className="text-2xl font-semibold text-gray-900">12</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">推荐准确率</p>
              <p className="text-2xl font-semibold text-gray-900">94.2%</p>
            </div>
            <Star className="h-8 w-8 text-yellow-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">用户满意度</p>
              <p className="text-2xl font-semibold text-gray-900">4.8/5</p>
            </div>
            <Heart className="h-8 w-8 text-red-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">活跃用户</p>
              <p className="text-2xl font-semibold text-gray-900">1,258</p>
            </div>
            <Activity className="h-8 w-8 text-blue-600" />
          </div>
        </div>
      </div>

      {/* 标签页导航 */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="h-4 w-4 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* 推荐内容 */}
        <div className="p-6">
          <div className="grid gap-6">
            {recommendations[activeTab]?.map((rec) => (
              <div key={rec.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <rec.icon className="h-8 w-8 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {rec.title}
                      </h3>
                      <p className="text-gray-600 mb-3">
                        {rec.description}
                      </p>
                      <div className="flex flex-wrap gap-2 mb-3">
                        {rec.tags?.map((tag, index) => (
                          <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        {rec.estimatedBenefit && (
                          <span>预期效果: {rec.estimatedBenefit}</span>
                        )}
                        {rec.rating && (
                          <span>评分: {rec.rating}★</span>
                        )}
                        {rec.distance && (
                          <span>距离: {rec.distance}</span>
                        )}
                        {rec.price && (
                          <span>价格: {rec.price}</span>
                        )}
                        {rec.views && (
                          <span>观看: {rec.views}</span>
                        )}
                        {rec.duration && (
                          <span>时长: {rec.duration}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end space-y-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(rec.priority)}`}>
                      {getPriorityText(rec.priority)}
                    </span>
                    <button className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors">
                      查看详情
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 算法说明 */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Brain className="h-5 w-5 mr-2" />
          AI推荐算法说明
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700">
          <div>
            <h4 className="font-medium mb-2">协同过滤算法</h4>
            <p>基于用户行为和偏好相似性进行推荐</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">内容匹配算法</h4>
            <p>根据用户档案和历史数据匹配相关内容</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">深度学习模型</h4>
            <p>运用神经网络进行智能预测和优化</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SmartRecommendationEngine;