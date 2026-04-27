import { useEffect, useState, useCallback } from 'react';
import { Volume2, X } from 'lucide-react';
import { getActivationScript, markOnboardingDone } from '../lib/api';

/**
 * 3 句话激活蒙层（r28 落地 Insight #11）
 *
 * 行为：
 *   - 在老人 StandbyScreen 加载完后，1 秒延迟自动检测 is_first_visit
 *   - 是 → 全屏蒙层，依次显示 3 句话（5s + 10s + 15s 节奏）
 *   - 浏览器原生 SpeechSynthesis 朗读（不依赖讯飞 TTS，0 延迟）
 *   - 老人点 "我听完了" → mark-done + 关闭
 *   - 老人点右上角 X → 关闭但**不**标 done（下次还会再来）
 *
 * 设计：
 *   - 蒙层是不抢焦点的全屏遮罩；点击文字外区域关不掉（防误触）
 *   - 字号 24+px，按钮 80+px
 *   - 朗读失败（浏览器不支持 / 老人静音）→ 仍可阅读后点完
 */
interface Props {
  onClose: () => void;
}

export default function ActivationOverlay({ onClose }: Props) {
  const [lines, setLines] = useState<string[]>([]);
  const [visibleCount, setVisibleCount] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [shouldShow, setShouldShow] = useState(false);
  const [marking, setMarking] = useState(false);

  const speakLine = useCallback((text: string) => {
    if (!('speechSynthesis' in window)) return;
    try {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'zh-CN';
      u.rate = 0.85; // 略慢，老人友好
      u.pitch = 1.0;
      window.speechSynthesis.cancel(); // 停掉前一句避免重叠
      window.speechSynthesis.speak(u);
    } catch (_) { /* 忽略 */ }
  }, []);

  // 拉脚本
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await getActivationScript();
        if (cancelled) return;
        if (!data.is_first_visit) {
          // 不是首次，直接关
          onClose();
          return;
        }
        setLines(data.lines);
        setShouldShow(true);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : '加载失败');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [onClose]);

  // 节奏：第 1 句立即出 + 朗读，5s 后第 2 句，再 10s 后第 3 句
  useEffect(() => {
    if (!shouldShow || lines.length === 0) return;
    speakLine(lines[0]);

    const t1 = window.setTimeout(() => {
      setVisibleCount(2);
      speakLine(lines[1] || '');
    }, 5000);

    const t2 = window.setTimeout(() => {
      setVisibleCount(3);
      speakLine(lines[2] || '');
    }, 15000);

    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
      try { window.speechSynthesis.cancel(); } catch (_) {}
    };
  }, [shouldShow, lines, speakLine]);

  const handleDone = async () => {
    setMarking(true);
    try {
      await markOnboardingDone();
    } catch (_) { /* 即使失败也关闭 */ }
    onClose();
  };

  if (loading || error || !shouldShow) return null;

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-indigo-900/95 via-purple-900/95 to-indigo-800/95 z-50 flex flex-col items-center justify-center p-8">
      {/* 右上 X */}
      <button
        onClick={onClose}
        className="absolute top-6 right-6 w-12 h-12 bg-white/10 rounded-full flex items-center justify-center text-white hover:bg-white/20"
        title="先关闭，下次再来"
      >
        <X className="w-6 h-6" />
      </button>

      {/* 喇叭图标 */}
      <Volume2 className="w-12 h-12 text-amber-300 mb-6 animate-pulse" />

      {/* 3 句话依次出现 */}
      <div className="w-full max-w-2xl space-y-6">
        {lines.slice(0, visibleCount).map((line, i) => (
          <div
            key={i}
            className="bg-white/10 backdrop-blur-md rounded-3xl p-6 transition-opacity duration-500"
          >
            <p className="text-white text-3xl leading-relaxed">{line}</p>
          </div>
        ))}
      </div>

      {/* 我听完了 */}
      {visibleCount >= 3 && (
        <button
          onClick={handleDone}
          disabled={marking}
          className="mt-10 px-12 py-5 bg-amber-400 hover:bg-amber-300 text-indigo-900 text-2xl font-bold rounded-3xl shadow-lg disabled:opacity-60"
        >
          {marking ? '稍候...' : '我听完了'}
        </button>
      )}
    </div>
  );
}
