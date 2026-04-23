import { useState, useEffect, useRef } from 'react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { MessageCircle, Phone, Loader2, Check, X, Pill, Users, Sparkles } from 'lucide-react';
import { getStoredUser, getMyFamilyGroups, createFamilyGroup, createBindingRequest, getFamilyGroupId, generateProactiveGreeting, triggerSOS } from '../lib/api';

interface StandbyScreenProps {
  onWakeUp: () => void;
  onNavigate?: (page: 'notifications' | 'medication') => void;
}

export default function StandbyScreen({ onWakeUp, onNavigate }: StandbyScreenProps) {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [weather, setWeather] = useState<{ temp: number; condition: string; icon: string }>({
    temp: 20,
    condition: '加载中',
    icon: '🌤️',
  });
  const [weatherLoaded, setWeatherLoaded] = useState(false);
  const [sosState, setSosState] = useState<'idle' | 'confirm' | 'sending' | 'sent' | 'error'>('idle');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [proactiveGreeting, setProactiveGreeting] = useState<string | null>(null);
  // SOS 长按计时（防止老人误触；按住 1.5 秒才进入确认）
  const [sosHoldProgress, setSosHoldProgress] = useState(0); // 0~100
  const sosHoldTimer = useRef<number | null>(null);
  const sosProgressTimer = useRef<number | null>(null);

  // 更新时间
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 获取真实天气（wttr.in，无需 API Key）
  useEffect(() => {
    const fetchWeather = async () => {
      // 检查缓存（30分钟内有效）
      const cached = localStorage.getItem('weather_cache');
      if (cached) {
        try {
          const { data, ts } = JSON.parse(cached);
          if (Date.now() - ts < 30 * 60 * 1000) {
            setWeather(data);
            setWeatherLoaded(true);
            return;
          }
        } catch { /* 忽略损坏缓存 */ }
      }
      try {
        const resp = await fetch('https://wttr.in/?format=j1', {
          signal: AbortSignal.timeout(5000),
        });
        if (!resp.ok) throw new Error('weather api failed');
        const json = await resp.json();
        const current = json.current_condition?.[0];
        if (!current) throw new Error('no current condition');
        const tempC = parseInt(current.temp_C);
        const desc = current.lang_zh?.[0]?.value || current.weatherDesc?.[0]?.value || '未知';
        // 根据 weatherCode 映射 emoji
        const weatherCode = parseInt(current.weatherCode);
        let icon = '🌤️';
        if (weatherCode === 113) icon = '☀️';
        else if (weatherCode <= 116) icon = '⛅';
        else if (weatherCode <= 119) icon = '☁️';
        else if (weatherCode <= 266) icon = '🌧️';
        else if (weatherCode <= 296) icon = '🌧️';
        else if (weatherCode <= 395) icon = '❄️';
        const weatherData = { temp: tempC, condition: desc, icon };
        setWeather(weatherData);
        setWeatherLoaded(true);
        localStorage.setItem('weather_cache', JSON.stringify({ data: weatherData, ts: Date.now() }));
      } catch {
        // 按季节回退默认值
        const month = new Date().getMonth();
        const seasonTemp = [8, 10, 15, 20, 25, 30, 33, 33, 28, 22, 15, 9][month];
        setWeather({ temp: seasonTemp, condition: '天气加载失败', icon: '🌤️' });
        setWeatherLoaded(true);
      }
    };
    fetchWeather();

    const weatherTimer = setInterval(fetchWeather, 30 * 60 * 1000);
    return () => clearInterval(weatherTimer);
  }, []);

  // SOS 触发
  const handleTriggerSOS = async () => {
    setSosState('sending');
    try {
      const user = getStoredUser();
      const elderUserId = user?.elder_id ? String(user.elder_id) : user?.user_id;
      if (!elderUserId) throw new Error('未获取到老人账号信息');
      await triggerSOS(elderUserId, { description: '紧急求助' });
      setSosState('sent');
      setTimeout(() => setSosState('idle'), 5000);
    } catch {
      setSosState('error');
      setTimeout(() => setSosState('idle'), 3000);
    }
  };

  // 生成邀请码
  const generateInviteCode = async () => {
    setInviteLoading(true);
    setInviteError(null);
    setInviteCode(null);
    try {
      // 获取或创建家庭组
      let groupId: string;
      const { groups } = await getMyFamilyGroups();
      if (groups.length > 0) {
        groupId = getFamilyGroupId(groups[0]);
      } else {
        const user = getStoredUser();
        const elderName = user?.name || '我';
        const result = await createFamilyGroup(`${elderName}的家庭`, elderName);
        groupId = getFamilyGroupId(result.group);
      }
      // 创建绑定请求，拿到邀请码
      const { invite_code } = await createBindingRequest(groupId);
      setInviteCode(invite_code);
    } catch (err) {
      setInviteError(err instanceof Error ? err.message : '生成失败，请重试');
    } finally {
      setInviteLoading(false);
    }
  };

  // 问候语
  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 6) return { text: '夜深了', sub: '注意休息' };
    if (hour < 9) return { text: '早上好', sub: '新的一天开始了' };
    if (hour < 12) return { text: '上午好', sub: '今天精神怎么样' };
    if (hour < 14) return { text: '中午好', sub: '记得吃午饭哦' };
    if (hour < 18) return { text: '下午好', sub: '喝杯茶休息一下' };
    if (hour < 22) return { text: '晚上好', sub: '今天过得开心吗' };
    return { text: '夜深了', sub: '早点休息吧' };
  };

  useEffect(() => {
    const user = getStoredUser();
    const elderUserId = user?.elder_id ? String(user.elder_id) : user?.user_id;
    if (!elderUserId) return;

    let cancelled = false;
    generateProactiveGreeting(elderUserId)
      .then((result) => {
        if (!cancelled) {
          setProactiveGreeting(result.greeting);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setProactiveGreeting(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const greeting = getGreeting();

  // 农历信息（简化版）
  const getLunarInfo = () => {
    const lunarMonths = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月'];
    const lunarDays = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十', '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十'];
    const day = currentTime.getDate();
    const month = currentTime.getMonth();
    return `${lunarMonths[month % 12]}${lunarDays[(day - 1) % 30]}`;
  };

  // SOS 按钮：放大到 96px、独占一行、长按 1.5s 触发，杜绝老人误触
  // （历史上 SOS 与"邀请家人"相邻且仅 64px，单击即弹确认弹窗，是 UX 上的致命相邻）
  const SOS_HOLD_MS = 1500;

  const startSosHold = () => {
    if (sosState !== 'idle') return;
    const startedAt = Date.now();
    setSosHoldProgress(0);
    sosProgressTimer.current = window.setInterval(() => {
      const pct = Math.min(100, ((Date.now() - startedAt) / SOS_HOLD_MS) * 100);
      setSosHoldProgress(pct);
    }, 50);
    sosHoldTimer.current = window.setTimeout(() => {
      cancelSosHold();
      setSosState('confirm');
    }, SOS_HOLD_MS);
  };

  const cancelSosHold = () => {
    if (sosHoldTimer.current) {
      clearTimeout(sosHoldTimer.current);
      sosHoldTimer.current = null;
    }
    if (sosProgressTimer.current) {
      clearInterval(sosProgressTimer.current);
      sosProgressTimer.current = null;
    }
    setSosHoldProgress(0);
  };

  // 卸载时清理计时器，防止泄漏（直接读 ref，避免 useEffect 依赖列表 lint 警告）
  useEffect(() => {
    return () => {
      if (sosHoldTimer.current) clearTimeout(sosHoldTimer.current);
      if (sosProgressTimer.current) clearInterval(sosProgressTimer.current);
    };
  }, []);

  // Phone 按钮样式（96px、明显的红色基色，反映 SOS 状态）
  const getPhoneButtonClass = () => {
    const base = 'relative w-24 h-24 rounded-3xl flex items-center justify-center transition-all active:scale-95 ring-4 ring-white/20 shadow-lg select-none';
    switch (sosState) {
      case 'confirm':
        return `${base} bg-red-500 animate-pulse`;
      case 'sending':
        return `${base} bg-yellow-500`;
      case 'sent':
        return `${base} bg-green-600`;
      case 'error':
        return `${base} bg-red-700`;
      default:
        return `${base} bg-red-500/85 hover:bg-red-500`;
    }
  };

  const getPhoneButtonIcon = () => {
    switch (sosState) {
      case 'sending':
        return <Loader2 className="w-10 h-10 text-white animate-spin" />;
      case 'sent':
        return <Check className="w-10 h-10 text-white" />;
      case 'error':
        return <X className="w-10 h-10 text-white" />;
      default:
        return <Phone className="w-10 h-10 text-white" />;
    }
  };

  // 用于抑制 weatherLoaded 未使用的 lint 警告（后续可用于动画）
  void weatherLoaded;

  return (
    <div
      className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-indigo-800 flex flex-col items-center justify-center p-8 cursor-pointer"
      onClick={onWakeUp}
    >
      {/* 主时间显示 */}
      <div className="text-center mb-8">
        <p className="text-8xl font-thin text-white tracking-wider mb-2">
          {format(currentTime, 'HH:mm')}
        </p>
        <p className="text-2xl text-indigo-200">
          {format(currentTime, 'ss', { locale: zhCN })} 秒
        </p>
      </div>

      {/* 日期信息 */}
      <div className="text-center mb-8">
        <p className="text-2xl text-white mb-1">
          {format(currentTime, 'yyyy年MM月dd日', { locale: zhCN })}
        </p>
        <p className="text-xl text-indigo-300">
          {format(currentTime, 'EEEE', { locale: zhCN })} · {getLunarInfo()}
        </p>
      </div>

      {/* 天气卡片 */}
      <div className="bg-white/10 backdrop-blur-md rounded-3xl p-6 mb-8 flex items-center gap-6">
        <div className="text-6xl">{weather.icon}</div>
        <div>
          <p className="text-4xl font-light text-white">{weather.temp}°C</p>
          <p className="text-xl text-indigo-200">{weather.condition}</p>
        </div>
      </div>

      {/* 问候语 */}
      <div className="text-center mb-12">
        <p className="text-4xl font-bold text-white mb-2">{greeting.text}</p>
        <p className="text-xl text-indigo-200">{greeting.sub}</p>
      </div>

      {proactiveGreeting && (
        <div className="mb-10 w-full max-w-2xl">
          <button
            onClick={(e) => { e.stopPropagation(); onWakeUp(); }}
            className="w-full rounded-3xl bg-white/12 backdrop-blur-md px-6 py-5 text-left shadow-lg ring-1 ring-white/10 hover:bg-white/15 transition-all"
          >
            <div className="flex items-start gap-4">
              <div className="mt-1 flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-400/20 text-amber-200">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="flex-1">
                <p className="text-sm tracking-wide text-amber-200">主动问候</p>
                <p className="mt-2 text-xl leading-8 text-white">{proactiveGreeting}</p>
                <p className="mt-3 text-sm text-indigo-100/80">点一下，继续和安心宝聊聊</p>
              </div>
            </div>
          </button>
        </div>
      )}

      {/* 提示文字 */}
      <div className="absolute bottom-12 left-0 right-0 text-center">
        <div className="inline-flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-full px-8 py-4">
          <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          <p className="text-xl text-white">点击屏幕或按下按钮开始聊天</p>
        </div>
      </div>

      {/* 普通快捷入口（聊天 / 邀请家人 / 用药）：放大到 80px、与 SOS 完全分离 */}
      <div className="absolute bottom-60 left-0 right-0 flex justify-center gap-10">
        {/* 聊天按钮 */}
        <button
          onClick={(e) => { e.stopPropagation(); onWakeUp(); }}
          className="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-3xl flex items-center justify-center hover:bg-white/30 transition-all active:scale-95"
          title="开始聊天"
        >
          <MessageCircle className="w-10 h-10 text-white" />
        </button>

        {/* 邀请家人按钮（远离 SOS） */}
        <button
          onClick={(e) => { e.stopPropagation(); setShowInviteModal(true); setInviteCode(null); setInviteError(null); }}
          className="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-3xl flex items-center justify-center hover:bg-white/30 transition-all active:scale-95"
          title="邀请家人"
        >
          <Users className="w-10 h-10 text-white" />
        </button>

        {/* 用药提醒按钮 */}
        <button
          onClick={(e) => { e.stopPropagation(); onNavigate?.('medication'); }}
          className="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-3xl flex items-center justify-center hover:bg-white/30 transition-all active:scale-95"
          title="今日用药"
        >
          <Pill className="w-10 h-10 text-white" />
        </button>
      </div>

      {/* SOS 紧急求助按钮：独立位置、放大到 96px、长按 1.5s 触发 */}
      <div className="absolute bottom-24 left-0 right-0 flex flex-col items-center gap-2">
        <button
          onClick={(e) => e.stopPropagation()}
          onPointerDown={(e) => { e.stopPropagation(); startSosHold(); }}
          onPointerUp={(e) => { e.stopPropagation(); cancelSosHold(); }}
          onPointerLeave={cancelSosHold}
          onPointerCancel={cancelSosHold}
          className={getPhoneButtonClass()}
          title="按住 1.5 秒呼叫家人"
        >
          {getPhoneButtonIcon()}
          {/* 长按进度环（视觉反馈，避免老人不知道还在按） */}
          {sosHoldProgress > 0 && sosState === 'idle' && (
            <span
              className="absolute inset-0 rounded-3xl ring-4 ring-white pointer-events-none"
              style={{ clipPath: `inset(${100 - sosHoldProgress}% 0 0 0)` }}
            />
          )}
        </button>
        <span className="text-sm text-white/80 select-none">
          紧急求助 · 按住 1.5 秒
        </span>
      </div>

      {/* SOS 确认弹窗 */}
      {sosState === 'confirm' && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
          onClick={() => setSosState('idle')}
        >
          <div
            className="bg-white rounded-3xl p-8 mx-6 text-center"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="text-6xl mb-4">🆘</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">确认紧急求助？</h2>
            <p className="text-gray-500 mb-8">将立即通知您的家人</p>
            <div className="flex gap-4">
              <button
                onClick={() => setSosState('idle')}
                className="flex-1 py-4 bg-gray-100 rounded-2xl text-xl text-gray-700 font-medium"
              >
                取消
              </button>
              <button
                onClick={handleTriggerSOS}
                className="flex-1 py-4 bg-red-500 rounded-2xl text-xl text-white font-bold"
              >
                确认求助
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 发送成功 Toast */}
      {sosState === 'sent' && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 pointer-events-none">
          <div className="bg-green-500 rounded-3xl px-10 py-8 mx-6 text-center shadow-2xl">
            <div className="text-5xl mb-3">✅</div>
            <h2 className="text-2xl font-bold text-white">求助已发送</h2>
            <p className="text-green-100 mt-2">家人已收到通知，请保持冷静</p>
          </div>
        </div>
      )}

      {/* 发送失败 Toast */}
      {sosState === 'error' && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 pointer-events-none">
          <div className="bg-red-500 rounded-3xl px-10 py-8 mx-6 text-center shadow-2xl">
            <div className="text-5xl mb-3">❌</div>
            <h2 className="text-2xl font-bold text-white">发送失败</h2>
            <p className="text-red-100 mt-2">请检查网络后重试</p>
          </div>
        </div>
      )}
      {/* 邀请码弹窗 */}
      {showInviteModal && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
          onClick={() => setShowInviteModal(false)}
        >
          <div
            className="bg-white rounded-3xl p-8 mx-6 w-full max-w-sm text-center"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="text-5xl mb-4">👨‍👩‍👧‍👦</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">邀请家人关注</h2>
            <p className="text-gray-500 text-sm mb-6">
              生成邀请码，发给您的子女或家人，让他们在家属端输入即可关注您的健康状态
            </p>

            {!inviteCode && !inviteLoading && !inviteError && (
              <button
                onClick={generateInviteCode}
                className="w-full py-4 bg-indigo-600 rounded-2xl text-xl text-white font-bold mb-4"
              >
                生成邀请码
              </button>
            )}

            {inviteLoading && (
              <div className="flex items-center justify-center gap-3 py-4 mb-4">
                <Loader2 className="w-6 h-6 text-indigo-600 animate-spin" />
                <span className="text-gray-600">生成中...</span>
              </div>
            )}

            {inviteError && (
              <div className="bg-red-50 rounded-2xl p-4 mb-4">
                <p className="text-red-600 text-sm">{inviteError}</p>
                <button
                  onClick={generateInviteCode}
                  className="mt-3 w-full py-3 bg-red-100 rounded-xl text-red-700 font-medium"
                >
                  重试
                </button>
              </div>
            )}

            {inviteCode && (
              <div className="mb-6">
                <p className="text-sm text-gray-500 mb-3">您的邀请码（有效期7天）</p>
                <div className="bg-indigo-50 rounded-2xl p-5">
                  <p className="text-4xl font-bold text-indigo-700 tracking-[0.3em]">{inviteCode}</p>
                </div>
                <p className="text-xs text-gray-400 mt-3">告诉家人在安心宝家属端输入此邀请码</p>
              </div>
            )}

            <button
              onClick={() => setShowInviteModal(false)}
              className="w-full py-4 bg-gray-100 rounded-2xl text-xl text-gray-700 font-medium"
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
