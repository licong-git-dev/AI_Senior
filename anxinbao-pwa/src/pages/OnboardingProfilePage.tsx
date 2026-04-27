import { useState } from 'react';
import { ChevronRight, X } from 'lucide-react';
import { updateOnboardingProfile, type OnboardingProfile } from '../lib/api';

/**
 * 老人个性化字段引导页（r28 落地 Insight #11）
 *
 * 触发：家属登录后，URL ?onboarding=1 或检测到老人未填字段时跳转。
 * 5 字段（全选填，但越填得多 3 句话激活越准）：
 *   - family_name      老人姓
 *   - addressed_as     喜欢的称呼（妈/婆婆）
 *   - closest_child_name 最亲子女名（自己即可）
 *   - favorite_tv_show 喜欢的电视节目
 *   - health_focus     健康关注点
 *
 * 设计原则：
 *   - 全部选填，"跳过"按钮永远可用
 *   - 一屏一字段，避免一次填 5 个吓退家属
 *   - 完成时显示"3 句话预览"让家属看到效果
 */
interface Props {
  onDone: () => void;
}

const HEALTH_OPTIONS = ['高血压', '糖尿病', '睡眠', '关节', '其他'];

export default function OnboardingProfilePage({ onDone }: Props) {
  const [step, setStep] = useState(0); // 0..4
  const [profile, setProfile] = useState<OnboardingProfile>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const total = 5;

  const STEPS: { key: keyof OnboardingProfile; title: string; placeholder: string; example: string; }[] = [
    { key: 'family_name', title: '老人姓什么？', placeholder: '张/李/王', example: '比如"张"' },
    { key: 'addressed_as', title: '老人喜欢被怎么称呼？', placeholder: '妈/婆婆/爸/爷爷', example: '比如"妈"' },
    { key: 'closest_child_name', title: '老人最亲的子女叫什么？', placeholder: '小军/小红', example: '"小军" 用来让 AI 第一句话就提到您' },
    { key: 'favorite_tv_show', title: '老人爱看什么节目？', placeholder: '中央 1 套 19:00 / 楚剧', example: 'AI 会用这个开场聊天' },
    { key: 'health_focus', title: '老人最关注的健康事是？', placeholder: '高血压/糖尿病/睡眠/关节', example: 'AI 会带"我记得您说过…"勾子' },
  ];

  const cur = STEPS[step];
  const value = profile[cur.key] || '';

  const setValue = (v: string) => setProfile((p) => ({ ...p, [cur.key]: v }));

  const next = async () => {
    if (step < total - 1) {
      setStep(step + 1);
    } else {
      await save();
    }
  };

  const save = async () => {
    setSaving(true);
    setError('');
    try {
      await updateOnboardingProfile(profile);
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : '保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl p-6">
        {/* 顶部进度 + 跳过 */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs text-gray-400">{step + 1} / {total} · 帮 AI 更懂您父母</p>
          <button
            onClick={onDone}
            className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
          >
            稍后再说 <X className="w-3 h-3" />
          </button>
        </div>
        <div className="h-1 bg-gray-100 rounded-full mb-6">
          <div
            className="h-full bg-indigo-500 rounded-full transition-all"
            style={{ width: `${((step + 1) / total) * 100}%` }}
          />
        </div>

        {/* 标题 */}
        <h2 className="text-2xl font-bold text-gray-800 mb-1">{cur.title}</h2>
        <p className="text-sm text-gray-500 mb-6">{cur.example}</p>

        {/* 输入 */}
        {cur.key === 'health_focus' ? (
          <div className="grid grid-cols-2 gap-3 mb-8">
            {HEALTH_OPTIONS.map((opt) => (
              <button
                key={opt}
                onClick={() => setValue(opt)}
                className={`py-4 rounded-2xl text-base font-medium border-2 transition-all ${
                  value === opt ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-gray-200 text-gray-600'
                }`}
              >
                {opt}
              </button>
            ))}
          </div>
        ) : (
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={cur.placeholder}
            maxLength={50}
            className="w-full border-2 border-gray-200 rounded-2xl px-4 py-4 text-lg focus:border-indigo-400 focus:outline-none mb-8"
            autoFocus
          />
        )}

        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

        {/* 操作按钮 */}
        <div className="flex gap-3">
          {step > 0 && (
            <button
              onClick={() => setStep(step - 1)}
              className="flex-1 py-3 rounded-2xl border-2 border-gray-200 text-gray-600 font-medium"
            >
              上一步
            </button>
          )}
          <button
            onClick={next}
            disabled={saving}
            className="flex-1 py-3 rounded-2xl bg-indigo-500 hover:bg-indigo-600 text-white font-medium flex items-center justify-center gap-1 disabled:opacity-60"
          >
            {saving ? '保存中...' : step === total - 1 ? '完成' : '下一步'}
            {!saving && <ChevronRight className="w-4 h-4" />}
          </button>
        </div>

        <p className="text-xs text-gray-400 text-center mt-4">
          这 5 个字段决定老人首次打开时 AI 第一句话能否"击中"。全部选填，越准越好。
        </p>
      </div>
    </div>
  );
}
