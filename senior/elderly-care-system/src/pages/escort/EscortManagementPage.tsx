import { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import { useNavigate } from 'react-router-dom';
import LocationTrackingMap from '../../components/escort/LocationTrackingMap';

interface ServiceOrder {
  id: string;
  order_number: string;
  elderly_id: string;
  worker_id: string | null;
  order_status: string;
  scheduled_time: string;
  destination_location: string;
  total_fee: number;
  payment_status: string;
  created_at: string;
}

interface EscortWorker {
  id: string;
  name: string;
  phone: string;
  rating: number;
  work_status: string;
  total_orders: number;
  completed_orders: number;
}

interface Statistics {
  total_orders: number;
  pending_orders: number;
  in_progress_orders: number;
  completed_orders: number;
  total_workers: number;
  available_workers: number;
}

export default function EscortManagementPage({ session }: { session: any }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [orders, setOrders] = useState<ServiceOrder[]>([]);
  const [workers, setWorkers] = useState<EscortWorker[]>([]);
  const [stats, setStats] = useState<Statistics>({
    total_orders: 0,
    pending_orders: 0,
    in_progress_orders: 0,
    completed_orders: 0,
    total_workers: 0,
    available_workers: 0
  });
  const [selectedTab, setSelectedTab] = useState<'orders' | 'workers' | 'map'>('orders');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [inProgressOrders, setInProgressOrders] = useState<ServiceOrder[]>([]);
  const [selectedOrderForMap, setSelectedOrderForMap] = useState<ServiceOrder | null>(null);

  useEffect(() => {
    loadData();
    
    // 设置定时刷新
    const interval = setInterval(loadData, 15000); // 每15秒刷新
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    await Promise.all([
      loadOrders(),
      loadWorkers(),
      loadStats()
    ]);
  };

  const loadOrders = async () => {
    try {
      const { data, error } = await supabase
        .from('service_orders')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;
      setOrders(data || []);
      
      // 筛选进行中的订单
      setInProgressOrders((data || []).filter(o => o.order_status === 'in_progress'));
    } catch (error) {
      console.error('加载订单失败:', error);
    }
  };

  const loadWorkers = async () => {
    try {
      const { data, error } = await supabase
        .from('escort_workers')
        .select('*')
        .order('rating', { ascending: false });

      if (error) throw error;
      setWorkers(data || []);
    } catch (error) {
      console.error('加载陪诊师失败:', error);
    }
  };

  const loadStats = async () => {
    try {
      // 统计订单数据
      const { data: ordersData } = await supabase
        .from('service_orders')
        .select('order_status');

      // 统计陪诊师数据
      const { data: workersData } = await supabase
        .from('escort_workers')
        .select('work_status');

      if (ordersData) {
        setStats({
          total_orders: ordersData.length,
          pending_orders: ordersData.filter(o => o.order_status === 'pending').length,
          in_progress_orders: ordersData.filter(o => o.order_status === 'in_progress').length,
          completed_orders: ordersData.filter(o => o.order_status === 'completed').length,
          total_workers: workersData?.length || 0,
          available_workers: workersData?.filter((w: any) => w.work_status === 'available').length || 0
        });
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      assigned: 'bg-blue-100 text-blue-800',
      accepted: 'bg-purple-100 text-purple-800',
      in_progress: 'bg-green-100 text-green-800',
      completed: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待分配',
      assigned: '已分配',
      accepted: '已接单',
      in_progress: '进行中',
      completed: '已完成',
      cancelled: '已取消'
    };
    return texts[status] || status;
  };

  const getWorkStatusColor = (status: string) => {
    return status === 'available' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800';
  };

  const getWorkStatusText = (status: string) => {
    return status === 'available' ? '空闲' : '工作中';
  };

  const filteredOrders = statusFilter === 'all' 
    ? orders 
    : orders.filter(o => o.order_status === statusFilter);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50">
      <div className="container mx-auto px-4 py-8">
        {/* 头部 */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">陪诊管理中心</h1>
            <p className="text-gray-600 mt-2">订单调度与陪诊师管理</p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            返回首页
          </button>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-4">
            <div className="text-sm text-gray-600 mb-1">总订单数</div>
            <div className="text-3xl font-bold text-indigo-600">{stats.total_orders}</div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-4">
            <div className="text-sm text-gray-600 mb-1">待分配</div>
            <div className="text-3xl font-bold text-yellow-600">{stats.pending_orders}</div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-4">
            <div className="text-sm text-gray-600 mb-1">进行中</div>
            <div className="text-3xl font-bold text-green-600">{stats.in_progress_orders}</div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-4">
            <div className="text-sm text-gray-600 mb-1">已完成</div>
            <div className="text-3xl font-bold text-gray-600">{stats.completed_orders}</div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-4">
            <div className="text-sm text-gray-600 mb-1">总陪诊师</div>
            <div className="text-3xl font-bold text-purple-600">{stats.total_workers}</div>
          </div>
          <div className="bg-white rounded-xl shadow-lg p-4">
            <div className="text-sm text-gray-600 mb-1">可用陪诊师</div>
            <div className="text-3xl font-bold text-blue-600">{stats.available_workers}</div>
          </div>
        </div>

        {/* 标签页 */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="border-b border-gray-200">
            <div className="flex">
              <button
                onClick={() => setSelectedTab('orders')}
                className={`flex-1 px-6 py-4 text-center font-medium transition-colors ${
                  selectedTab === 'orders'
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                订单管理
              </button>
              <button
                onClick={() => setSelectedTab('workers')}
                className={`flex-1 px-6 py-4 text-center font-medium transition-colors ${
                  selectedTab === 'workers'
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                陪诊师管理
              </button>
              <button
                onClick={() => setSelectedTab('map')}
                className={`flex-1 px-6 py-4 text-center font-medium transition-colors ${
                  selectedTab === 'map'
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                实时地图 ({inProgressOrders.length})
              </button>
            </div>
          </div>

          <div className="p-6">
            {/* 订单管理 */}
            {selectedTab === 'orders' && (
              <div>
                {/* 状态筛选 */}
                <div className="flex gap-2 mb-6 flex-wrap">
                  <button
                    onClick={() => setStatusFilter('all')}
                    className={`px-4 py-2 rounded-lg transition-colors ${
                      statusFilter === 'all'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    全部 ({orders.length})
                  </button>
                  <button
                    onClick={() => setStatusFilter('pending')}
                    className={`px-4 py-2 rounded-lg transition-colors ${
                      statusFilter === 'pending'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    待分配 ({stats.pending_orders})
                  </button>
                  <button
                    onClick={() => setStatusFilter('in_progress')}
                    className={`px-4 py-2 rounded-lg transition-colors ${
                      statusFilter === 'in_progress'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    进行中 ({stats.in_progress_orders})
                  </button>
                  <button
                    onClick={() => setStatusFilter('completed')}
                    className={`px-4 py-2 rounded-lg transition-colors ${
                      statusFilter === 'completed'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    已完成 ({stats.completed_orders})
                  </button>
                </div>

                {/* 订单列表 */}
                <div className="space-y-4">
                  {filteredOrders.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                      <p>暂无订单数据</p>
                    </div>
                  ) : (
                    filteredOrders.map((order) => (
                      <div
                        key={order.id}
                        className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="text-lg font-semibold text-gray-800">订单号：{order.order_number}</h3>
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(order.order_status)}`}>
                                {getStatusText(order.order_status)}
                              </span>
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                order.payment_status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {order.payment_status === 'paid' ? '已支付' : '未支付'}
                              </span>
                            </div>
                            <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
                              <div>
                                <span className="font-medium">预约时间：</span>
                                {new Date(order.scheduled_time).toLocaleString('zh-CN')}
                              </div>
                              <div>
                                <span className="font-medium">服务费用：</span>
                                <span className="text-indigo-600 font-semibold">¥{order.total_fee}</span>
                              </div>
                              <div>
                                <span className="font-medium">陪诊师ID：</span>
                                {order.worker_id || '未分配'}
                              </div>
                            </div>
                            <div className="mt-2 text-sm text-gray-500">
                              <span className="font-medium">目的地：</span>
                              {order.destination_location}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* 陪诊师管理 */}
            {selectedTab === 'workers' && (
              <div className="space-y-4">
                {workers.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    <p>暂无陪诊师数据</p>
                  </div>
                ) : (
                  workers.map((worker) => (
                    <div
                      key={worker.id}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-gray-800">{worker.name}</h3>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getWorkStatusColor(worker.work_status)}`}>
                              {getWorkStatusText(worker.work_status)}
                            </span>
                            <span className="text-yellow-500">
                              {'★'.repeat(Math.floor(worker.rating))}
                              {' '}
                              {worker.rating.toFixed(1)}
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
                            <div>
                              <span className="font-medium">联系电话：</span>
                              {worker.phone}
                            </div>
                            <div>
                              <span className="font-medium">完成订单：</span>
                              {worker.completed_orders}
                            </div>
                            <div>
                              <span className="font-medium">总订单数：</span>
                              {worker.total_orders}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* 实时地图 */}
            {selectedTab === 'map' && (
              <div>
                {inProgressOrders.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                    </svg>
                    <p>当前没有进行中的订单</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* 订单选择 */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-800 mb-4">选择要查看的订单</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {inProgressOrders.map((order) => (
                          <button
                            key={order.id}
                            onClick={() => setSelectedOrderForMap(order)}
                            className={`text-left p-4 border-2 rounded-lg transition-all ${
                              selectedOrderForMap?.id === order.id
                                ? 'border-indigo-500 bg-indigo-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <div className="flex justify-between items-start mb-2">
                              <span className="font-semibold text-gray-800">{order.order_number}</span>
                              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                                进行中
                              </span>
                            </div>
                            <p className="text-sm text-gray-600">{order.destination_location}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {new Date(order.scheduled_time).toLocaleString('zh-CN')}
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* 地图显示 */}
                    {selectedOrderForMap && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">
                          订单追踪：{selectedOrderForMap.order_number}
                        </h3>
                        <LocationTrackingMap
                          orderId={selectedOrderForMap.id}
                          hospitalLocation={{
                            lat: 30.5928 + Math.random() * 0.1,
                            lng: 114.3055 + Math.random() * 0.1,
                            address: selectedOrderForMap.destination_location
                          }}
                          showRoute={true}
                          autoUpdate={true}
                          height="600px"
                        />
                      </div>
                    )}

                    {!selectedOrderForMap && inProgressOrders.length > 0 && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                        <svg className="w-12 h-12 text-blue-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                        </svg>
                        <p className="text-blue-700">请选择一个订单以查看实时位置</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
