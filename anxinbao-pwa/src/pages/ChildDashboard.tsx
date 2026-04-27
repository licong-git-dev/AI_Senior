import { useState, useEffect, useMemo } from 'react';
import { format } from 'date-fns';
import {
  Heart,
  AlertTriangle,
  TrendingUp,
  ChevronRight,
  Activity,
  Utensils,
  Moon,
  Video,
  Bell,
  Calendar,
  Phone,
  Share2,
  Copy,
  CheckCircle2,
  Link2,
  MessageCircle,
  Bookmark,
} from 'lucide-react';
import VoiceInbox from '../components/VoiceInbox';
import IntentCard from '../components/IntentCard';
import {
  getHealthSummary,
  getDashboardSummary,
  getDailyReportHistory,
  getAnxinScoreTrend,
  getMyFamilyGroups,
  createFamilyGroup,
  createBindingRequest,
  getStoredUser,
  getFamilyGroupId,
  buildFamilyInviteLink,
  copyText,
  shareContent,
  getMySubscription,
} from '../lib/api';
import type { DashboardSummary, HealthSummary, DailyReportHistoryItem, AnxinScoreTrendPoint, MySubscription } from '../lib/api';

interface ChildDashboardProps {
  parentUserId?: string;
  parentName?: string;
  onStartVideoCall?: (targetId: string, targetName: string) => void;
  onNavigate?: (page: 'trends' | 'notifications' | 'chat' | 'landing') => void;
}

export default function ChildDashboard({
  parentUserId,
  parentName = '妈妈',
  onStartVideoCall,
  onNavigate
}: ChildDashboardProps) {
  const [healthData, setHealthData] = useState<HealthSummary | null>(null);
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [reportHistory, setReportHistory] = useState<DailyReportHistoryItem[]>([]);
  const [anxinTrend, setAnxinTrend] = useState<AnxinScoreTrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'health' | 'chat' | 'trends' | 'notifications'>('health');
  const [shareStatus, setShareStatus] = useState<string | null>(null);
  const [shareLoading, setShareLoading] = useState(false);
  const [subscription, setSubscription] = useState<MySubscription | null>(null);

  // 更新时间（已移除，改用 dailyReport 中的真实时间）

  // 获取健康数据和日报
  useEffect(() => {
    if (!parentUserId) {
      setLoading(false);
      setError('暂未获取到家人信息，请先完成绑定。');
      return;
    }

    const fetchData = async () => {
      try {
        setError(null);

        const [healthResult, summaryResult] = await Promise.all([
          getHealthSummary(parentUserId),
          getDashboardSummary(parentUserId),
        ]);

        setHealthData(healthResult);
        setDashboardSummary(summaryResult);

        const [historyResult, trendResult, subscriptionResult] = await Promise.allSettled([
          getDailyReportHistory(parentUserId, 7),
          getAnxinScoreTrend(parentUserId, 7),
          getMySubscription(),
        ]);

        if (historyResult.status === 'fulfilled') {
          setReportHistory(historyResult.value.reports);
        } else {
          console.error('获取历史日报失败:', historyResult.reason);
          setReportHistory([]);
        }

        if (trendResult.status === 'fulfilled') {
          setAnxinTrend(trendResult.value.trend);
        } else {
          console.error('获取安心趋势失败:', trendResult.reason);
          setAnxinTrend([]);
        }

        if (subscriptionResult.status === 'fulfilled') {
          setSubscription(subscriptionResult.value);
        } else {
          setSubscription(null);
        }
      } catch (fetchError) {
        console.error('获取家人核心数据失败:', fetchError);
        setHealthData(null);
        setDashboardSummary(null);
        setReportHistory([]);
        setAnxinTrend([]);
        setError('暂时无法获取家人实时数据，请稍后重试。');
      } finally {
        setLoading(false);
      }
    };
    fetchData();

    // 每5分钟刷新
    const interval = setInterval(fetchData, 300000);
    return () => clearInterval(interval);
  }, [parentUserId]);

  // 关怀建议 → 一键行动入口
  // 设计目标：把"信息看板"改成"行动入口"。每条 tip 根据关键词推断
  // 最有用的下一步动作（视频/发祝福/设提醒/查趋势/记下），让子女
  // 看到 → 行动 → 焦虑被释放，而不是看完即关。
  const inferTipAction = (tip: string): {
    label: string;
    icon: typeof Phone;
    color: string;
    onClick: () => void;
  } => {
    if (/视频|通话|连线|见面|聊聊/.test(tip)) {
      return {
        label: '立即视频',
        icon: Video,
        color: 'bg-indigo-500 hover:bg-indigo-600',
        onClick: () => parentUserId && onStartVideoCall?.(parentUserId, parentName),
      };
    }
    if (/电话|打个/.test(tip)) {
      return {
        label: '马上去电',
        icon: Phone,
        color: 'bg-emerald-500 hover:bg-emerald-600',
        onClick: () => parentUserId && onStartVideoCall?.(parentUserId, parentName),
      };
    }
    if (/提醒|服药|吃药|药|按时/.test(tip)) {
      return {
        label: '设个提醒',
        icon: Bell,
        color: 'bg-amber-500 hover:bg-amber-600',
        onClick: () => onNavigate?.('notifications'),
      };
    }
    if (/祝福|问候|关心|陪|聊|说说|告诉/.test(tip)) {
      return {
        label: '发条祝福',
        icon: MessageCircle,
        color: 'bg-pink-500 hover:bg-pink-600',
        onClick: () => onNavigate?.('chat'),
      };
    }
    if (/血压|心率|血糖|健康|趋势|检查|睡眠|运动/.test(tip)) {
      return {
        label: '查健康趋势',
        icon: TrendingUp,
        color: 'bg-green-500 hover:bg-green-600',
        onClick: () => onNavigate?.('trends'),
      };
    }
    // 默认：可记下，避免有用的建议被遗忘
    return {
      label: '记下',
      icon: Bookmark,
      color: 'bg-gray-500 hover:bg-gray-600',
      onClick: () => {
        try {
          const noted = JSON.parse(localStorage.getItem('noted_tips') || '[]') as Array<{ tip: string; ts: number }>;
          noted.unshift({ tip, ts: Date.now() });
          localStorage.setItem('noted_tips', JSON.stringify(noted.slice(0, 50)));
        } catch (_) { /* 容忍存储失败 */ }
        if (typeof window !== 'undefined') {
          window.alert('已记下此建议（最近 50 条）');
        }
      },
    };
  };

  // 风险等级配置
  const riskConfig = {
    low: { color: 'bg-green-500', text: '健康良好', icon: '💚' },
    medium: { color: 'bg-yellow-500', text: '需要关注', icon: '💛' },
    high: { color: 'bg-red-500', text: '建议就医', icon: '❤️' },
  };

  const risk = healthData ? riskConfig[healthData.risk_level] : riskConfig.low;
  const dailyReport = dashboardSummary?.report ?? null;

  // 从日报派生聊天记录
  const recentChats = dailyReport ? [
    ...(dailyReport.conversation.key_quotes.map((quote, i) => ({
      time: i === 0 && dailyReport.conversation.last_chat_time
        ? `今天 ${dailyReport.conversation.last_chat_time}`
        : i === 1 && dailyReport.conversation.first_chat_time
        ? `今天 ${dailyReport.conversation.first_chat_time}`
        : '今天',
      content: quote,
      mood: dailyReport.emotion.emotion_score >= 7 ? 'happy' :
            dailyReport.emotion.emotion_score <= 4 ? 'sad' : 'normal',
    }))),
  ] : [];

  // 快捷按钮配置（带导航动作）
  const shortcuts = [
    { icon: Bell, label: '安心提醒', color: 'text-blue-500', action: () => onNavigate?.('notifications') },
    { icon: Activity, label: '健康趋势', color: 'text-green-500', action: () => onNavigate?.('trends') },
    { icon: Utensils, label: '关怀建议', color: 'text-orange-500', action: () => onNavigate?.('notifications') },
    { icon: Moon, label: '睡眠情况', color: 'text-purple-500', action: () => onNavigate?.('trends') },
  ];

  const trendMaxScore = Math.max(...anxinTrend.map((item) => item.score), 10);
  const abnormalReports = reportHistory.filter(
    (item) => item.anxin_score <= 6 || item.health_status !== '正常'
  );

  const formatReportDate = (dateText: string) => {
    try {
      return format(new Date(dateText), 'M月d日');
    } catch {
      return dateText;
    }
  };

  const shareText = useMemo(() => {
    if (!dailyReport) {
      return '';
    }

    const summaryLines = [
      `${parentName}的今日日报：安心指数 ${dailyReport.anxin_score} 分（${dailyReport.anxin_level}）`,
      dailyReport.one_line_summary,
      dailyReport.tips_for_children[0] ? `今日建议：${dailyReport.tips_for_children[0]}` : '',
    ].filter(Boolean);

    return summaryLines.join('\n');
  }, [dailyReport, parentName]);

  const handleShareDailyReport = async () => {
    if (!dailyReport || shareLoading) {
      return;
    }

    setShareLoading(true);
    setShareStatus(null);

    try {
      let groupId: string;
      const { groups } = await getMyFamilyGroups();

      if (groups.length > 0) {
        groupId = getFamilyGroupId(groups[0]);
      } else {
        const user = getStoredUser();
        const elderName = dailyReport.user_name || user?.name || parentName;
        const createdGroup = await createFamilyGroup(`${elderName}的家庭`, elderName);
        groupId = getFamilyGroupId(createdGroup.group);
      }

      const { invite_code: inviteCode } = await createBindingRequest(groupId);
      const inviteLink = buildFamilyInviteLink(inviteCode);
      const message = `${shareText}\n\n邀请家人一起关注：${inviteLink}\n邀请码：${inviteCode}`;
      const shared = await shareContent({
        title: `${parentName}的安心日报`,
        text: message,
        url: inviteLink,
      });

      if (shared) {
        setShareStatus('已调起系统分享，可直接发给家人。');
        return;
      }

      await copyText(message);
      setShareStatus('已复制日报和邀请码，直接发给家人即可。');
    } catch (shareError) {
      setShareStatus(shareError instanceof Error ? shareError.message : '分享失败，请稍后重试');
    } finally {
      setShareLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="max-w-sm rounded-3xl bg-white p-8 text-center shadow-sm">
          <AlertTriangle className="mx-auto mb-4 h-12 w-12 text-amber-500" />
          <h2 className="mb-2 text-xl font-bold text-gray-800">暂时无法查看家人状态</h2>
          <p className="text-sm leading-6 text-gray-500">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* 顶部头像和状态 */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 pt-12 pb-8 rounded-b-3xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center text-3xl">
              👵
            </div>
            <div>
              <h1 className="text-2xl font-bold">{parentName}</h1>
              <p className="text-indigo-200 text-sm">
                最后活跃: {
                  dailyReport?.conversation?.last_chat_time
                    ? `今天 ${dailyReport.conversation.last_chat_time}`
                    : dailyReport
                    ? `今天 ${format(new Date(dailyReport.generated_at), 'HH:mm')}`
                    : '暂无记录'
                }
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              if (!parentUserId) return;
              // 进入前预提醒：未配置 TURN 时通话在国内 70% NAT 场景会失败
              // （详见 anxinbao-server/docs/VIDEO_CALL_SETUP.md）
              if (!import.meta.env.VITE_TURN_URL) {
                const ok = window.confirm(
                  '提醒：当前服务器未配置 TURN 中继。\n\n'
                  + '在部分家庭网络下视频可能连不上。\n'
                  + '建议先用电话联系，或联系管理员配置 TURN。\n\n'
                  + '仍要尝试视频通话吗？'
                );
                if (!ok) return;
              }
              onStartVideoCall?.(parentUserId, parentName);
            }}
            className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center hover:bg-white/30 transition-colors"
          >
            <Video className="w-6 h-6" />
          </button>
        </div>

        {/* 健康状态卡片 */}
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{risk.icon}</span>
              <div>
                <p className="font-bold text-lg">{risk.text}</p>
                <p className="text-indigo-200 text-sm">今日健康评估</p>
              </div>
            </div>
            <div className={`px-4 py-2 rounded-full ${risk.color}`}>
              <span className="text-white font-medium">
                {healthData?.risk_level === 'low' ? '正常' :
                 healthData?.risk_level === 'medium' ? '关注' : '警告'}
              </span>
            </div>
          </div>
        </div>

        {/* 安心指数卡片 */}
        {dailyReport && (
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 mt-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-indigo-200 text-sm">今日安心指数</p>
                <p className="text-white font-medium mt-1 text-sm">{dailyReport.one_line_summary}</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-white">{dailyReport.anxin_score}</p>
                <p className="text-indigo-200 text-xs">{dailyReport.anxin_level}</p>
              </div>
            </div>
            {dailyReport.tips_for_children.length > 0 && (
              <div className="mt-3 space-y-2">
                {dailyReport.tips_for_children.slice(0, 3).map((tip, idx) => {
                  const action = inferTipAction(tip);
                  const Icon = action.icon;
                  return (
                    <div
                      key={`${idx}-${tip.slice(0, 8)}`}
                      className="bg-white/10 rounded-xl px-3 py-2 flex items-center gap-3"
                    >
                      <p className="text-indigo-100 text-sm flex-1 leading-6">💡 {tip}</p>
                      <button
                        onClick={action.onClick}
                        className={`shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-white shadow-sm transition ${action.color}`}
                        title={action.label}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        {action.label}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="mt-4 rounded-2xl bg-white/12 p-4 ring-1 ring-white/10">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-white">转发今日日报给家人</p>
                  <p className="mt-1 text-xs leading-5 text-indigo-100/90">
                    分享时会自动附上家庭邀请码，家人点开链接或输入邀请码就能进入绑定流程。
                  </p>
                </div>
                <button
                  onClick={handleShareDailyReport}
                  disabled={shareLoading}
                  className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-indigo-600 shadow-sm transition hover:bg-indigo-50 disabled:opacity-60"
                >
                  {shareLoading ? <Copy className="h-5 w-5 animate-pulse" /> : <Share2 className="h-5 w-5" />}
                </button>
              </div>

              <div className="mt-3 flex flex-wrap gap-2 text-xs text-indigo-100">
                <span className="inline-flex items-center gap-1 rounded-full bg-white/10 px-3 py-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5" /> 优先系统分享
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-white/10 px-3 py-1.5">
                  <Link2 className="h-3.5 w-3.5" /> 自动附带邀请链接
                </span>
              </div>

              {shareStatus && (
                <p className="mt-3 rounded-xl bg-white/10 px-3 py-2 text-sm text-white/95">{shareStatus}</p>
              )}
            </div>
          </div>
        )}
      </div>

      {!subscription?.has_subscription && (
        <div className="px-6 -mt-2">
          <div className="rounded-3xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-4 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-amber-700">升级到安心版</p>
                <p className="mt-1 text-sm leading-6 text-gray-600">
                  解锁完整今日日报、连续安心趋势、更多家庭成员关注与主动守护能力。
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

      {/* r28 · 妈妈给您留言 + 妈妈最近想要的东西（仅 payer 可见 IntentCard） */}
      {parentUserId && (
        <div className="px-6 -mt-2 mb-2">
          <VoiceInbox />
          <IntentCard elderUserId={Number(parentUserId)} />
        </div>
      )}

      {/* 快捷操作 */}
      <div className="px-6 -mt-4">
        <div className="bg-white rounded-2xl shadow-lg p-4 grid grid-cols-4 gap-4">
          {shortcuts.map((item, index) => (
            <button
              key={index}
              onClick={item.action}
              className="flex flex-col items-center gap-2"
            >
              <div className={`w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center ${item.color}`}>
                <item.icon className="w-6 h-6" />
              </div>
              <span className="text-xs text-gray-600">{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 近期症状 */}
      {healthData?.recent_symptoms && healthData.recent_symptoms.length > 0 && (
        <div className="px-6 mt-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-gray-800">近期提到的症状</h2>
            <button
              onClick={() => onNavigate?.('trends')}
              className="text-indigo-600 text-sm flex items-center gap-1"
            >
              查看全部 <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {healthData.recent_symptoms.map((symptom, index) => (
              <span
                key={index}
                className="px-4 py-2 bg-orange-50 text-orange-700 rounded-full text-sm"
              >
                {symptom}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 建议事项 */}
      {healthData?.recommendations && healthData.recommendations.length > 0 && (
        <div className="px-6 mt-6">
          <h2 className="font-bold text-gray-800 mb-3">AI健康建议</h2>
          <div className="bg-white rounded-2xl shadow-sm p-4 space-y-3">
            {healthData.recommendations.map((rec, index) => (
              <div key={index} className="flex items-start gap-3">
                <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-green-600 text-xs">✓</span>
                </div>
                <p className="text-gray-700">{rec}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7日安心趋势 */}
      <div className="px-6 mt-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-gray-800">最近7天安心趋势</h2>
          <button
            onClick={() => onNavigate?.('trends')}
            className="text-indigo-600 text-sm flex items-center gap-1"
          >
            查看趋势 <ChevronRight className="w-4 h-4" />
          </button>
        </div>
        <div className="bg-white rounded-2xl shadow-sm p-4">
          {anxinTrend.length > 0 ? (
            <>
              <div className="flex items-end gap-2 h-28">
                {anxinTrend.map((item) => {
                  const barHeight = `${Math.max(20, (item.score / trendMaxScore) * 100)}%`;
                  const isAlert = item.score <= 6;
                  return (
                    <div key={item.date} className="flex-1 flex flex-col items-center gap-2">
                      <div className="text-xs font-semibold text-gray-600">{item.score}</div>
                      <div className="w-full flex items-end justify-center h-20">
                        <div
                          className={`w-full max-w-8 rounded-t-xl ${isAlert ? 'bg-amber-400' : 'bg-indigo-500'}`}
                          style={{ height: barHeight }}
                        />
                      </div>
                      <div className="text-[11px] text-gray-400">{formatReportDate(item.date)}</div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 flex items-center justify-between rounded-xl bg-indigo-50 px-3 py-2 text-sm">
                <span className="text-gray-600">本周平均安心指数</span>
                <span className="font-bold text-indigo-700">
                  {(anxinTrend.reduce((sum, item) => sum + item.score, 0) / anxinTrend.length).toFixed(1)}
                </span>
              </div>
            </>
          ) : (
            <div className="text-center text-sm text-gray-400 py-6">最近7天暂无安心趋势数据</div>
          )}
        </div>
      </div>

      {/* 异常日回看 */}
      <div className="px-6 mt-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-gray-800">需要重点关注的日子</h2>
          <div className="text-xs text-gray-400">自动筛出安心指数偏低或健康异常</div>
        </div>
        <div className="space-y-3">
          {abnormalReports.length > 0 ? (
            abnormalReports.slice(0, 3).map((item) => (
              <div key={item.date} className="bg-white rounded-2xl shadow-sm p-4 border border-amber-100">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                      <Calendar className="w-4 h-4 text-amber-500" />
                      <span>{formatReportDate(item.date)}</span>
                    </div>
                    <p className="font-medium text-gray-800">{item.one_line_summary}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs">
                      <span className="px-2 py-1 rounded-full bg-amber-50 text-amber-700">安心指数 {item.anxin_score}</span>
                      <span className="px-2 py-1 rounded-full bg-rose-50 text-rose-700">{item.health_status}</span>
                      <span className="px-2 py-1 rounded-full bg-indigo-50 text-indigo-700">情绪：{item.emotion}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => onStartVideoCall?.(parentUserId ?? '', parentName)}
                    disabled={!parentUserId}
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-50 text-indigo-600 disabled:opacity-40"
                  >
                    <Phone className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white rounded-2xl shadow-sm p-4 text-center text-gray-400 text-sm">
              最近7天没有明显异常，状态整体平稳
            </div>
          )}
        </div>
      </div>

      {/* 历史日报摘要 */}
      <div className="px-6 mt-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-gray-800">历史日报摘要</h2>
          <div className="text-xs text-gray-400">帮助你快速回看最近一周</div>
        </div>
        <div className="space-y-3">
          {reportHistory.length > 0 ? (
            reportHistory.slice(0, 5).map((item) => (
              <div key={item.date} className="bg-white rounded-2xl shadow-sm p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm text-gray-400">{formatReportDate(item.date)}</p>
                    <p className="font-medium text-gray-800 mt-1">{item.one_line_summary}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-indigo-600">{item.anxin_score}</p>
                    <p className="text-xs text-gray-400">{item.anxin_level}</p>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white rounded-2xl shadow-sm p-4 text-center text-gray-400 text-sm">
              暂无历史日报数据
            </div>
          )}
        </div>
      </div>

      {/* 最近对话 */}
      <div className="px-6 mt-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-gray-800">最近对话摘要</h2>
          <div className="text-xs text-gray-400">来自今日日报提炼</div>
        </div>
        <div className="space-y-3">
          {recentChats.length > 0 ? (
            recentChats.map((chat, index) => (
              <div key={index} className="bg-white rounded-2xl shadow-sm p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-400">{chat.time}</span>
                  <span className="text-lg">
                    {chat.mood === 'happy' ? '😊' : chat.mood === 'sad' ? '😔' : '😐'}
                  </span>
                </div>
                <p className="text-gray-700">{chat.content}</p>
              </div>
            ))
          ) : (
            <div className="bg-white rounded-2xl shadow-sm p-4 text-center text-gray-400 text-sm">
              暂无对话记录
            </div>
          )}
        </div>
      </div>

      {/* 底部提醒设置 */}
      <div className="px-6 mt-6">
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-6 h-6 text-indigo-600" />
              <div>
                <p className="font-medium text-gray-800">异常提醒已开启</p>
                <p className="text-sm text-gray-500">健康评分≥7时自动通知</p>
              </div>
            </div>
            <div className="w-12 h-7 bg-indigo-600 rounded-full relative">
              <div className="absolute right-1 top-1 w-5 h-5 bg-white rounded-full"></div>
            </div>
          </div>
        </div>
      </div>

      {/* 底部导航 */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-6 py-3">
        <div className="flex items-center justify-around">
          {[
            { key: 'health', icon: Heart, label: '健康' },
            { key: 'trends', icon: TrendingUp, label: '趋势' },
            { key: 'notifications', icon: Bell, label: '提醒' },
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => {
                setActiveTab(item.key as typeof activeTab);
                if (item.key !== 'health' && onNavigate) {
                  onNavigate(item.key as 'trends' | 'notifications' | 'chat');
                }
              }}
              className={`flex flex-col items-center gap-1 ${
                activeTab === item.key ? 'text-indigo-600' : 'text-gray-400'
              }`}
            >
              <item.icon className="w-6 h-6" />
              <span className="text-xs">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
