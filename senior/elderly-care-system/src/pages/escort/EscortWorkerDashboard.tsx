import { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import { useNavigate } from 'react-router-dom';

interface ServiceOrder {
  id: string;
  order_number: string;
  elderly_id: string;
  appointment_id: string;
  order_status: string;
  scheduled_time: string;
  estimated_duration: number;
  destination_location: string;
  total_fee: number;
  payment_status: string;
  service_type: string;
  distance: number;
  actual_start_time: string | null;
  actual_end_time: string | null;
  created_at: string;
}

interface EscortWorker {
  id: string;
  name: string;
  phone: string;
  rating: number;
  total_orders: number;
  completed_orders: number;
  work_status: string;
}

export default function EscortWorkerDashboard({ session }: { session: any }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [worker, setWorker] = useState<EscortWorker | null>(null);
  const [pendingOrders, setPendingOrders] = useState<ServiceOrder[]>([]);
  const [myOrders, setMyOrders] = useState<ServiceOrder[]>([]);
  const [selectedTab, setSelectedTab] = useState<'pending' | 'my'>('pending');

  useEffect(() => {
    loadWorkerInfo();
    loadOrders();
    
    // 设置定时刷新
    const interval = setInterval(loadOrders, 10000); // 每10秒刷新
    return () => clearInterval(interval);
  }, []);

  const loadWorkerInfo = async () => {
    try {
      const { data, error } = await supabase
        .from('escort_workers')
        .select('*')
        .eq('user_id', session.user.id)
        .maybeSingle();

      if (error) throw error;
      setWorker(data);
    } catch (error) {
      console.error('加载陪诊师信息失败:', error);
    }
  };

  const loadOrders = async () => {
    try {
      // 加载待接单的订单
      const { data: pending, error: pendingError } = await supabase
        .from('service_orders')
        .select('*')
        .in('order_status', ['pending', 'assigned'])
        .order('scheduled_time', { ascending: true });

      if (pendingError) throw pendingError;
      setPendingOrders(pending || []);

      // 加载我的订单（如果已经是陪诊师）
      if (worker) {
        const { data: my, error: myError } = await supabase
          .from('service_orders')
          .select('*')
          .eq('worker_id', worker.id)
          .in('order_status', ['accepted', 'in_progress'])
          .order('scheduled_time', { ascending: true });

        if (myError) throw myError;
        setMyOrders(my || []);
      }
    } catch (error) {
      console.error('加载订单失败:', error);
    }
  };

  const handleAcceptOrder = async (orderId: string) => {
    if (!worker) {
      alert('请先注册成为陪诊师');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('order-dispatch', {
        body: {
          order_id: orderId,
          worker_id: worker.id,
          action: 'accept'
        }
      });

      if (error) throw error;
      alert('接单成功！');
      loadOrders();
    } catch (error: any) {
      console.error('接单失败:', error);
      alert('接单失败：' + (error.message || '请稍后重试'));
    } finally {
      setLoading(false);
    }
  };

  const handleStartService = async (orderId: string) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('order-dispatch', {
        body: {
          order_id: orderId,
          action: 'start'
        }
      });

      if (error) throw error;
      
      // 更新位置
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (position) => {
          await supabase.functions.invoke('location-tracking', {
            body: {
              action: 'update',
              order_id: orderId,
              worker_id: worker?.id,
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              accuracy: position.coords.accuracy,
              status: 'started'
            }
          });
        });
      }

      alert('服务已开始！');
      loadOrders();
    } catch (error: any) {
      console.error('开始服务失败:', error);
      alert('开始服务失败：' + (error.message || '请稍后重试'));
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteService = async (orderId: string) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('order-dispatch', {
        body: {
          order_id: orderId,
          action: 'complete'
        }
      });

      if (error) throw error;
      alert('服务已完成！');
      loadOrders();
      loadWorkerInfo(); // 重新加载陪诊师信息更新完成订单数
    } catch (error: any) {
      console.error('完成服务失败:', error);
      alert('完成服务失败：' + (error.message || '请稍后重试'));
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      assigned: 'bg-blue-100 text-blue-800',
      accepted: 'bg-purple-100 text-purple-800',
      in_progress: 'bg-green-100 text-green-800',
      completed: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待分配',
      assigned: '已分配',
      accepted: '已接单',
      in_progress: '进行中',
      completed: '已完成'
    };
    return texts[status] || status;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-teal-50 to-cyan-50">
      <div className="container mx-auto px-4 py-8">
        {/* 头部 - 陪诊师信息 */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-8">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold text-gray-800">陪诊师工作台</h1>
            <button
              onClick={() => navigate('/')}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              返回首页
            </button>
          </div>

          {worker ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-4 text-white">
                <div className="text-sm opacity-90 mb-1">姓名</div>
                <div className="text-2xl font-bold">{worker.name}</div>
              </div>
              <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-4 text-white">
                <div className="text-sm opacity-90 mb-1">评分</div>
                <div className="text-2xl font-bold">{worker.rating.toFixed(1)} 分</div>
              </div>
              <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-4 text-white">
                <div className="text-sm opacity-90 mb-1">完成订单</div>
                <div className="text-2xl font-bold">{worker.completed_orders}</div>
              </div>
              <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-4 text-white">
                <div className="text-sm opacity-90 mb-1">总订单数</div>
                <div className="text-2xl font-bold">{worker.total_orders}</div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">您还不是陪诊师，请联系管理员注册</p>
            </div>
          )}
        </div>

        {/* 订单标签页 */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="border-b border-gray-200">
            <div className="flex">
              <button
                onClick={() => setSelectedTab('pending')}
                className={`flex-1 px-6 py-4 text-center font-medium transition-colors ${
                  selectedTab === 'pending'
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                待接订单 ({pendingOrders.length})
              </button>
              <button
                onClick={() => setSelectedTab('my')}
                className={`flex-1 px-6 py-4 text-center font-medium transition-colors ${
                  selectedTab === 'my'
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                我的订单 ({myOrders.length})
              </button>
            </div>
          </div>

          <div className="p-6">
            {/* 待接订单列表 */}
            {selectedTab === 'pending' && (
              <div className="space-y-4">
                {pendingOrders.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <p>暂无待接订单</p>
                  </div>
                ) : (
                  pendingOrders.map((order) => (
                    <div
                      key={order.id}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-gray-800">订单号：{order.order_number}</h3>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(order.order_status)}`}>
                              {getStatusText(order.order_status)}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                              <span className="font-medium">预约时间：</span>
                              {new Date(order.scheduled_time).toLocaleString('zh-CN')}
                            </div>
                            <div>
                              <span className="font-medium">预计时长：</span>
                              {order.estimated_duration}分钟
                            </div>
                            <div>
                              <span className="font-medium">服务费用：</span>
                              <span className="text-indigo-600 font-semibold">¥{order.total_fee}</span>
                            </div>
                            <div>
                              <span className="font-medium">距离：</span>
                              {order.distance}公里
                            </div>
                          </div>
                          <div className="mt-2 text-sm text-gray-500">
                            <span className="font-medium">目的地：</span>
                            {order.destination_location}
                          </div>
                        </div>
                        {worker && (
                          <button
                            onClick={() => handleAcceptOrder(order.id)}
                            disabled={loading}
                            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                          >
                            接单
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* 我的订单列表 */}
            {selectedTab === 'my' && (
              <div className="space-y-4">
                {myOrders.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <p>暂无进行中的订单</p>
                  </div>
                ) : (
                  myOrders.map((order) => (
                    <div
                      key={order.id}
                      className="border border-indigo-200 bg-indigo-50 rounded-lg p-4"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-gray-800">订单号：{order.order_number}</h3>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(order.order_status)}`}>
                              {getStatusText(order.order_status)}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                              <span className="font-medium">预约时间：</span>
                              {new Date(order.scheduled_time).toLocaleString('zh-CN')}
                            </div>
                            <div>
                              <span className="font-medium">服务费用：</span>
                              <span className="text-indigo-600 font-semibold">¥{order.total_fee}</span>
                            </div>
                          </div>
                          <div className="mt-2 text-sm text-gray-500">
                            <span className="font-medium">目的地：</span>
                            {order.destination_location}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          {order.order_status === 'accepted' && (
                            <button
                              onClick={() => handleStartService(order.id)}
                              disabled={loading}
                              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                            >
                              开始服务
                            </button>
                          )}
                          {order.order_status === 'in_progress' && (
                            <button
                              onClick={() => handleCompleteService(order.id)}
                              disabled={loading}
                              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                            >
                              完成服务
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
