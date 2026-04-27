import { useEffect, useState } from 'react';
import { Mic, RefreshCw } from 'lucide-react';
import { getVoiceInbox, markVoiceRead, type VoiceMessage } from '../lib/api';

/**
 * 子女端语音收件箱（r28 落地 Insight #12）
 *
 * 入口：ChildDashboard 顶部"妈妈来语音了 (N)"红点
 * 行为：
 *   - 拉 GET /api/voice-message/inbox?unread_only=false
 *   - 未读优先 + 时间倒序展示
 *   - 点击展开 → audio 播放 + AI caption + 时长
 *   - 播放完自动 mark-read
 *   - emotion 字段用 emoji 体现（开心 😊 / 想念 🥺 / 中性 🙂）
 *
 * 设计原则：
 *   - 不在通知栏暴露 transcript（隐私）
 *   - AI caption 是子女首屏看到的"妈妈想说什么"摘要
 *   - 录音原声永远是首要内容，AI 只是辅助
 */

const EMOTION_EMOJI: Record<string, string> = {
  happy: '😊',
  sad: '😢',
  lonely: '🥺',
  anxious: '😟',
  tired: '😪',
  angry: '😠',
  neutral: '🙂',
};

export default function VoiceInbox() {
  const [items, setItems] = useState<VoiceMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const refresh = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getVoiceInbox(false, 30);
      // 未读优先 + created_at desc
      const sorted = [...data.items].sort((a, b) => {
        const aUnread = !a.read_at ? 1 : 0;
        const bUnread = !b.read_at ? 1 : 0;
        if (aUnread !== bUnread) return bUnread - aUnread;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      setItems(sorted);
    } catch (e) {
      setError(e instanceof Error ? e.message : '拉取失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // 每 60s 自动刷一次
    const t = window.setInterval(refresh, 60000);
    return () => window.clearInterval(t);
  }, []);

  const handleExpand = async (msg: VoiceMessage) => {
    setExpandedId(msg.id === expandedId ? null : msg.id);
    if (!msg.read_at) {
      try {
        await markVoiceRead(msg.id);
        // 本地也更新一下，免等下次 refresh
        setItems((prev) =>
          prev.map((m) => (m.id === msg.id ? { ...m, read_at: new Date().toISOString() } : m)),
        );
      } catch (_) { /* 忽略 */ }
    }
  };

  const unreadCount = items.filter((m) => !m.read_at).length;

  return (
    <div className="bg-white rounded-3xl shadow-sm p-5 mb-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Mic className="w-5 h-5 text-pink-500" />
          <h3 className="font-bold text-gray-800">妈妈给您留言</h3>
          {unreadCount > 0 && (
            <span className="ml-1 px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
              {unreadCount} 未听
            </span>
          )}
        </div>
        <button
          onClick={refresh}
          className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
        >
          <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} /> 刷新
        </button>
      </div>

      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}

      {loading && items.length === 0 ? (
        <p className="text-gray-400 text-sm text-center py-6">加载中...</p>
      ) : items.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-400 text-sm">暂无语音留言</p>
          <p className="text-gray-300 text-xs mt-1">老人对 AI 说"想给您留段话"时会自动出现</p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.slice(0, 10).map((m) => {
            const expanded = expandedId === m.id;
            const emoji = EMOTION_EMOJI[m.emotion || 'neutral'] || '🙂';
            const isUnread = !m.read_at;
            return (
              <div
                key={m.id}
                className={`rounded-2xl p-3 cursor-pointer transition-colors ${
                  isUnread ? 'bg-pink-50 border border-pink-200' : 'bg-gray-50'
                }`}
                onClick={() => handleExpand(m)}
              >
                <div className="flex items-center gap-3">
                  <div className="text-2xl">{emoji}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-gray-800 text-sm truncate">
                      {m.ai_caption || '妈妈给您留了段话'}
                    </p>
                    <p className="text-gray-400 text-xs mt-0.5">
                      {m.duration_sec}s · {new Date(m.created_at).toLocaleString('zh-CN', {
                        month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit',
                      })}
                    </p>
                  </div>
                  {isUnread && <span className="w-2 h-2 bg-red-500 rounded-full" />}
                </div>
                {expanded && (
                  <div className="mt-3">
                    <audio
                      src={m.audio_url}
                      controls
                      className="w-full"
                      onEnded={() => { /* 已在 handleExpand 标 read */ }}
                    />
                    {m.transcript && (
                      <p className="text-xs text-gray-500 mt-2 italic">
                        转写：{m.transcript}
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
