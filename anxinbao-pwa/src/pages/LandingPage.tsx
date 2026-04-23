import { useState, useEffect } from 'react';
import { getSubscriptionPlans, isAuthenticated, startSubscriptionTrial, subscribeToPlan } from '../lib/api';
import type { SubscriptionPlan } from '../lib/api';
import {
  Heart,
  Shield,
  MessageCircle,
  Activity,
  Phone,
  Star,
  Clock,
  Users,
  Pill,
  AlertTriangle,
  Moon,
  Coffee,
  Check,
} from 'lucide-react';

interface LandingPageProps {
  onTryNow?: () => void;
  onOpenFamilyInvite?: () => void;
}

export default function LandingPage({ onTryNow, onOpenFamilyInvite }: LandingPageProps) {
  const [activeScene, setActiveScene] = useState(0);

  const handlePlanAction = async (planId: string) => {
    if (planId === 'free') {
      onTryNow?.();
      return;
    }

    if (!isAuthenticated()) {
      onTryNow?.();
      return;
    }

    try {
      setTrialLoadingPlanId(planId);
      const plan = plans.find((item) => item.id === planId);
      if (plan?.supportsTrial) {
        const result = await startSubscriptionTrial(planId);
        setTrialMessage(result.message || '试用已开启');
      } else {
        const result = await subscribeToPlan(planId);
        setTrialMessage(result.message || '订单已创建，请完成支付后开通会员');
      }
    } catch (error) {
      setTrialMessage(error instanceof Error ? error.message : '开通会员失败');
    } finally {
      setTrialLoadingPlanId(null);
    }
  };
  const [anxinScore] = useState(8);
  const [plans, setPlans] = useState<DisplayPlan[]>(fallbackPricingPlans);
  const [trialMessage, setTrialMessage] = useState<string | null>(null);
  const [trialLoadingPlanId, setTrialLoadingPlanId] = useState<string | null>(null);

  // 场景轮播
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveScene((prev) => (prev + 1) % scenes.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;

    getSubscriptionPlans()
      .then(({ plans: subscriptionPlans }) => {
        if (!cancelled) {
          const displayPlans = subscriptionPlans.filter(isLandingPlan).map(toDisplayPlan);
          setPlans(displayPlans.length > 0 ? displayPlans : fallbackPricingPlans);
        }
      })
      .catch(() => {
        if (!cancelled) setPlans(fallbackPricingPlans);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-white text-gray-800">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-orange-50 via-rose-50 to-purple-50 px-6 pt-16 pb-20">
        <div className="max-w-md mx-auto text-center">
          {/* Logo */}
          <div className="inline-flex items-center gap-2 bg-white/80 backdrop-blur-sm rounded-full px-4 py-2 mb-8 shadow-sm">
            <Heart className="w-5 h-5 text-rose-500" fill="currentColor" />
            <span className="font-bold text-lg text-gray-800">安心宝</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-3xl font-bold leading-tight mb-4 text-gray-900">
            你不在的时候
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-rose-500">
              安心宝用爸妈最熟悉的话
            </span>
            <br />
            陪着他们
          </h1>

          <p className="text-gray-500 text-base mb-8 leading-relaxed">
            方言AI陪伴 &times; 健康守护 &times; 子女安心
          </p>

          {/* CTA Button */}
          <button
            onClick={onTryNow}
            className="w-full max-w-xs bg-gradient-to-r from-orange-500 to-rose-500 text-white font-bold py-4 px-8 rounded-2xl text-lg shadow-lg shadow-orange-200 active:scale-95 transition-transform"
          >
            免费体验
          </button>
          <p className="text-sm text-gray-400 mt-3">每天不到一杯咖啡的钱，换爸妈整天的陪伴</p>
        </div>

        {/* Decorative Elements */}
        <div className="absolute top-10 left-5 w-20 h-20 bg-orange-200/30 rounded-full blur-2xl" />
        <div className="absolute bottom-10 right-5 w-32 h-32 bg-rose-200/30 rounded-full blur-3xl" />
      </section>

      {/* Pain Point Section */}
      <section className="px-6 py-16 bg-white">
        <div className="max-w-md mx-auto">
          <h2 className="text-2xl font-bold text-center mb-2">你有多久没回家了？</h2>
          <p className="text-center text-gray-400 mb-10">这些场景，是不是很熟悉</p>

          <div className="space-y-4">
            {painPoints.map((point, index) => (
              <div
                key={index}
                className="flex items-start gap-4 p-4 bg-gray-50 rounded-2xl"
              >
                <div className="flex-shrink-0 w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center">
                  <point.icon className="w-5 h-5 text-orange-500" />
                </div>
                <div>
                  <p className="font-medium text-gray-800">{point.title}</p>
                  <p className="text-sm text-gray-400 mt-1">{point.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Core Feature: Dialect AI */}
      <section className="px-6 py-16 bg-gradient-to-b from-orange-50 to-white">
        <div className="max-w-md mx-auto">
          <div className="text-center mb-10">
            <div className="inline-flex items-center bg-orange-100 text-orange-600 text-sm font-medium rounded-full px-4 py-1.5 mb-4">
              <Star className="w-4 h-4 mr-1.5" />
              核心卖点
            </div>
            <h2 className="text-2xl font-bold mb-2">会说方言的AI"孩子"</h2>
            <p className="text-gray-400">武汉话、鄂州话、普通话，爸妈听得懂的温暖</p>
          </div>

          {/* Scene Cards */}
          <div className="relative">
            {scenes.map((scene, index) => (
              <div
                key={index}
                className={`transition-all duration-500 ${
                  activeScene === index
                    ? 'opacity-100 translate-y-0'
                    : 'opacity-0 absolute inset-0 translate-y-4 pointer-events-none'
                }`}
              >
                <div className="bg-white rounded-3xl shadow-lg p-6 border border-gray-100">
                  <div className="flex items-center gap-2 mb-4">
                    <scene.icon className="w-5 h-5 text-orange-500" />
                    <span className="text-sm font-medium text-orange-500">{scene.tag}</span>
                    <span className="text-xs text-gray-300 ml-auto">{scene.time}</span>
                  </div>

                  {/* Chat Bubbles */}
                  <div className="space-y-3">
                    {scene.messages.map((msg, msgIndex) => (
                      <div
                        key={msgIndex}
                        className={`flex ${msg.role === 'ai' ? 'justify-start' : 'justify-end'}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                            msg.role === 'ai'
                              ? 'bg-gradient-to-r from-orange-50 to-rose-50 text-gray-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {msg.text}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Push Notification Preview */}
                  {scene.push && (
                    <div className="mt-4 bg-blue-50 rounded-xl px-4 py-3 flex items-start gap-2">
                      <Phone className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-blue-400 font-medium">子女手机推送</p>
                        <p className="text-sm text-blue-700 mt-1">{scene.push}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Scene Indicators */}
            <div className="flex justify-center gap-2 mt-6">
              {scenes.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setActiveScene(index)}
                  className={`h-2 rounded-full transition-all ${
                    activeScene === index ? 'w-6 bg-orange-500' : 'w-2 bg-gray-200'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Core Feature: Daily Report */}
      <section className="px-6 py-16 bg-white">
        <div className="max-w-md mx-auto">
          <div className="text-center mb-10">
            <div className="inline-flex items-center bg-emerald-100 text-emerald-600 text-sm font-medium rounded-full px-4 py-1.5 mb-4">
              <Activity className="w-4 h-4 mr-1.5" />
              今日爸妈
            </div>
            <h2 className="text-2xl font-bold mb-2">一打开就知道爸妈过得好不好</h2>
            <p className="text-gray-400">安心指数、情绪、健康、用药，一目了然</p>
          </div>

          {/* Mock Daily Report Card */}
          <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-3xl p-6 border border-emerald-100">
            <div className="flex items-center justify-between mb-5">
              <div>
                <p className="text-sm text-gray-400">今日爸妈 &middot; 3月3日</p>
                <p className="text-lg font-bold text-gray-800 mt-1">妈妈今天过得不错</p>
              </div>
              <div className="text-center">
                <div className="w-14 h-14 bg-emerald-500 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-emerald-200">
                  {anxinScore}
                </div>
                <p className="text-xs text-emerald-600 font-medium mt-1">很安心</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {reportItems.map((item, index) => (
                <div key={index} className="bg-white/80 rounded-xl p-3">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <span>{item.emoji}</span>
                    <span className="text-xs text-gray-400">{item.label}</span>
                  </div>
                  <p className="text-sm font-medium text-gray-700">{item.value}</p>
                </div>
              ))}
            </div>

            <div className="mt-4 bg-white/60 rounded-xl p-3">
              <p className="text-xs text-gray-400 mb-1.5">给你的建议</p>
              <p className="text-sm text-gray-600">妈妈今天提到了想你，有空给她打个电话吧</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="px-6 py-16 bg-gray-50">
        <div className="max-w-md mx-auto">
          <h2 className="text-2xl font-bold text-center mb-10">全方位守护</h2>

          <div className="grid grid-cols-2 gap-4">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-white rounded-2xl p-5 shadow-sm border border-gray-50"
              >
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${feature.bgColor}`}
                >
                  <feature.icon className={`w-5 h-5 ${feature.iconColor}`} />
                </div>
                <h3 className="font-bold text-gray-800 mb-1">{feature.title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="px-6 py-16 bg-white">
        <div className="max-w-md mx-auto">
          <h2 className="text-2xl font-bold text-center mb-2">为什么选安心宝？</h2>
          <p className="text-center text-gray-400 mb-10">和市面产品的对比</p>

          <div className="overflow-x-auto -mx-6 px-6">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className="text-left py-3 text-gray-400 font-normal">功能</th>
                  <th className="py-3 text-gray-400 font-normal">智能音箱</th>
                  <th className="py-3 text-gray-400 font-normal">手环</th>
                  <th className="py-3 text-orange-500 font-bold">安心宝</th>
                </tr>
              </thead>
              <tbody>
                {comparisonData.map((row, index) => (
                  <tr key={index} className="border-t border-gray-50">
                    <td className="py-3 text-gray-600">{row.feature}</td>
                    <td className="py-3 text-center">{row.speaker}</td>
                    <td className="py-3 text-center">{row.band}</td>
                    <td className="py-3 text-center font-medium text-orange-600">{row.anxinbao}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="px-6 py-16 bg-gradient-to-b from-orange-50 to-white">
        <div className="max-w-md mx-auto">
          <h2 className="text-2xl font-bold text-center mb-2">选择适合的方案</h2>
          <p className="text-center text-gray-400 mb-10">一杯咖啡的钱，换爸妈一整天的陪伴</p>

          {trialMessage && (
            <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
              {trialMessage}
            </div>
          )}

          <div className="space-y-4">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={`rounded-2xl p-5 border-2 transition-all ${
                  plan.recommended
                    ? 'border-orange-500 bg-gradient-to-r from-orange-50 to-rose-50 shadow-lg'
                    : 'border-gray-100 bg-white'
                }`}
              >
                {plan.recommended && (
                  <div className="inline-block bg-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full mb-3">
                    推荐
                  </div>
                )}
                <div className="flex items-end justify-between mb-3">
                  <div>
                    <h3 className="font-bold text-lg">{plan.name}</h3>
                    <p className="text-xs text-gray-400">{plan.desc}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-bold text-gray-800">&yen;{plan.price}</span>
                    <span className="text-sm text-gray-400">{plan.billingLabel}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  {plan.features.map((feat) => (
                    <div key={feat} className="flex items-center gap-2 text-sm text-gray-500">
                      <Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
                <button
                  onClick={() => handlePlanAction(plan.id)}
                  disabled={trialLoadingPlanId === plan.id}
                  className={`mt-5 w-full rounded-2xl py-3 text-sm font-bold transition-transform active:scale-95 disabled:opacity-60 ${
                    plan.recommended
                      ? 'bg-orange-500 text-white shadow-lg shadow-orange-100'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {trialLoadingPlanId === plan.id ? '处理中...' : plan.ctaLabel}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="px-6 py-20 bg-gradient-to-br from-orange-500 to-rose-500 text-white text-center">
        <div className="max-w-md mx-auto">
          <h2 className="text-2xl font-bold mb-3">今天，让爸妈不再孤单</h2>
          <p className="text-orange-100 mb-8">
            用他们最熟悉的方言，给他们最温暖的陪伴
          </p>
          <div className="space-y-3">
            <button
              onClick={onTryNow}
              className="w-full bg-white text-orange-600 font-bold py-4 px-8 rounded-2xl text-lg shadow-lg active:scale-95 transition-transform"
            >
              立即开始
            </button>
            <button
              onClick={onOpenFamilyInvite}
              className="w-full border border-white/40 bg-white/10 text-white font-bold py-4 px-8 rounded-2xl text-lg active:scale-95 transition-transform"
            >
              我是家属，去输入邀请码
            </button>
          </div>
          <p className="text-sm text-orange-200 mt-4">基础版支持7天免费试用，无需绑定银行卡</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-10 bg-gray-900 text-gray-400 text-center text-sm">
        <div className="max-w-md mx-auto">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Heart className="w-4 h-4 text-rose-400" fill="currentColor" />
            <span className="font-bold text-white">安心宝</span>
          </div>
          <p>方言AI陪伴 &times; 健康守护 &times; 子女安心</p>
          <p className="mt-2 text-gray-500">&copy; 2026 安心宝科技 All Rights Reserved</p>
        </div>
      </footer>
    </div>
  );
}

// ==================== Data ====================

const painPoints = [
  {
    icon: Clock,
    title: '"上次回家是三个月前了"',
    desc: '工作太忙，每次想回去又抽不出时间',
  },
  {
    icon: Phone,
    title: '"视频通话也就每周一次"',
    desc: '爸妈总说"挺好的别担心"，但你真的放心吗？',
  },
  {
    icon: Moon,
    title: '"妈每天晚饭后一个人坐到睡觉"',
    desc: '18:00到21:00，是最孤独的三个小时',
  },
  {
    icon: AlertTriangle,
    title: '"万一夜里摔了都没人知道"',
    desc: '高血压、头晕、起夜跌倒……不敢想',
  },
];

const scenes = [
  {
    tag: '晚饭后的陪伴',
    time: '每天 18:30',
    icon: Coffee,
    messages: [
      { role: 'ai', text: '张妈妈，今天的晚饭恰了么？外头降温了，记得加件衣裳。' },
      { role: 'user', text: '恰了恰了，今天搞了个排骨藕汤。' },
      { role: 'ai', text: '排骨藕汤好啊！藕汤对血管好，您这个血压正好合适喝。' },
    ],
    push: '妈妈今天情绪不错，聊了晚饭和天气，晚8点已按时服药。',
  },
  {
    tag: '身体不适时的守护',
    time: '凌晨 3:12',
    icon: Shield,
    messages: [
      { role: 'user', text: '安心宝，我头有点发昏。' },
      { role: 'ai', text: '张妈妈莫急，先坐下来歇一哈。您血压最近偏高，我帮您量一下好不好？' },
      { role: 'ai', text: '血压有点高，我先帮您通知张明，您先喝杯温水休息。' },
    ],
    push: '妈妈凌晨3:12头晕，血压152/95，已引导休息，请关注。',
  },
  {
    tag: '想念家人时',
    time: '晚上 20:15',
    icon: Heart,
    messages: [
      { role: 'user', text: '今天看到隔壁孙子来看她奶奶了……' },
      { role: 'ai', text: '张妈妈，想小明了是不是？他在深圳也想着您嘞。要不要我帮您跟他打个电话？' },
      { role: 'user', text: '算了，他忙，莫打扰他。' },
      { role: 'ai', text: '小明不会觉得麻烦的。不过现在我陪您聊聊也蛮好，今天邻居王阿姨过得怎么样？' },
    ],
    push: '妈妈今天有些想你，情绪略低落，建议近期打个电话。',
  },
];

const reportItems = [
  { emoji: '😊', label: '情绪', value: '开心（聊了广场舞）' },
  { emoji: '💊', label: '用药', value: '早晚准时服药 ✓' },
  { emoji: '🩺', label: '血压', value: '135/85 正常' },
  { emoji: '🗣️', label: '聊天', value: '15条对话，3个话题' },
  { emoji: '🚶', label: '活动', value: '散步30分钟' },
  { emoji: '💤', label: '睡眠', value: '22:30-6:40' },
];

const features = [
  {
    icon: MessageCircle,
    title: '方言对话',
    desc: '武汉话/鄂州话/普通话，爸妈零学习成本',
    bgColor: 'bg-orange-100',
    iconColor: 'text-orange-500',
  },
  {
    icon: Heart,
    title: '情感陪伴',
    desc: '识别孤独/焦虑/开心，用乡音温暖回应',
    bgColor: 'bg-rose-100',
    iconColor: 'text-rose-500',
  },
  {
    icon: Activity,
    title: '安心日报',
    desc: '每天推送爸妈状态，安心指数一目了然',
    bgColor: 'bg-emerald-100',
    iconColor: 'text-emerald-500',
  },
  {
    icon: Pill,
    title: '用药提醒',
    desc: '方言提醒按时服药，不再漏服',
    bgColor: 'bg-blue-100',
    iconColor: 'text-blue-500',
  },
  {
    icon: Shield,
    title: '一键SOS',
    desc: '紧急求助+跌倒检测，自动通知家人',
    bgColor: 'bg-red-100',
    iconColor: 'text-red-500',
  },
  {
    icon: Users,
    title: '家庭守护',
    desc: '多个子女共同监护，分担关心',
    bgColor: 'bg-purple-100',
    iconColor: 'text-purple-500',
  },
];

const comparisonData = [
  { feature: '方言对话', speaker: '❌', band: '❌', anxinbao: '✅' },
  { feature: '情感陪伴', speaker: '❌', band: '❌', anxinbao: '✅' },
  { feature: '健康建议', speaker: '❌', band: '⚠️', anxinbao: '✅' },
  { feature: '子女日报', speaker: '❌', band: '❌', anxinbao: '✅' },
  { feature: '紧急响应', speaker: '❌', band: '⚠️', anxinbao: '✅' },
  { feature: '学习成本', speaker: '高', band: '低', anxinbao: '极低' },
];

interface DisplayPlan {
  id: string;
  name: string;
  desc: string;
  price: number;
  billingLabel: string;
  ctaLabel: string;
  recommended: boolean;
  supportsTrial: boolean;
  features: string[];
}

const LANDING_PLAN_IDS = ['free', 'basic_monthly', 'premium_monthly'];

function isLandingPlan(plan: SubscriptionPlan): boolean {
  return LANDING_PLAN_IDS.includes(plan.plan_id);
}

function toDisplayPlan(plan: SubscriptionPlan): DisplayPlan {
  return {
    id: plan.plan_id,
    name: plan.name.replace(/ - 月付$/, '').replace(/ - 年付$/, ''),
    desc: plan.description,
    price: plan.price,
    billingLabel: plan.billing_cycle === 'yearly' ? '/年' : '/月',
    ctaLabel: plan.price === 0 ? '免费开始' : plan.trial_days > 0 ? `开启${plan.trial_days}天试用` : '立即开通',
    recommended: plan.is_popular || plan.plan_id === 'basic_monthly',
    supportsTrial: plan.trial_days > 0,
    features: plan.benefits.slice(0, 5).map((benefit) => benefit.value ? `${benefit.name}（${benefit.value}）` : benefit.name),
  };
}

const fallbackPricingPlans: DisplayPlan[] = [
  {
    id: 'free',
    name: '免费版',
    desc: '体验核心功能',
    price: 0,
    billingLabel: '/月',
    ctaLabel: '免费开始',
    recommended: false,
    supportsTrial: false,
    features: ['每日3次方言对话', '基础健康记录', '单人监护'],
  },
  {
    id: 'basic_monthly',
    name: '安心版',
    desc: '日常陪伴首选',
    price: 29.9,
    billingLabel: '/月',
    ctaLabel: '开启7天试用',
    recommended: true,
    supportsTrial: true,
    features: ['无限方言对话', '每日安心日报推送', '用药提醒', '情绪识别', '家庭多人监护'],
  },
  {
    id: 'premium_monthly',
    name: '守护版',
    desc: '全面健康守护',
    price: 59.9,
    billingLabel: '/月',
    ctaLabel: '立即开通',
    recommended: false,
    supportsTrial: false,
    features: ['安心版全部功能', 'SOS紧急响应', '实时健康监测', '视频通话', '专属客服'],
  },
];
