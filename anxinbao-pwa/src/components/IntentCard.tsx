import { useEffect, useState } from 'react';
import { ShoppingBag, Check, X, RefreshCw } from 'lucide-react';
import {
  listCommercialIntents,
  reviewIntent,
  dismissIntent,
  type CommercialIntent,
} from '../lib/api';

/**
 * 子女端"妈妈最近想要的东西"卡片（r28 落地 Insight #13）
 *
 * 入口：ChildDashboard 顶部
 * 行为：
 *   - 仅 payer 角色拉得到（后端 _require_payer_for_elder 校验）
 *   - 列出 status='detected' 的活跃意图
 *   - 子女可标"已查看 / 我看到了"或"关掉 / 不用买"
 *   - 当前 alpha：不接通商城；只展示 + 状态机
 *
 * 隐私：老人**永远看不到**自己的 intent（payer-only）
 */
interface Props {
  elderUserId: number;
}

const CATEGORY_LABEL: Record<string, string> = {
  nutrition: '🥛 营养',
  pain_relief: '💊 镇痛/关节',
  sleep: '😴 睡眠',
  mobility: '🚶 行动',
  hygiene: '🧻 卫生',
  hobby: '📻 兴趣',
  appliance: '⚡ 家电',
};

export default function IntentCard({ elderUserId }: Props) {
  const [items, setItems] = useState<CommercialIntent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [acting, setActing] = useState<number | null>(null);

  const refresh = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listCommercialIntents(elderUserId, 'detected');
      setItems(data.items);
    } catch (e) {
      // 403 表示当前家属不是 payer，正常情况，悄悄隐藏
      const msg = e instanceof Error ? e.message : '加载失败';
      if (msg.includes('403') || msg.includes('payer')) {
        setItems([]);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [elderUserId]);

  const handleReview = async (id: number) => {
    setActing(id);
    try {
      await reviewIntent(id);
      setItems((prev) => prev.filter((it) => it.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : '操作失败');
    } finally {
      setActing(null);
    }
  };

  const handleDismiss = async (id: number) => {
    setActing(id);
    try {
      await dismissIntent(id);
      setItems((prev) => prev.filter((it) => it.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : '操作失败');
    } finally {
      setActing(null);
    }
  };

  // 没数据 + 不在加载 → 不渲染卡片（避免空状态污染 UI）
  if (!loading && items.length === 0 && !error) return null;

  return (
    <div className="bg-white rounded-3xl shadow-sm p-5 mb-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ShoppingBag className="w-5 h-5 text-orange-500" />
          <h3 className="font-bold text-gray-800">妈妈最近提到的东西</h3>
          <span className="text-xs text-gray-400">{items.length} 条</span>
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
        <p className="text-gray-400 text-sm text-center py-4">加载中...</p>
      ) : (
        <div className="space-y-2">
          {items.map((it) => (
            <div
              key={it.id}
              className="rounded-2xl bg-orange-50 border border-orange-100 p-3"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-500 mb-1">
                    {CATEGORY_LABEL[it.category] || it.category}
                  </p>
                  <p className="text-gray-800 text-sm font-medium">
                    {it.suggested_title || it.keyword}
                  </p>
                  {it.source_text && (
                    <p className="text-gray-500 text-xs mt-1 italic line-clamp-2">
                      "{it.source_text}"
                    </p>
                  )}
                </div>
                <div className="flex flex-col gap-1 shrink-0">
                  <button
                    onClick={() => handleReview(it.id)}
                    disabled={acting === it.id}
                    className="text-xs px-3 py-1 rounded-full bg-indigo-500 text-white hover:bg-indigo-600 flex items-center gap-1 disabled:opacity-60"
                  >
                    <Check className="w-3 h-3" /> 看到了
                  </button>
                  <button
                    onClick={() => handleDismiss(it.id)}
                    disabled={acting === it.id}
                    className="text-xs px-3 py-1 rounded-full text-gray-500 hover:bg-gray-100 flex items-center gap-1 disabled:opacity-60"
                  >
                    <X className="w-3 h-3" /> 不用买
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-400 mt-3 text-center">
        AI 从妈妈最近的对话里识别 · 仅您（主付费人）可见
      </p>
    </div>
  );
}
