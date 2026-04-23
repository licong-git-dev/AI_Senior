import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import {
  Bell,
  AlertTriangle,
  Heart,
  Clock,
  CheckCheck,
  ChevronLeft,
  Activity,
  Home,
  PhoneCall,
} from 'lucide-react';
import { getMySubscription, getNotifications, markNotificationRead, markNotificationHandled } from '../lib/api';
import type { MySubscription, Notification } from '../lib/api';

interface NotificationsPageProps {
  familyId?: string;
  onBack?: () => void;
  onNavigate?: (page: 'trends' | 'child' | 'chat' | 'landing') => void;
  onCallParent?: () => void;
}

export default function NotificationsPage({ familyId, onBack, onNavigate, onCallParent }: NotificationsPageProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'unread' | 'high_risk'>('all');
  const [unreadCount, setUnreadCount] = useState(0);
  const [subscription, setSubscription] = useState<MySubscription | null>(null);

  // 获取通知列表
  const fetchNotifications = async () => {
    if (!familyId) {
      setNotifications([]);
      setUnreadCount(0);
      setError('暂未获取到家属账号信息，请重新登录后再试。');
      setLoading(false);
      return;
    }

    try {
      setError(null);
      const [data, subscriptionResult] = await Promise.all([
        getNotifications(familyId),
        getMySubscription().catch(() => null),
      ]);
      setNotifications(data.notifications);
      setUnreadCount(data.unread_count);
      setSubscription(subscriptionResult);
    } catch (fetchError) {
      console.error('获取通知失败:', fetchError);
      setNotifications([]);
      setUnreadCount(0);
      setError('暂时无法获取通知，请稍后重试。');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [familyId]);

  // 标记已读
  const handleMarkRead = async (notificationId: string) => {
    if (!familyId) return;
    try {
      await markNotificationRead(notificationId, familyId);
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('标记已读失败:', error);
      // 本地更新
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    }
  };

  // 标记已处理
  const handleMarkHandled = async (notificationId: string) => {
    if (!familyId) return;
    try {
      await markNotificationHandled(notificationId, familyId);
    } catch {
      // 忽略错误，本地更新仍然执行
    }
    setNotifications(prev =>
      prev.map(n =>
        n.id === notificationId ? { ...n, is_read: true, is_handled: true } : n
      )
    );
  };

  // 过滤通知
  const filteredNotifications = notifications.filter(n => {
    if (filter === 'unread') return !n.is_read;
    if (filter === 'high_risk') return n.risk_score >= 7;
    return true;
  });

  // 获取分类图标和颜色
  const getCategoryStyle = (category: string, riskScore: number) => {
    if (riskScore >= 7) {
      return { icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-100' };
    }
    switch (category) {
      case 'health':
        return { icon: Heart, color: 'text-pink-500', bg: 'bg-pink-100' };
      case 'reminder':
        return { icon: Clock, color: 'text-blue-500', bg: 'bg-blue-100' };
      case 'emergency':
        return { icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-100' };
      default:
        return { icon: Bell, color: 'text-gray-500', bg: 'bg-gray-100' };
    }
  };

  const getActionButtons = (notification: Notification) => {
    const actions: Array<{
      key: string;
      label: string;
      icon: typeof Activity;
      onClick: () => void;
      className: string;
    }> = [];

    if (notification.category === 'emergency' || notification.risk_score >= 7) {
      actions.push({
        key: 'trends',
        label: '查看趋势',
        icon: Activity,
        onClick: () => onNavigate?.('trends'),
        className: 'bg-red-50 text-red-700 hover:bg-red-100',
      });
      actions.push({
        key: 'call',
        label: '联系老人',
        icon: PhoneCall,
        onClick: () => onCallParent?.(),
        className: 'bg-orange-50 text-orange-700 hover:bg-orange-100',
      });
    }

    if (notification.category === 'health') {
      actions.push({
        key: 'trends',
        label: '健康趋势',
        icon: Activity,
        onClick: () => onNavigate?.('trends'),
        className: 'bg-pink-50 text-pink-700 hover:bg-pink-100',
      });
    }

    if (notification.category === 'reminder') {
      actions.push({
        key: 'dashboard',
        label: '回到看板',
        icon: Home,
        onClick: () => onNavigate?.('child'),
        className: 'bg-blue-50 text-blue-700 hover:bg-blue-100',
      });
    }

    if (notification.is_read && !notification.is_handled) {
      actions.push({
        key: 'handled',
        label: '标记已处理',
        icon: CheckCheck,
        onClick: () => handleMarkHandled(notification.id),
        className: 'bg-green-50 text-green-700 hover:bg-green-100',
      });
    }

    return actions;
  };

  // 格式化时间
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return format(date, 'MM-dd HH:mm');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">加载通知中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="max-w-sm rounded-3xl bg-white p-8 text-center shadow-sm">
          <AlertTriangle className="mx-auto mb-4 h-12 w-12 text-amber-500" />
          <h2 className="mb-2 text-xl font-bold text-gray-800">暂时无法查看通知</h2>
          <p className="text-sm leading-6 text-gray-500">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-6">
      {/* 顶部导航 */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 pt-12 pb-6 rounded-b-3xl">
        <div className="flex items-center gap-4 mb-4">
          {onBack && (
            <button
              onClick={onBack}
              className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
          )}
          <div className="flex-1">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Bell className="w-7 h-7" />
              通知中心
            </h1>
            <p className="text-indigo-200 text-sm">
              {unreadCount > 0 ? `${unreadCount}条未读消息` : '暂无未读消息'}
            </p>
          </div>
        </div>

        {/* 过滤器 */}
        <div className="flex gap-2">
          {[
            { key: 'all', label: '全部' },
            { key: 'unread', label: '未读' },
            { key: 'high_risk', label: '高风险' }
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => setFilter(item.key as typeof filter)}
              className={`px-4 py-2 rounded-full text-sm transition-all ${
                filter === item.key
                  ? 'bg-white text-indigo-600 font-medium'
                  : 'bg-white/20 text-white'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {!subscription?.has_subscription && (
        <div className="px-4 mt-6">
          <div className="rounded-2xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-4 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-amber-700">升级到安心版</p>
                <p className="mt-1 text-sm leading-6 text-gray-600">
                  解锁完整健康趋势、更多家庭成员关注与更稳的守护提醒体验。
                </p>
              </div>
              <button
                onClick={() => onNavigate?.('landing')}
                className="rounded-full bg-amber-500 px-4 py-2 text-sm font-bold text-white hover:bg-amber-600"
              >
                去升级
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 通知列表 */}
      <div className="px-4 mt-6 space-y-3">
        {filteredNotifications.length === 0 ? (
          <div className="text-center py-12">
            <Bell className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">暂无通知</p>
          </div>
        ) : (
          filteredNotifications.map((notification) => {
            const style = getCategoryStyle(notification.category, notification.risk_score);
            const Icon = style.icon;

            return (
              <div
                key={notification.id}
                className={`bg-white rounded-2xl p-4 shadow-sm transition-all ${
                  !notification.is_read ? 'border-l-4 border-indigo-500' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-10 h-10 rounded-full ${style.bg} flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-5 h-5 ${style.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className={`font-medium ${!notification.is_read ? 'text-gray-900' : 'text-gray-600'}`}>
                        {notification.title}
                      </h3>
                      {notification.risk_score >= 7 && (
                        <span className="px-2 py-0.5 bg-red-100 text-red-600 text-xs rounded-full">
                          风险{notification.risk_score}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mb-2">{notification.content}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400">
                        {formatTime(notification.created_at)}
                      </span>
                      <div className="flex items-center gap-2">
                        {notification.is_handled ? (
                          <span className="text-xs text-green-600 flex items-center gap-1">
                            <CheckCheck className="w-4 h-4" />
                            已处理
                          </span>
                        ) : (
                          <>
                            {!notification.is_read && (
                              <button
                                onClick={() => handleMarkRead(notification.id)}
                                className="text-xs text-indigo-600 hover:text-indigo-700"
                              >
                                标记已读
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                    {getActionButtons(notification).length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {getActionButtons(notification).map((action) => {
                          const ActionIcon = action.icon;
                          return (
                            <button
                              key={action.key}
                              onClick={action.onClick}
                              className={`inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium transition ${action.className}`}
                            >
                              <ActionIcon className="h-3.5 w-3.5" />
                              {action.label}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 统计卡片 */}
      <div className="px-4 mt-6">
        <h2 className="text-lg font-bold text-gray-800 mb-3">通知统计</h2>
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white rounded-2xl p-4 shadow-sm text-center">
            <p className="text-2xl font-bold text-indigo-600">{notifications.length}</p>
            <p className="text-xs text-gray-500">总通知</p>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow-sm text-center">
            <p className="text-2xl font-bold text-orange-600">{unreadCount}</p>
            <p className="text-xs text-gray-500">未读</p>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow-sm text-center">
            <p className="text-2xl font-bold text-red-600">
              {notifications.filter(n => n.risk_score >= 7).length}
            </p>
            <p className="text-xs text-gray-500">高风险</p>
          </div>
        </div>
      </div>
    </div>
  );
}
