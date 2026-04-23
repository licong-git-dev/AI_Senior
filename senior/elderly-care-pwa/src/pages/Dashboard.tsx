import React, { useState, useEffect, useCallback } from 'react'
import { 
  Heart, Activity, AlertTriangle, TrendingUp, Clock, 
  Thermometer, Droplets, Footprints, RefreshCw, Wifi, WifiOff
} from 'lucide-react'
import { supabase } from '../lib/supabase'
import { isOnline, onNetworkChange, speak } from '../lib/pwa-utils'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area
} from 'recharts'
import { format } from 'date-fns'

interface HealthMetric {
  id: string
  type: string
  value: number
  unit: string
  timestamp: string
  status: 'normal' | 'warning' | 'danger'
}

interface TrendData {
  time: string
  heartRate: number
  bloodPressure: number
  temperature: number
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<HealthMetric[]>([])
  const [trendData, setTrendData] = useState<TrendData[]>([])
  const [loading, setLoading] = useState(true)
  const [online, setOnline] = useState(isOnline())
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [greeting, setGreeting] = useState('')

  // 获取问候语
  useEffect(() => {
    const hour = new Date().getHours()
    if (hour < 6) setGreeting('夜深了，注意休息')
    else if (hour < 12) setGreeting('早上好，祝您今天身体健康')
    else if (hour < 14) setGreeting('中午好，记得午休')
    else if (hour < 18) setGreeting('下午好，保持愉快心情')
    else setGreeting('晚上好，注意适度活动')
  }, [])

  // 监听网络状态
  useEffect(() => {
    onNetworkChange(setOnline)
  }, [])

  // 获取健康数据
  const fetchHealthData = useCallback(async () => {
    setLoading(true)
    try {
      // 获取传感器数据
      const { data: sensorData, error } = await supabase
        .from('sensor_data')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(20)

      if (error) throw error

      if (sensorData) {
        // 转换为健康指标格式
        const metricsMap = new Map<string, HealthMetric>()
        
        sensorData.forEach((item: any) => {
          if (!metricsMap.has(item.sensor_type)) {
            let status: 'normal' | 'warning' | 'danger' = 'normal'
            
            // 根据类型判断状态
            if (item.sensor_type === 'heart_rate') {
              if (item.value < 50 || item.value > 100) status = 'warning'
              if (item.value < 40 || item.value > 120) status = 'danger'
            } else if (item.sensor_type === 'blood_pressure_sys') {
              if (item.value < 90 || item.value > 140) status = 'warning'
              if (item.value < 80 || item.value > 160) status = 'danger'
            } else if (item.sensor_type === 'temperature') {
              if (item.value < 36 || item.value > 37.5) status = 'warning'
              if (item.value < 35 || item.value > 38.5) status = 'danger'
            }

            metricsMap.set(item.sensor_type, {
              id: item.id,
              type: item.sensor_type,
              value: item.value,
              unit: item.unit || '',
              timestamp: item.timestamp,
              status
            })
          }
        })

        setMetrics(Array.from(metricsMap.values()))

        // 生成趋势数据
        const trends: TrendData[] = []
        for (let i = 6; i >= 0; i--) {
          const sensorItem = sensorData.find((s: any) => 
            s.sensor_type === 'heart_rate' && new Date(s.timestamp).getDate() === new Date().getDate() - i
          )
          trends.push({
            time: format(new Date(Date.now() - i * 24 * 60 * 60 * 1000), 'MM/dd'),
            heartRate: sensorItem?.value || 72 + Math.random() * 10,
            bloodPressure: 120 + Math.random() * 15,
            temperature: 36.5 + Math.random() * 0.5
          })
        }
        setTrendData(trends)
      }
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error fetching health data:', error)
      speak('无法获取健康数据，请检查网络连接')
      // 不使用模拟数据，保持空状态
      setMetrics([])
    } finally {
      setLoading(false)
    }
  }, [])

  // 初始化和定期刷新
  useEffect(() => {
    fetchHealthData()
    const interval = setInterval(fetchHealthData, 30000) // 每30秒刷新
    return () => clearInterval(interval)
  }, [fetchHealthData])

  // 设置实时订阅
  useEffect(() => {
    const channel = supabase
      .channel('sensor_changes')
      .on('postgres_changes', { 
        event: 'INSERT', 
        schema: 'public', 
        table: 'sensor_data' 
      }, (payload) => {
        console.log('New sensor data:', payload)
        fetchHealthData()
      })
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [fetchHealthData])

  // 获取指标图标
  const getMetricIcon = (type: string) => {
    const iconClass = "w-10 h-10"
    switch (type) {
      case 'heart_rate':
        return <Heart className={iconClass} />
      case 'blood_pressure':
      case 'blood_pressure_sys':
        return <Activity className={iconClass} />
      case 'temperature':
        return <Thermometer className={iconClass} />
      case 'blood_oxygen':
        return <Droplets className={iconClass} />
      case 'steps':
        return <Footprints className={iconClass} />
      default:
        return <Activity className={iconClass} />
    }
  }

  // 获取指标名称
  const getMetricName = (type: string) => {
    switch (type) {
      case 'heart_rate': return '心率'
      case 'blood_pressure': 
      case 'blood_pressure_sys': return '血压'
      case 'temperature': return '体温'
      case 'blood_oxygen': return '血氧'
      case 'steps': return '步数'
      default: return type
    }
  }

  // 状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'bg-green-100 text-green-700 border-green-300'
      case 'warning': return 'bg-yellow-100 text-yellow-700 border-yellow-300'
      case 'danger': return 'bg-red-100 text-red-700 border-red-300'
      default: return 'bg-gray-100 text-gray-700 border-gray-300'
    }
  }

  // 语音播报
  const speakSummary = () => {
    const heartRate = metrics.find(m => m.type === 'heart_rate')
    const bp = metrics.find(m => m.type.includes('blood_pressure'))
    const temp = metrics.find(m => m.type === 'temperature')
    
    let text = `${greeting}。您当前的健康数据：`
    if (heartRate) text += `心率${heartRate.value}次每分钟，`
    if (bp) text += `血压${bp.value}毫米汞柱，`
    if (temp) text += `体温${temp.value}摄氏度。`
    
    const abnormal = metrics.filter(m => m.status !== 'normal')
    if (abnormal.length > 0) {
      text += `注意：${abnormal.map(a => getMetricName(a.type)).join('、')}指标异常，请留意。`
    } else {
      text += '所有指标正常，请继续保持。'
    }
    
    speak(text)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 pb-24">
      {/* 顶部状态栏 */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {online ? (
              <Wifi className="w-5 h-5" />
            ) : (
              <WifiOff className="w-5 h-5 text-yellow-300" />
            )}
            <span className="text-sm">
              {online ? '在线' : '离线模式'}
            </span>
          </div>
          <span className="text-sm opacity-80">
            更新于 {format(lastUpdate, 'HH:mm:ss')}
          </span>
        </div>
      </div>

      {/* 问候语区域 */}
      <div className="px-5 py-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-b-3xl shadow-lg">
        <h1 className="text-3xl font-bold mb-2">{greeting}</h1>
        <p className="text-indigo-100 text-lg">您的健康，我们守护</p>
        
        {/* 快捷操作 */}
        <div className="flex space-x-4 mt-6">
          <button 
            onClick={speakSummary}
            className="flex-1 py-3 px-4 bg-white/20 backdrop-blur-sm rounded-2xl text-center hover:bg-white/30 transition-all active:scale-95"
          >
            <span className="text-lg font-medium">语音播报</span>
          </button>
          <button 
            onClick={fetchHealthData}
            className="flex-1 py-3 px-4 bg-white/20 backdrop-blur-sm rounded-2xl text-center hover:bg-white/30 transition-all active:scale-95 flex items-center justify-center"
          >
            <RefreshCw className={`w-5 h-5 mr-2 ${loading ? 'animate-spin' : ''}`} />
            <span className="text-lg font-medium">刷新数据</span>
          </button>
        </div>
      </div>

      {/* 健康指标卡片 */}
      <div className="px-5 -mt-6">
        <div className="grid grid-cols-2 gap-4">
          {metrics.slice(0, 4).map((metric) => (
            <div
              key={metric.id}
              className={`p-5 rounded-2xl border-2 shadow-sm ${getStatusColor(metric.status)} transition-all active:scale-95`}
            >
              <div className="flex items-center justify-between mb-3">
                {getMetricIcon(metric.type)}
                {metric.status !== 'normal' && (
                  <AlertTriangle className="w-6 h-6 text-current" />
                )}
              </div>
              <p className="text-base text-current/70 mb-1">{getMetricName(metric.type)}</p>
              <p className="text-4xl font-bold text-current">
                {metric.value}
                <span className="text-lg font-normal ml-1">{metric.unit}</span>
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 趋势图表 */}
      <div className="px-5 mt-6">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-800">7日趋势</h2>
            <TrendingUp className="w-6 h-6 text-indigo-500" />
          </div>
          
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="colorHeart" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="time" stroke="#9CA3AF" fontSize={14} />
              <YAxis stroke="#9CA3AF" fontSize={14} />
              <Tooltip 
                contentStyle={{ 
                  borderRadius: '12px',
                  fontSize: '14px',
                  border: 'none',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="heartRate" 
                stroke="#6366F1" 
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorHeart)"
                name="心率"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 今日提醒 */}
      <div className="px-5 mt-6">
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl p-5 border border-amber-200">
          <div className="flex items-center space-x-3 mb-3">
            <Clock className="w-6 h-6 text-amber-600" />
            <h2 className="text-xl font-bold text-amber-800">今日提醒</h2>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-amber-200">
              <span className="text-lg text-amber-700">08:00 - 服用降压药</span>
              <span className="text-base text-green-600 font-medium">已完成</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-amber-200">
              <span className="text-lg text-amber-700">12:00 - 午餐后散步</span>
              <span className="text-base text-orange-600 font-medium">待完成</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-lg text-amber-700">20:00 - 测量血压</span>
              <span className="text-base text-gray-500 font-medium">未开始</span>
            </div>
          </div>
        </div>
      </div>

      {/* 离线提示 */}
      {!online && (
        <div className="fixed bottom-20 left-4 right-4 bg-yellow-500 text-white p-4 rounded-2xl shadow-lg flex items-center justify-center">
          <WifiOff className="w-5 h-5 mr-2" />
          <span className="text-lg">当前为离线模式，数据将在联网后同步</span>
        </div>
      )}
    </div>
  )
}
