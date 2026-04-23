import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { ArrowLeft, Store, CheckCircle, Clock, XCircle, Star } from 'lucide-react';

export default function ProviderManagement() {
  const [providers, setProviders] = useState<any[]>([]);
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [providersResult, applicationsResult] = await Promise.all([
        supabase.from('service_providers').select('*').order('created_at', { ascending: false }),
        supabase.from('provider_applications').select('*, service_providers(name)').order('created_at', { ascending: false })
      ]);

      setProviders(providersResult.data || []);
      setApplications(applicationsResult.data || []);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const certificationStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const certificationStatusText = (status: string) => {
    switch (status) {
      case 'approved': return '已认证';
      case 'pending': return '待审核';
      case 'rejected': return '已拒绝';
      default: return status;
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
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center">
          <Link to="/" className="text-blue-600 hover:text-blue-700 mr-4">
            <ArrowLeft className="w-6 h-6" />
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">服务商管理端</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">服务商总数</p>
                <p className="text-3xl font-bold text-blue-600">{providers.length}</p>
              </div>
              <Store className="w-12 h-12 text-blue-300" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">已认证</p>
                <p className="text-3xl font-bold text-green-600">
                  {providers.filter(p => p.certification_status === 'approved').length}
                </p>
              </div>
              <CheckCircle className="w-12 h-12 text-green-300" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">待审核</p>
                <p className="text-3xl font-bold text-yellow-600">
                  {providers.filter(p => p.certification_status === 'pending').length}
                </p>
              </div>
              <Clock className="w-12 h-12 text-yellow-300" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-1">平均评分</p>
                <p className="text-3xl font-bold text-orange-600">
                  {(providers.filter(p => p.rating > 0).reduce((sum, p) => sum + p.rating, 0) / 
                    providers.filter(p => p.rating > 0).length || 0).toFixed(1)}
                </p>
              </div>
              <Star className="w-12 h-12 text-orange-300" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 服务商列表 */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">服务商列表</h2>
            <div className="space-y-4">
              {providers.map((provider) => (
                <div key={provider.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">{provider.name}</h3>
                      <p className="text-sm text-gray-600 mb-1">许可证: {provider.license_number}</p>
                      <p className="text-sm text-gray-600 mb-2">
                        电话: {provider.contact_info?.phone || '-'}
                      </p>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {provider.service_types?.map((type: string, index: number) => (
                          <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            {type}
                          </span>
                        ))}
                      </div>
                      {provider.rating > 0 && (
                        <div className="flex items-center">
                          <Star className="w-4 h-4 text-yellow-500 fill-current" />
                          <span className="text-sm font-medium text-gray-900 ml-1">{provider.rating}</span>
                        </div>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${certificationStatusColor(provider.certification_status)}`}>
                      {certificationStatusText(provider.certification_status)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 申请记录 */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">申请记录</h2>
            <div className="space-y-4">
              {applications.map((application) => (
                <div key={application.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">
                        {application.service_providers?.name || '未知服务商'}
                      </h3>
                      <p className="text-sm text-gray-600 mb-1">
                        申请时间: {new Date(application.created_at).toLocaleDateString('zh-CN')}
                      </p>
                      {application.reviewed_at && (
                        <p className="text-sm text-gray-600 mb-1">
                          审核时间: {new Date(application.reviewed_at).toLocaleDateString('zh-CN')}
                        </p>
                      )}
                      {application.review_notes && (
                        <p className="text-sm text-gray-600 mt-2">
                          审核意见: {application.review_notes}
                        </p>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${certificationStatusColor(application.status)}`}>
                      {certificationStatusText(application.status)}
                    </span>
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
