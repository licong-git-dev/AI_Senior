import { useState, useEffect } from 'react';
import { ArrowLeft, CheckCircle2, Clock, AlertCircle, Pill } from 'lucide-react';
import { getUserId, authFetch } from '../lib/api';

interface MedScheduleItem {
  medication_id: string;
  medication_name: string;
  dosage: string;
  medication_type: string;
  scheduled_time: string;
  scheduled_datetime: string;
  status: 'pending' | 'taken' | 'missed' | 'skipped';
  record_id: string | null;
  instructions: string | null;
  notes: string | null;
}

interface MedScheduleResponse {
  user_id: string;
  date: string;
  schedule: MedScheduleItem[];
  total_count: number;
  taken_count: number;
  pending_count: number;
}

interface MedicationPageProps {
  onBack: () => void;
}

async function fetchTodaySchedule(userId: string): Promise<MedScheduleResponse> {
  const resp = await authFetch(`/api/medication/schedule/today/${userId}`);
  if (!resp.ok) throw new Error('获取用药计划失败');
  return resp.json();
}

async function recordTaken(userId: string, medicationId: string, scheduledDatetime: string): Promise<void> {
  const params = new URLSearchParams({
    user_id: userId,
    medication_id: medicationId,
    scheduled_time: scheduledDatetime,
  });
  const resp = await authFetch(`/api/medication/records/take?${params}`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
  if (!resp.ok) throw new Error('记录服药失败');
}

const statusConfig = {
  pending: { label: '待服用', color: 'bg-amber-100 text-amber-700', icon: Clock },
  taken:   { label: '已服用', color: 'bg-green-100 text-green-700', icon: CheckCircle2 },
  missed:  { label: '已漏服', color: 'bg-red-100 text-red-700', icon: AlertCircle },
  skipped: { label: '已跳过', color: 'bg-gray-100 text-gray-500', icon: AlertCircle },
};

export default function MedicationPage({ onBack }: MedicationPageProps) {
  const [schedule, setSchedule] = useState<MedScheduleItem[]>([]);
  const [summary, setSummary] = useState<{ total: number; taken: number; pending: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [takingId, setTakingId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const userId = getUserId();

  const loadSchedule = async () => {
    try {
      const data = await fetchTodaySchedule(userId);
      setSchedule(data.schedule);
      setSummary({ total: data.total_count, taken: data.taken_count, pending: data.pending_count });
    } catch {
      setError('暂时无法加载用药计划，请稍后再试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedule();
  }, [userId]);

  const handleTake = async (item: MedScheduleItem) => {
    const key = item.medication_id + item.scheduled_time;
    setTakingId(key);
    try {
      await recordTaken(userId, item.medication_id, item.scheduled_datetime);
      // Optimistically update local state
      setSchedule(prev => prev.map(m =>
        m.medication_id === item.medication_id && m.scheduled_time === item.scheduled_time
          ? { ...m, status: 'taken' }
          : m
      ));
      setSummary(prev => prev ? { ...prev, taken: prev.taken + 1, pending: Math.max(0, prev.pending - 1) } : prev);
    } catch {
      setError('记录失败，请重试');
      setTimeout(() => setError(''), 3000);
    } finally {
      setTakingId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 text-xl">加载用药计划...</p>
        </div>
      </div>
    );
  }

  const now = new Date();
  const currentTimeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

  return (
    <div className="min-h-screen bg-gray-50 pb-10">
      {/* 顶部导航 */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 pt-12 pb-8 rounded-b-3xl">
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={onBack}
            className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center hover:bg-white/30 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold">今日用药</h1>
            <p className="text-indigo-200">按时服药，健康每一天</p>
          </div>
        </div>

        {/* 服药进度 */}
        {summary && (
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-3xl font-bold">{summary.total}</p>
              <p className="text-indigo-200 text-sm">今日总数</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-green-300">{summary.taken}</p>
              <p className="text-indigo-200 text-sm">已服用</p>
            </div>
            <div>
              <p className={`text-3xl font-bold ${summary.pending > 0 ? 'text-amber-300' : 'text-green-300'}`}>
                {summary.pending}
              </p>
              <p className="text-indigo-200 text-sm">待服用</p>
            </div>
          </div>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mx-6 mt-4 bg-red-50 border border-red-200 rounded-2xl px-4 py-3 text-red-600 text-base">
          {error}
        </div>
      )}

      {/* 用药列表 */}
      <div className="px-6 mt-6 space-y-4">
        {schedule.length === 0 ? (
          <div className="text-center py-16">
            <Pill className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-xl">今天没有用药计划</p>
            <p className="text-gray-400 text-base mt-2">如需添加，请联系家人设置</p>
          </div>
        ) : (
          schedule.map((item) => {
            const cfg = statusConfig[item.status] || statusConfig.pending;
            const StatusIcon = cfg.icon;
            const isPending = item.status === 'pending';
            const isPast = item.scheduled_time <= currentTimeStr;
            const takingKey = item.medication_id + item.scheduled_time;

            return (
              <div
                key={takingKey}
                className={`bg-white rounded-3xl shadow-sm p-5 border-2 transition-all ${
                  isPending && isPast ? 'border-amber-200' : 'border-transparent'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-2xl ${
                      item.status === 'taken' ? 'bg-green-100' :
                      item.status === 'missed' ? 'bg-red-100' : 'bg-indigo-100'
                    }`}>
                      💊
                    </div>
                    <div>
                      <p className="text-xl font-bold text-gray-800">{item.medication_name}</p>
                      <p className="text-gray-500 text-base">{item.dosage}</p>
                      {item.instructions && (
                        <p className="text-gray-400 text-sm mt-0.5">{item.instructions}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-gray-700">{item.scheduled_time}</p>
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium mt-1 ${cfg.color}`}>
                      <StatusIcon className="w-3 h-3" />
                      {cfg.label}
                    </span>
                  </div>
                </div>

                {/* 服药按钮 */}
                {isPending && (
                  <button
                    onClick={() => handleTake(item)}
                    disabled={takingId === takingKey}
                    className={`w-full mt-4 py-4 rounded-2xl text-xl font-bold transition-all active:scale-98 ${
                      isPast
                        ? 'bg-amber-500 hover:bg-amber-600 text-white'
                        : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                    } disabled:opacity-60`}
                  >
                    {takingId === takingKey ? '记录中...' : isPast ? '⚠️ 已到时间，点击确认服药' : '✓ 提前确认服药'}
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* 底部提示 */}
      {summary && summary.pending === 0 && summary.total > 0 && (
        <div className="mx-6 mt-6 bg-green-50 border border-green-200 rounded-2xl p-4 text-center">
          <p className="text-green-700 text-xl font-bold">🎉 今日用药全部完成！</p>
          <p className="text-green-600 text-base mt-1">按时服药，身体棒棒的</p>
        </div>
      )}
    </div>
  );
}
