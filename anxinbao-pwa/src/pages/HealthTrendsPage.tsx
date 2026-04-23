import { useState, useEffect, useCallback } from 'react';
import { format } from 'date-fns';
import {
  TrendingUp,
  Heart,
  Droplets,
  Activity,
  Scale,
  ChevronLeft,
  Calendar
} from 'lucide-react';
import { getHealthRecords, getUserId } from '../lib/api';

interface HealthTrendsPageProps {
  userId?: string;
  onBack?: () => void;
}

interface HealthRecord {
  date: string;
  value: number | { systolic: number; diastolic: number };
}

interface HealthData {
  bloodPressure: HealthRecord[];
  heartRate: HealthRecord[];
  bloodSugar: HealthRecord[];
  weight: HealthRecord[];
  temperature: HealthRecord[];
}

export default function HealthTrendsPage({ userId, onBack }: HealthTrendsPageProps) {
  const [activeTab, setActiveTab] = useState<'bloodPressure' | 'heartRate' | 'bloodSugar' | 'weight'>('bloodPressure');
  const [timeRange, setTimeRange] = useState<7 | 30>(7);
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 从API获取真实数据
  const fetchRealData = useCallback(async (): Promise<HealthData | null> => {
    const uid = userId || getUserId();
    try {
      const [bpRes, hrRes, bsRes, wtRes] = await Promise.all([
        getHealthRecords(uid, 'blood_pressure', timeRange),
        getHealthRecords(uid, 'heart_rate', timeRange),
        getHealthRecords(uid, 'blood_sugar', timeRange),
        getHealthRecords(uid, 'weight', timeRange),
      ]);

      // 仅当至少有一种数据类型返回记录时认为API有效
      if (bpRes.total + hrRes.total + bsRes.total + wtRes.total === 0) {
        return null;
      }

      const toDate = (iso: string) => format(new Date(iso), 'MM-dd');

      return {
        bloodPressure: bpRes.records.map(r => {
          const v = r.value as unknown as { systolic?: number; diastolic?: number };
          return {
            date: toDate(r.measured_at),
            value: { systolic: v?.systolic ?? 120, diastolic: v?.diastolic ?? 80 }
          };
        }),
        heartRate: hrRes.records.map(r => {
          const v = r.value as unknown as { bpm?: number };
          return {
            date: toDate(r.measured_at),
            value: v?.bpm ?? 0
          };
        }),
        bloodSugar: bsRes.records.map(r => {
          const v = r.value as unknown as { value?: number };
          return {
            date: toDate(r.measured_at),
            value: v?.value ?? 0
          };
        }),
        weight: wtRes.records.map(r => {
          const v = r.value as unknown as { kg?: number };
          return {
            date: toDate(r.measured_at),
            value: v?.kg ?? 0
          };
        }),
        temperature: [],
      };
    } catch {
      return null;
    }
  }, [userId, timeRange]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetchRealData().then(data => {
      if (cancelled) return;
      if (data) {
        setHealthData(data);
        setError(null);
      } else {
        setHealthData(null);
        setError('暂时没有可展示的健康趋势数据，请先记录健康数据后再查看。');
      }
      setLoading(false);
    });

    return () => { cancelled = true; };
  }, [fetchRealData]);

  // 简单的柱状图组件
  const BarChart = ({ data, color, unit, getLabel }: {
    data: HealthRecord[];
    color: string;
    unit: string;
    getLabel: (value: number | { systolic: number; diastolic: number }) => string;
  }) => {
    const values = data.map(d => {
      if (typeof d.value === 'number') return d.value;
      return d.value.systolic;
    });
    const maxValue = Math.max(...values) * 1.2;

    return (
      <div className="bg-white rounded-2xl p-4 shadow-sm">
        <div className="flex items-end justify-between h-48 gap-1">
          {data.map((item, index) => {
            const value = typeof item.value === 'number' ? item.value : item.value.systolic;
            const height = (value / maxValue) * 100;

            return (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div className="w-full flex flex-col items-center justify-end h-36">
                  <span className="text-xs text-gray-600 mb-1">
                    {getLabel(item.value)}
                  </span>
                  <div
                    className={`w-full max-w-8 rounded-t-lg ${color} transition-all duration-300`}
                    style={{ height: `${height}%` }}
                  />
                </div>
                <span className="text-xs text-gray-400 mt-2">{item.date}</span>
              </div>
            );
          })}
        </div>
        <div className="text-center mt-4 text-sm text-gray-500">
          单位: {unit}
        </div>
      </div>
    );
  };

  // 血压特殊图表
  const BloodPressureChart = ({ data }: { data: HealthRecord[] }) => {
    return (
      <div className="bg-white rounded-2xl p-4 shadow-sm">
        <div className="space-y-3">
          {data.slice(-7).map((item, index) => {
            const bp = item.value as { systolic: number; diastolic: number };
            const isHigh = bp.systolic >= 140 || bp.diastolic >= 90;
            const isLow = bp.systolic < 90 || bp.diastolic < 60;

            return (
              <div key={index} className="flex items-center gap-4">
                <span className="text-sm text-gray-500 w-12">{item.date}</span>
                <div className="flex-1 flex items-center gap-2">
                  <div className="flex-1 bg-gray-100 rounded-full h-6 relative overflow-hidden">
                    <div
                      className={`absolute left-0 top-0 h-full rounded-full ${
                        isHigh ? 'bg-red-400' : isLow ? 'bg-yellow-400' : 'bg-green-400'
                      }`}
                      style={{ width: `${(bp.systolic / 180) * 100}%` }}
                    />
                    <div
                      className={`absolute left-0 top-0 h-full rounded-full ${
                        isHigh ? 'bg-red-600' : isLow ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${(bp.diastolic / 180) * 100}%` }}
                    />
                  </div>
                  <span className={`text-sm font-medium w-20 text-right ${
                    isHigh ? 'text-red-600' : isLow ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    {bp.systolic}/{bp.diastolic}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex justify-center gap-6 mt-4 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-green-500" /> 正常
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-yellow-500" /> 偏低
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-500" /> 偏高
          </span>
        </div>
      </div>
    );
  };

  const tabs = [
    { key: 'bloodPressure', label: '血压', icon: Heart, color: 'text-red-500' },
    { key: 'heartRate', label: '心率', icon: Activity, color: 'text-pink-500' },
    { key: 'bloodSugar', label: '血糖', icon: Droplets, color: 'text-blue-500' },
    { key: 'weight', label: '体重', icon: Scale, color: 'text-purple-500' },
  ] as const;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">加载健康数据中...</p>
        </div>
      </div>
    );
  }

  if (error || !healthData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="max-w-sm rounded-3xl bg-white p-8 text-center shadow-sm">
          <TrendingUp className="mx-auto mb-4 h-12 w-12 text-indigo-400" />
          <h2 className="mb-2 text-xl font-bold text-gray-800">暂无健康趋势数据</h2>
          <p className="text-sm leading-6 text-gray-500">{error ?? '请先录入健康数据后再查看趋势。'}</p>
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
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <TrendingUp className="w-7 h-7" />
              健康趋势
            </h1>
            <p className="text-indigo-200 text-sm">查看历史健康数据变化</p>
          </div>
        </div>

        {/* 时间范围选择 */}
        <div className="flex gap-2">
          <button
            onClick={() => setTimeRange(7)}
            className={`px-4 py-2 rounded-full text-sm transition-all ${
              timeRange === 7
                ? 'bg-white text-indigo-600 font-medium'
                : 'bg-white/20 text-white'
            }`}
          >
            <Calendar className="w-4 h-4 inline mr-1" />
            近7天
          </button>
          <button
            onClick={() => setTimeRange(30)}
            className={`px-4 py-2 rounded-full text-sm transition-all ${
              timeRange === 30
                ? 'bg-white text-indigo-600 font-medium'
                : 'bg-white/20 text-white'
            }`}
          >
            <Calendar className="w-4 h-4 inline mr-1" />
            近30天
          </button>
        </div>
      </div>

      {/* 数据类型切换 */}
      <div className="px-4 -mt-4">
        <div className="bg-white rounded-2xl shadow-lg p-2 flex gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 py-3 rounded-xl flex flex-col items-center gap-1 transition-all ${
                activeTab === tab.key
                  ? 'bg-indigo-50 text-indigo-600'
                  : 'text-gray-500'
              }`}
            >
              <tab.icon className={`w-5 h-5 ${activeTab === tab.key ? tab.color : ''}`} />
              <span className="text-xs">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 图表区域 */}
      <div className="px-4 mt-6">
        {activeTab === 'bloodPressure' && healthData && (
          <>
            <h2 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
              <Heart className="w-5 h-5 text-red-500" />
              血压变化 (mmHg)
            </h2>
            <BloodPressureChart data={healthData.bloodPressure} />
            <div className="mt-4 bg-red-50 rounded-2xl p-4">
              <h3 className="font-medium text-red-800 mb-2">健康提示</h3>
              <p className="text-sm text-red-600">
                正常血压范围: 收缩压 90-140 mmHg，舒张压 60-90 mmHg。
                建议每天早晚各测量一次，保持规律作息。
              </p>
            </div>
          </>
        )}

        {activeTab === 'heartRate' && healthData && (
          <>
            <h2 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
              <Activity className="w-5 h-5 text-pink-500" />
              心率变化 (次/分钟)
            </h2>
            <BarChart
              data={healthData.heartRate}
              color="bg-pink-400"
              unit="次/分钟"
              getLabel={(v) => String(v)}
            />
            <div className="mt-4 bg-pink-50 rounded-2xl p-4">
              <h3 className="font-medium text-pink-800 mb-2">健康提示</h3>
              <p className="text-sm text-pink-600">
                静息心率正常范围: 60-100 次/分钟。
                心率过快或过慢都需要注意，建议适当运动保持心脏健康。
              </p>
            </div>
          </>
        )}

        {activeTab === 'bloodSugar' && healthData && (
          <>
            <h2 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
              <Droplets className="w-5 h-5 text-blue-500" />
              血糖变化 (mmol/L)
            </h2>
            <BarChart
              data={healthData.bloodSugar}
              color="bg-blue-400"
              unit="mmol/L"
              getLabel={(v) => String(v)}
            />
            <div className="mt-4 bg-blue-50 rounded-2xl p-4">
              <h3 className="font-medium text-blue-800 mb-2">健康提示</h3>
              <p className="text-sm text-blue-600">
                空腹血糖正常范围: 3.9-6.1 mmol/L。
                餐后2小时血糖应低于 7.8 mmol/L。注意控制饮食，少吃甜食。
              </p>
            </div>
          </>
        )}

        {activeTab === 'weight' && healthData && (
          <>
            <h2 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
              <Scale className="w-5 h-5 text-purple-500" />
              体重变化 (kg)
            </h2>
            <BarChart
              data={healthData.weight}
              color="bg-purple-400"
              unit="kg"
              getLabel={(v) => String(v)}
            />
            <div className="mt-4 bg-purple-50 rounded-2xl p-4">
              <h3 className="font-medium text-purple-800 mb-2">健康提示</h3>
              <p className="text-sm text-purple-600">
                保持体重稳定很重要。突然的体重变化可能提示健康问题。
                建议每周测量1-2次，最好在早晨空腹时测量。
              </p>
            </div>
          </>
        )}
      </div>

      {/* 数据统计 */}
      <div className="px-4 mt-6">
        <h2 className="text-lg font-bold text-gray-800 mb-3">数据统计</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl p-4 shadow-sm">
            <p className="text-sm text-gray-500">测量周期</p>
            <p className="text-2xl font-bold text-indigo-600">{timeRange}</p>
            <p className="text-xs text-gray-400">近{timeRange}天</p>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow-sm">
            <p className="text-sm text-gray-500">数据来源</p>
            <p className="text-2xl font-bold text-green-600">实时</p>
            <p className="text-xs text-gray-400">来自服务器</p>
          </div>
        </div>
      </div>
    </div>
  );
}
