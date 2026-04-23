import { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import { useNavigate } from 'react-router-dom';

interface Appointment {
  id: string;
  elderly_name: string;
  hospital_name: string;
  hospital_address: string;
  department: string;
  appointment_time: string;
  service_type: string;
  urgency_level: number;
  status: string;
}

interface ServiceOrder {
  id: string;
  order_number: string;
  order_status: string;
  scheduled_time: string;
  total_fee: number;
  payment_status: string;
  worker_id: string | null;
}

interface FeeBreakdown {
  baseFee: number;
  distanceFee: number;
  durationFee: number;
  urgencyFee: number;
  total: number;
}

export default function AppointmentBookingPage({ session }: { session: any }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    elderly_name: '',
    elderly_phone: '',
    appointment_time: '',
    hospital_name: '',
    hospital_address: '',
    department: '',
    doctor_name: '',
    service_type: 'standard',
    urgency_level: 1,
    special_needs: ''
  });
  const [paymentMethod, setPaymentMethod] = useState<'wechat' | 'alipay' | 'insurance'>('wechat');
  const [feeBreakdown, setFeeBreakdown] = useState<FeeBreakdown>({
    baseFee: 0,
    distanceFee: 0,
    durationFee: 0,
    urgencyFee: 0,
    total: 0
  });
  const [showPayment, setShowPayment] = useState(false);
  const [currentOrderId, setCurrentOrderId] = useState<string | null>(null);

  useEffect(() => {
    loadAppointments();
  }, []);

  const loadAppointments = async () => {
    try {
      const { data, error } = await supabase
        .from('appointments')
        .select('*')
        .order('appointment_time', { ascending: false })
        .limit(20);

      if (error) throw error;
      setAppointments(data || []);
    } catch (error) {
      console.error('加载预约记录失败:', error);
    }
  };

  // 计算费用
  const calculateFee = () => {
    let baseFee = 50; // 基础费用
    let distanceFee = 0; // 距离费用（简化计算）
    let durationFee = 30; // 时长费用
    let urgencyFee = 0;

    // 根据服务类型调整费用
    if (formData.service_type === 'specialist') {
      baseFee = 100;
      durationFee = 50;
    } else if (formData.service_type === 'urgent') {
      baseFee = 80;
      urgencyFee = 50;
      durationFee = 40;
    }

    // 简化的距离费用计算（实际应该根据地址计算）
    distanceFee = 20;

    const total = baseFee + distanceFee + durationFee + urgencyFee;

    setFeeBreakdown({
      baseFee,
      distanceFee,
      durationFee,
      urgencyFee,
      total
    });
  };

  // 处理支付
  const handlePayment = async (orderId: string) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('payment-processing', {
        body: {
          order_id: orderId,
          amount: feeBreakdown.total,
          payment_method: paymentMethod,
          payer_id: session.user.id
        }
      });

      if (error) throw error;

      alert('支付成功！');
      setShowPayment(false);
      loadAppointments();
    } catch (error: any) {
      console.error('支付失败:', error);
      alert('支付失败：' + (error.message || '请稍后重试'));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const { data, error } = await supabase.functions.invoke('appointment-booking', {
        body: {
          elderly_id: session.user.id,
          elderly_name: formData.elderly_name,
          elderly_phone: formData.elderly_phone,
          appointment_time: new Date(formData.appointment_time).toISOString(),
          hospital_name: formData.hospital_name,
          hospital_address: formData.hospital_address,
          department: formData.department,
          doctor_name: formData.doctor_name,
          service_type: formData.service_type,
          urgency_level: formData.urgency_level,
          special_needs: formData.special_needs
        }
      });

      if (error) throw error;

      const orderData = data?.data;
      alert(orderData?.message || '预约成功！');
      
      // 显示支付界面
      if (orderData?.order_id) {
        setCurrentOrderId(orderData.order_id);
        calculateFee();
        setShowPayment(true);
      }
      
      setShowForm(false);
      loadAppointments();
      
      // 重置表单
      setFormData({
        elderly_name: '',
        elderly_phone: '',
        appointment_time: '',
        hospital_name: '',
        hospital_address: '',
        department: '',
        doctor_name: '',
        service_type: 'standard',
        urgency_level: 1,
        special_needs: ''
      });
    } catch (error: any) {
      console.error('预约失败:', error);
      alert('预约失败：' + (error.message || '请稍后重试'));
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待确认',
      confirmed: '已确认',
      completed: '已完成',
      cancelled: '已取消'
    };
    return texts[status] || status;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* 头部 */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">上门陪诊服务</h1>
            <p className="text-gray-600 mt-2">专业陪诊师，让就医更安心</p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={() => navigate('/')}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              返回首页
            </button>
            <button
              onClick={() => setShowForm(true)}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-lg"
            >
              预约陪诊
            </button>
          </div>
        </div>

        {/* 预约表单弹窗 */}
        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-800">预约陪诊服务</h2>
                  <button
                    onClick={() => setShowForm(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        老人姓名 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.elderly_name}
                        onChange={(e) => setFormData({ ...formData, elderly_name: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        placeholder="请输入老人姓名"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        联系电话 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="tel"
                        required
                        value={formData.elderly_phone}
                        onChange={(e) => setFormData({ ...formData, elderly_phone: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        placeholder="请输入联系电话"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        预约时间 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="datetime-local"
                        required
                        value={formData.appointment_time}
                        onChange={(e) => setFormData({ ...formData, appointment_time: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        医院名称 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.hospital_name}
                        onChange={(e) => setFormData({ ...formData, hospital_name: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        placeholder="例如：武汉协和医院"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        科室 <span className="text-red-500">*</span>
                      </label>
                      <select
                        required
                        value={formData.department}
                        onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      >
                        <option value="">请选择科室</option>
                        <option value="内科">内科</option>
                        <option value="外科">外科</option>
                        <option value="骨科">骨科</option>
                        <option value="心血管科">心血管科</option>
                        <option value="神经内科">神经内科</option>
                        <option value="呼吸科">呼吸科</option>
                        <option value="消化科">消化科</option>
                      </select>
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        医院地址 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.hospital_address}
                        onChange={(e) => setFormData({ ...formData, hospital_address: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        placeholder="请输入医院详细地址"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">医生姓名</label>
                      <input
                        type="text"
                        value={formData.doctor_name}
                        onChange={(e) => setFormData({ ...formData, doctor_name: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        placeholder="如有指定医生可填写"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        服务类型 <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={formData.service_type}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          service_type: e.target.value,
                          urgency_level: e.target.value === 'urgent' ? 3 : (e.target.value === 'specialist' ? 2 : 1)
                        })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      >
                        <option value="standard">标准陪诊</option>
                        <option value="specialist">专家陪诊</option>
                        <option value="urgent">紧急陪诊</option>
                      </select>
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">特殊需求</label>
                      <textarea
                        value={formData.special_needs}
                        onChange={(e) => setFormData({ ...formData, special_needs: e.target.value })}
                        rows={3}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        placeholder="如需要轮椅、特殊照护等，请在此说明"
                      />
                    </div>
                  </div>

                  {/* 费用预估 */}
                  <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-4 border border-indigo-200">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">费用预估</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">基础服务费：</span>
                        <span className="font-medium">¥{formData.service_type === 'specialist' ? '100' : formData.service_type === 'urgent' ? '80' : '50'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">距离费用：</span>
                        <span className="font-medium">¥20（预估）</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">时长费用：</span>
                        <span className="font-medium">¥{formData.service_type === 'specialist' ? '50' : formData.service_type === 'urgent' ? '40' : '30'}</span>
                      </div>
                      {formData.service_type === 'urgent' && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">加急费用：</span>
                          <span className="font-medium text-red-600">¥50</span>
                        </div>
                      )}
                      <div className="border-t border-indigo-200 pt-2 mt-2 flex justify-between">
                        <span className="font-semibold text-gray-800">预估总费用：</span>
                        <span className="text-xl font-bold text-indigo-600">
                          ¥{formData.service_type === 'specialist' ? '170' : formData.service_type === 'urgent' ? '190' : '100'}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">*实际费用以订单确认后为准</p>
                  </div>

                  <div className="flex gap-4 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowForm(false)}
                      className="flex-1 px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      取消
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? '提交中...' : '确认预约'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* 支付弹窗 */}
        {showPayment && currentOrderId && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl max-w-md w-full">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-800">订单支付</h2>
                  <button
                    onClick={() => setShowPayment(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* 费用详情 */}
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <h3 className="font-semibold text-gray-800 mb-3">费用明细</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">基础服务费</span>
                      <span>¥{feeBreakdown.baseFee}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">距离费用</span>
                      <span>¥{feeBreakdown.distanceFee}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">时长费用</span>
                      <span>¥{feeBreakdown.durationFee}</span>
                    </div>
                    {feeBreakdown.urgencyFee > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">加急费用</span>
                        <span className="text-red-600">¥{feeBreakdown.urgencyFee}</span>
                      </div>
                    )}
                    <div className="border-t border-gray-300 pt-2 mt-2 flex justify-between">
                      <span className="font-semibold text-gray-800">应付金额</span>
                      <span className="text-xl font-bold text-indigo-600">¥{feeBreakdown.total}</span>
                    </div>
                  </div>
                </div>

                {/* 支付方式选择 */}
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-800 mb-3">支付方式</h3>
                  <div className="space-y-2">
                    <button
                      onClick={() => setPaymentMethod('wechat')}
                      className={`w-full flex items-center gap-3 p-4 border-2 rounded-lg transition-all ${
                        paymentMethod === 'wechat'
                          ? 'border-green-500 bg-green-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center text-white font-bold">
                        微
                      </div>
                      <span className="font-medium">微信支付</span>
                    </button>
                    <button
                      onClick={() => setPaymentMethod('alipay')}
                      className={`w-full flex items-center gap-3 p-4 border-2 rounded-lg transition-all ${
                        paymentMethod === 'alipay'
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center text-white font-bold">
                        支
                      </div>
                      <span className="font-medium">支付宝</span>
                    </button>
                    <button
                      onClick={() => setPaymentMethod('insurance')}
                      className={`w-full flex items-center gap-3 p-4 border-2 rounded-lg transition-all ${
                        paymentMethod === 'insurance'
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center text-white font-bold">
                        医
                      </div>
                      <span className="font-medium">医保支付</span>
                    </button>
                  </div>
                </div>

                {/* 支付按钮 */}
                <div className="flex gap-4">
                  <button
                    onClick={() => setShowPayment(false)}
                    className="flex-1 px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    稍后支付
                  </button>
                  <button
                    onClick={() => handlePayment(currentOrderId)}
                    disabled={loading}
                    className="flex-1 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? '支付中...' : '确认支付'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 预约记录列表 */}
        <div className="bg-white rounded-2xl shadow-xl p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-6">我的预约记录</h2>
          
          {appointments.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-gray-500">暂无预约记录</p>
              <button
                onClick={() => setShowForm(true)}
                className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                立即预约
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {appointments.map((appointment) => (
                <div
                  key={appointment.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-800">{appointment.hospital_name}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(appointment.status)}`}>
                          {getStatusText(appointment.status)}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                        <div>
                          <span className="font-medium">老人：</span>
                          {appointment.elderly_name}
                        </div>
                        <div>
                          <span className="font-medium">科室：</span>
                          {appointment.department}
                        </div>
                        <div>
                          <span className="font-medium">预约时间：</span>
                          {new Date(appointment.appointment_time).toLocaleString('zh-CN')}
                        </div>
                        <div>
                          <span className="font-medium">服务类型：</span>
                          {appointment.service_type === 'standard' ? '标准陪诊' : 
                           appointment.service_type === 'specialist' ? '专家陪诊' : '紧急陪诊'}
                        </div>
                      </div>
                      <div className="mt-2 text-sm text-gray-500">
                        <span className="font-medium">地址：</span>
                        {appointment.hospital_address}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
