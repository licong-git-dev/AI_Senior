import { Link } from 'react-router-dom';
import { Building2, Users, Store, BarChart3 } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            江岸区智慧养老云平台
          </h1>
          <p className="text-xl text-gray-600">
            统一监管 · 数据透明 · 高效协同
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto">
          <Link
            to="/government"
            className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex flex-col items-center text-center">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mb-6">
                <Building2 className="w-10 h-10 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">政府监管端</h2>
              <p className="text-gray-600">
                数据总览 · 政策管理 · 监管预警
              </p>
            </div>
          </Link>

          <Link
            to="/community"
            className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex flex-col items-center text-center">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
                <Users className="w-10 h-10 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">社区管理端</h2>
              <p className="text-gray-600">
                社区管理 · 网点维护 · 服务监控
              </p>
            </div>
          </Link>

          <Link
            to="/provider"
            className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex flex-col items-center text-center">
              <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mb-6">
                <Store className="w-10 h-10 text-purple-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">服务商管理端</h2>
              <p className="text-gray-600">
                服务管理 · 订单处理 · 绩效评估
              </p>
            </div>
          </Link>

          <Link
            to="/dashboard"
            className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex flex-col items-center text-center">
              <div className="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center mb-6">
                <BarChart3 className="w-10 h-10 text-orange-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">数据分析大屏</h2>
              <p className="text-gray-600">
                实时数据 · 趋势分析 · 智能预测
              </p>
            </div>
          </Link>
        </div>

        <div className="mt-16 text-center">
          <div className="bg-white rounded-xl shadow-md p-8 max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">平台概况</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <div className="text-3xl font-bold text-blue-600">10</div>
                <div className="text-gray-600 mt-1">社区覆盖</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600">7,958</div>
                <div className="text-gray-600 mt-1">服务老人</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-purple-600">8</div>
                <div className="text-gray-600 mt-1">服务商</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-orange-600">85.5%</div>
                <div className="text-gray-600 mt-1">平台使用率</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
