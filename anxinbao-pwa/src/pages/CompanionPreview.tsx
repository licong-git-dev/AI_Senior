/**
 * CompanionPreview · 数字生命陪伴 alpha 预览页
 *
 * ⚠️ Alpha 状态，仅当 URL 含 `?mode=companion-preview` 时可访问。
 * ⚠️ 后端需设置 COMPANION_ENABLED=true 才能调通 /api/companion/*。
 *
 * 页面结构：
 * - 顶部：当前 persona 摘要 + 记忆统计
 * - 中部：对话框（复用 ChatPage 风格）
 * - 底部：工具池速查 + "一键忘记" 按钮
 *
 * 不接入生产路由表；仅通过直接 URL 访问，避免老人 / 家属误入。
 */
import { useEffect, useState } from 'react';
import { AlertTriangle, Brain, Heart, Send, Trash2 } from 'lucide-react';
import { authFetch } from '../lib/api';

interface PersonaSummary {
  name: string;
  age_persona: string;
  accent: string;
  personality: {
    warmth: number;
    patience: number;
    humor: number;
    proactivity: number;
    formality: number;
  };
  catchphrases: string[];
  taboos: string[];
}

interface MemoryStats {
  user_id: number;
  total: number;
  by_type: Record<string, number>;
}

interface ChatMessage {
  role: 'user' | 'companion';
  text: string;
  fallback?: boolean;
  usedMemories?: number[];
  at: string;
}

export default function CompanionPreview() {
  const [persona, setPersona] = useState<PersonaSummary | null>(null);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 初始拉取 persona + 记忆统计
  useEffect(() => {
    const init = async () => {
      try {
        const pResp = await authFetch('/api/companion/persona');
        if (pResp.status === 503) {
          setError('Companion 模式未在后端开启 (COMPANION_ENABLED=false)。请联系管理员。');
          return;
        }
        if (!pResp.ok) throw new Error('persona 获取失败');
        setPersona(await pResp.json());

        const sResp = await authFetch('/api/companion/memory/stats');
        if (sResp.ok) {
          setStats(await sResp.json());
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '初始化失败');
      }
    };
    init();
  }, []);

  const send = async () => {
    if (!input.trim() || sending) return;
    const userMsg: ChatMessage = { role: 'user', text: input, at: new Date().toISOString() };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setSending(true);

    try {
      const resp = await authFetch('/api/companion/chat', {
        method: 'POST',
        body: JSON.stringify({ message: userMsg.text, elder_name: '您' }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setMessages((m) => [
        ...m,
        {
          role: 'companion',
          text: data.text,
          fallback: data.fallback,
          usedMemories: data.used_memories,
          at: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: 'companion',
          text: `[发送失败] ${err instanceof Error ? err.message : '未知错误'}`,
          fallback: true,
          at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const forgetAll = async () => {
    if (!window.confirm('确定要清空所有记忆吗？此操作不可恢复。')) return;
    try {
      const resp = await authFetch('/api/companion/memory/all/clear?confirm=true', {
        method: 'DELETE',
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      window.alert(`已清空 ${data.deleted_count} 条记忆`);
      setStats((s) => (s ? { ...s, total: 0, by_type: {} } : s));
    } catch (err) {
      window.alert(`清空失败：${err instanceof Error ? err.message : err}`);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
        <div className="max-w-md bg-white rounded-2xl shadow p-6 text-center">
          <AlertTriangle className="mx-auto w-12 h-12 text-amber-500 mb-4" />
          <h2 className="text-xl font-bold mb-2">Companion 预览不可用</h2>
          <p className="text-gray-600">{error}</p>
          <p className="text-xs text-gray-400 mt-4">
            详见 anxinbao-server/docs/DIGITAL_COMPANION_RFC.md
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 p-6">
      {/* Alpha 警示带 */}
      <div className="max-w-3xl mx-auto mb-4 bg-amber-100 border border-amber-300 rounded-xl p-3 text-sm text-amber-800">
        <strong>🚧 Alpha 预览</strong> · 数字生命陪伴 Phase 1 ·
        此页面仅供评审，不稳定，不代表正式产品
      </div>

      {/* Persona + 记忆卡片 */}
      <div className="max-w-3xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="bg-white rounded-2xl shadow p-4">
          <div className="flex items-center gap-2 mb-2">
            <Heart className="w-5 h-5 text-pink-500" />
            <h3 className="font-bold">人格 · Persona</h3>
          </div>
          {persona ? (
            <div className="text-sm text-gray-700 space-y-1">
              <p>
                <span className="text-gray-400">名字：</span>
                {persona.name}（{persona.age_persona}人格）
              </p>
              <p>
                <span className="text-gray-400">方言：</span>
                {persona.accent}
              </p>
              <p>
                <span className="text-gray-400">温暖 / 耐心 / 主动：</span>
                {persona.personality.warmth.toFixed(1)} /{' '}
                {persona.personality.patience.toFixed(1)} /{' '}
                {persona.personality.proactivity.toFixed(1)}
              </p>
              <p className="text-xs text-gray-400 mt-2">
                口头禅：{persona.catchphrases.slice(0, 2).join('、')}
              </p>
            </div>
          ) : (
            <p className="text-sm text-gray-400">加载中...</p>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-indigo-500" />
              <h3 className="font-bold">长期记忆</h3>
            </div>
            <button
              onClick={forgetAll}
              className="text-xs text-red-500 hover:text-red-700 flex items-center gap-1"
            >
              <Trash2 className="w-3 h-3" /> 忘记我吧
            </button>
          </div>
          {stats ? (
            <div className="text-sm text-gray-700">
              <p className="text-2xl font-bold text-indigo-600">{stats.total}</p>
              <p className="text-xs text-gray-400">
                事实 {stats.by_type?.fact ?? 0} · 偏好 {stats.by_type?.preference ?? 0} ·
                关系 {stats.by_type?.relation ?? 0} · 事件 {stats.by_type?.event ?? 0} ·
                心境 {stats.by_type?.mood ?? 0}
              </p>
            </div>
          ) : (
            <p className="text-sm text-gray-400">加载中...</p>
          )}
        </div>
      </div>

      {/* 对话区 */}
      <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow flex flex-col" style={{ height: '50vh' }}>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <p className="text-sm text-gray-400 text-center mt-20">
              跟安心宝说说话吧 —— 它会记得你说过什么
            </p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={m.role === 'user' ? 'text-right' : ''}>
              <div
                className={`inline-block max-w-[80%] rounded-2xl px-4 py-2 ${
                  m.role === 'user'
                    ? 'bg-indigo-500 text-white'
                    : m.fallback
                    ? 'bg-amber-50 text-gray-700 border border-amber-200'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <p className="text-sm leading-6 whitespace-pre-wrap">{m.text}</p>
                {m.role === 'companion' && m.usedMemories && m.usedMemories.length > 0 && (
                  <p className="text-xs text-gray-400 mt-1">
                    🔗 召回了 {m.usedMemories.length} 条记忆
                  </p>
                )}
                {m.role === 'companion' && m.fallback && (
                  <p className="text-xs text-amber-600 mt-1">⚠️ 使用了兜底应答</p>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="border-t p-3 flex gap-2">
          <input
            className="flex-1 rounded-full px-4 py-2 bg-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !sending && send()}
            placeholder="跟安心宝说说话..."
            disabled={sending}
          />
          <button
            onClick={send}
            disabled={sending || !input.trim()}
            className="bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white rounded-full px-4 py-2 flex items-center gap-1"
          >
            <Send className="w-4 h-4" /> 发送
          </button>
        </div>
      </div>

      {/* 后端状态提示 */}
      <p className="max-w-3xl mx-auto mt-4 text-xs text-gray-500 text-center">
        此页面调用 <code>/api/companion/*</code>，需后端设置{' '}
        <code>COMPANION_ENABLED=true</code>。详见{' '}
        <span className="underline">anxinbao-server/docs/DIGITAL_COMPANION_RFC.md</span>
      </p>
    </div>
  );
}
