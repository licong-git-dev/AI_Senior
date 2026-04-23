import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { ArrowLeft, MapPin, Building, Activity, Star } from 'lucide-react';

export default function CommunityManagement() {
  const [communities, setCommunities] = useState<any[]>([]);
  const [outlets, setOutlets] = useState<any[]>([]);
  const [selectedCommunity, setSelectedCommunity] = useState<string | null>(null);
  const [performance, setPerformance] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedCommunity) {
      loadPerformance(selectedCommunity);
      loadOutlets(selectedCommunity);
    }
  }, [selectedCommunity]);

  const loadData = async () => {
    try {
      const { data: communitiesData } = await supabase
        .from('communities')
        .select('*')
        .order('population_count', { ascending: false });

      setCommunities(communitiesData || []);
      if (communitiesData && communitiesData.length > 0) {
        setSelectedCommunity(communitiesData[0].id);
      }
    } catch (error) {
      console.error('加载社区数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadOutlets = async (communityId: string) => {
    try {
      const { data } = await supabase
        .from('service_outlets')
        .select('*')
        .eq('community_id', communityId)
        .order('created_at', { ascending: false });

      setOutlets(data || []);
    } catch (error) {
      console.error('加载服务网点失败:', error);
    }
  };

  const loadPerformance = async (communityId: string) => {
    try {
      const { data } = await supabase.functions.invoke('community-performance-analytics', {
        body: { community_id: communityId, time_period: 'current_month' }
      });

      if (data?.data) {
        setPerformance(data.data);
      }
    } catch (error) {
      console.error('加载绩效数据失败:', error);
    }
  };

  const serviceLevelColor = (level: string) => {
    switch (level) {
      case '优秀': return 'bg-green-100 text-green-800';
      case '良好': return 'bg-blue-100 text-blue-800';
      case '合格': return 'bg-yellow-100 text-yellow-800';
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

  const selectedCommunityData = communities.find(c => c.id === selectedCommunity);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center">
          <Link to="/" className="text-blue-600 hover:text-blue-700 mr-4">
            <ArrowLeft className="w-6 h-6" />
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">社区管理端</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 社区列表 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">社区列表</h2>
              <div className="space-y-3">
                {communities.map((community) => (
                  <button
                    key={community.id}
                    onClick={() => setSelectedCommunity(community.id)}
                    className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                      selectedCommunity === community.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-gray-900">{community.name}</h3>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${serviceLevelColor(community.service_level)}`}>
                        {community.service_level}
                      </span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600 mb-1">
                      <MapPin className="w-4 h-4 mr-1" />
                      <span className="truncate">{community.address}</span>
                    </div>
                    <div className="text-sm text-gray-600">
                      老人数量: <span className="font-medium text-gray-900">{community.population_count}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 社区详情与服务网点 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 社区信息 */}
            {selectedCommunityData && (
              <div className="bg-white rounded-xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">社区信息</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">社区名称</p>
                    <p className="font-semibold text-gray-900">{selectedCommunityData.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">服务等级</p>
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${serviceLevelColor(selectedCommunityData.service_level)}`}>
                      {selectedCommunityData.service_level}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">老人数量</p>
                    <p className="font-semibold text-gray-900">{selectedCommunityData.population_count}人</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">联系电话</p>
                    <p className="font-semibold text-gray-900">
                      {selectedCommunityData.contact_info?.phone || '-'}
                    </p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-sm text-gray-600 mb-1">地址</p>
                    <p className="font-semibold text-gray-900">{selectedCommunityData.address}</p>
                  </div>
                </div>
              </div>
            )}

            {/* 绩效指标 */}
            {performance && (
              <div className="bg-white rounded-xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                  <Activity className="w-6 h-6 mr-2 text-blue-600" />
                  绩效指标
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">{performance.service_outlets}</p>
                    <p className="text-sm text-gray-600 mt-1">服务网点</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">{performance.service_coverage}%</p>
                    <p className="text-sm text-gray-600 mt-1">服务覆盖率</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <p className="text-2xl font-bold text-purple-600">{performance.user_satisfaction}</p>
                    <p className="text-sm text-gray-600 mt-1">用户满意度</p>
                  </div>
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <p className="text-2xl font-bold text-orange-600">{performance.emergency_response_time}分钟</p>
                    <p className="text-sm text-gray-600 mt-1">应急响应</p>
                  </div>
                </div>
                {performance.ai_analysis && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm font-medium text-gray-900 mb-2">AI分析报告</p>
                    <p className="text-sm text-gray-600 whitespace-pre-line">{performance.ai_analysis}</p>
                  </div>
                )}
              </div>
            )}

            {/* 服务网点 */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                <Building className="w-6 h-6 mr-2 text-green-600" />
                服务网点
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {outlets.map((outlet) => (
                  <div key={outlet.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-gray-900">{outlet.name}</h3>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        outlet.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {outlet.status === 'active' ? '运营中' : '已停用'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">类型: {outlet.type}</p>
                    <p className="text-sm text-gray-600 mb-1">容量: {outlet.capacity}人</p>
                    <p className="text-sm text-gray-600">
                      电话: {outlet.contact_info?.phone || '-'}
                    </p>
                  </div>
                ))}
                {outlets.length === 0 && (
                  <div className="col-span-2 text-center text-gray-500 py-8">
                    暂无服务网点数据
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
