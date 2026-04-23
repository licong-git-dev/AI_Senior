import React, { useState, useEffect, useCallback } from 'react'
import { 
  Activity, Heart, Thermometer, Droplets, TrendingUp,
  AlertTriangle, RefreshCw, Clock, CheckCircle, Filter
} from 'lucide-react'
import { supabase, SensorData, HealthAlert } from '../lib/supabase'
import { speak, showNotification, vibrate } from '../lib/pwa-utils'
import { format } from 'date-fns'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'

interface MonitorData {
  heartRate: number[]
  bloodPressure: { sys: number; dia: number }[]
  temperature: number[]
  bloodOxygen: number[]
  timestamps: string[]
}

export default function Monitor() {
  const [data, setData] = useState<MonitorData>({
    heartRate: [],
    bloodPressure: [],
    temperature: [],
    bloodOxygen: [],
    timestamps: []
  })
  const [alerts, setAlerts] = useState<HealthAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedMetric, setSelectedMetric] = useState<'heartRate' | 'bloodPressure' | 'temperature' | 'bloodOxygen'>('heartRate')
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('24h')

  // 获取监测数据
  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      // 计算时间范围
      const now = new Date()
      let startTime = new Date()
      switch (timeRange) {
        case '1h':
          startTime.setHours(now.getHours() - 1)
          break
        case '6h':
          startTime.setHours(now.getHours() - 6)
          break
        case '24h':
          startTime.setDate(now.getDate() - 1)
          break
        case '7d':
          startTime.setDate(now.getDate() - 7)
          break
      }

      // 获取传感器数据
      const { data: sensorData, error: sensorError } = await supabase
        .from('sensor_data')
        .select('*')
        .gte('timestamp', startTime.toISOString())
        .order('timestamp', { ascending: true })

      if (sensorError) throw sensorError

      // 整理数据
      const heartRates: number[] = []
      const bpSys: number[] = []
      const bpDia: number[] = []
      const temps: number[] = []
      const oxygen: number[] = []
      const times: string[] = []

      sensorData?.forEach((item: any) => {
        if (item.sensor_type === 'heart_rate') {
          heartRates.push(item.value)
          times.push(format(new Date(item.timestamp), 'HH:mm'))
        } else if (item.sensor_type === 'blood_pressure_sys') {
          bpSys.push(item.value)
        } else if (item.sensor_type === 'blood_pressure_dia') {
          bpDia.push(item.value)
        } else if (item.sensor_type === 'temperature') {
          temps.push(item.value)
        } else if (item.sensor_type === 'blood_oxygen') {
          oxygen.push(item.value)
        }
      })

      // 组合血压数据
      const bloodPressure = bpSys.map((sys, i) => ({
        sys,
        dia: bpDia[i] || 80
      }))

      setData({
        heartRate: heartRates,
        bloodPressure,
        temperature: temps,
        bloodOxygen: oxygen,
        timestamps: times
      })

      // 获取告警数据
      const { data: alertData, error: alertError } = await supabase
        .from('health_alerts')
        .select('*')
        .eq('resolved', false)
        .order('created_at', { ascending: false })
        .limit(5)

      if (!alertError && alertData) {
        setAlerts(alertData)
        
        // 如果有高危告警，进行语音提醒
        const criticalAlerts = alertData.filter(a => a.severity === 'critical' || a.severity === 'high')
        if (criticalAlerts.length > 0) {
          vibrate([300, 100, 300])
          speak(`注意：有${criticalAlerts.length}条重要健康告警需要关注`)
        }
      }
    } catch (error) {
      console.error('Fetch monitor data error:', error)
    } finally {
      setLoading(false)
    }
  }, [timeRange])

  // 初始化和刷新
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 60000) // 每分钟刷新
    return () => clearInterval(interval)
  }, [fetchData])

  // 实时订阅
  useEffect(() => {
    const channel = supabase
      .channel('monitor_changes')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'sensor_data'
      }, () => {
        fetchData()
      })
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'health_alerts'
      }, (payload) => {
        if (payload.eventType === 'INSERT') {
          const newAlert = payload.new as HealthAlert
          showNotification('新的健康告警', {
            body: `${newAlert.indicator_name}: ${newAlert.risk_assessment}`,
            requireInteraction: true
          })
        }
        fetchData()
      })
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [fetchData])

  // 获取图表数据
  const getChartData = () => {
    switch (selectedMetric) {
      case 'heartRate':
        return data.heartRate.map((value, i) => ({
          time: data.timestamps[i] || `${i}`,
          value,
          name: '心率'
        }))
      case 'bloodPressure':
        return data.bloodPressure.map((bp, i) => ({
          time: data.timestamps[i] || `${i}`,
          sys: bp.sys,
          dia: bp.dia,
          name: '血压'
        }))
      case 'temperature':
        return data.temperature.map((value, i) => ({
          time: data.timestamps[i] || `${i}`,
          value,
          name: '体温'
        }))
      case 'bloodOxygen':
        return data.bloodOxygen.map((value, i) => ({
          time: data.timestamps[i] || `${i}`,
          value,
          name: '血氧'
        }))
      default:
        return []
    }
  }

  // 解决告警
  const resolveAlert = async (alertId: string) => {
    try {
      await supabase
        .from('health_alerts')
        .update({ resolved: true })
        .eq('id', alertId)
      
      setAlerts(prev => prev.filter(a => a.id !== alertId))
      speak('告警已处理')
    } catch (error) {
      console.error('Resolve alert error:', error)
    }
  }

  // 告警严重程度颜色
  const getAlertColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300'
      default: return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const metricButtons = [
    { key: 'heartRate', label: '心率', icon: Heart, color: 'from-red-500 to-pink-500' },
    { key: 'bloodPressure', label: '血压', icon: Activity, color: 'from-blue-500 to-indigo-500' },
    { key: 'temperature', label: '体温', icon: Thermometer, color: 'from-orange-500 to-amber-500' },
    { key: 'bloodOxygen', label: '血氧', icon: Droplets, color: 'from-cyan-500 to-teal-500' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 pb-24">
      {/* 顶部标题 */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-5 py-6 rounded-b-3xl shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Activity className="w-8 h-8" />
            <h1 className="text-2xl font-bold">健康监测</h1>
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="p-2 bg-white/20 rounded-xl hover:bg-white/30 transition-colors active:scale-95"
          >
            <RefreshCw className={`w-6 h-6 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        
        {/* 时间范围选择 */}
        <div className="flex space-x-2">
          {[
            { key: '1h', label: '1小时' },
            { key: '6h', label: '6小时' },
            { key: '24h', label: '24小时' },
            { key: '7d', label: '7天' }
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => setTimeRange(item.key as any)}
              className={`flex-1 py-2 rounded-xl text-base font-medium transition-all ${
                timeRange === item.key
                  ? 'bg-white text-indigo-600'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* 指标选择 */}
      <div className="px-5 mt-6">
        <div className="grid grid-cols-4 gap-3">
          {metricButtons.map(({ key, label, icon: Icon, color }) => (
            <button
              key={key}
              onClick={() => setSelectedMetric(key as any)}
              className={`p-3 rounded-2xl flex flex-col items-center transition-all active:scale-95 ${
                selectedMetric === key
                  ? `bg-gradient-to-br ${color} text-white shadow-lg`
                  : 'bg-white text-gray-600 border border-gray-200'
              }`}
            >
              <Icon className="w-7 h-7 mb-1" />
              <span className="text-sm font-medium">{label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 图表区域 */}
      <div className="px-5 mt-6">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-800">
              {metricButtons.find(m => m.key === selectedMetric)?.label}趋势
            </h2>
            <TrendingUp className="w-6 h-6 text-indigo-500" />
          </div>
          
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={getChartData()}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="time" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{
                  borderRadius: '12px',
                  fontSize: '14px',
                  border: 'none',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              {selectedMetric === 'bloodPressure' ? (
                <>
                  <Line type="monotone" dataKey="sys" stroke="#6366F1" strokeWidth={2} dot={false} name="收缩压" />
                  <Line type="monotone" dataKey="dia" stroke="#A855F7" strokeWidth={2} dot={false} name="舒张压" />
                </>
              ) : (
                <Line type="monotone" dataKey="value" stroke="#6366F1" strokeWidth={3} dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>

          {/* 数据统计 */}
          <div className="mt-4 grid grid-cols-3 gap-3">
            {selectedMetric !== 'bloodPressure' ? (
              <>
                <div className="bg-green-50 p-3 rounded-xl text-center">
                  <p className="text-sm text-green-600">最低值</p>
                  <p className="text-lg font-bold text-green-700">
                    {Math.min(...(data[selectedMetric] as number[]), 0).toFixed(1)}
                  </p>
                </div>
                <div className="bg-blue-50 p-3 rounded-xl text-center">
                  <p className="text-sm text-blue-600">平均值</p>
                  <p className="text-lg font-bold text-blue-700">
                    {((data[selectedMetric] as number[]).reduce((a, b) => a + b, 0) / (data[selectedMetric] as number[]).length || 0).toFixed(1)}
                  </p>
                </div>
                <div className="bg-orange-50 p-3 rounded-xl text-center">
                  <p className="text-sm text-orange-600">最高值</p>
                  <p className="text-lg font-bold text-orange-700">
                    {Math.max(...(data[selectedMetric] as number[]), 0).toFixed(1)}
                  </p>
                </div>
              </>
            ) : (
              <>
                <div className="bg-blue-50 p-3 rounded-xl text-center">
                  <p className="text-sm text-blue-600">平均收缩压</p>
                  <p className="text-lg font-bold text-blue-700">
                    {(data.bloodPressure.reduce((a, b) => a + b.sys, 0) / data.bloodPressure.length || 0).toFixed(0)}
                  </p>
                </div>
                <div className="bg-purple-50 p-3 rounded-xl text-center">
                  <p className="text-sm text-purple-600">平均舒张压</p>
                  <p className="text-lg font-bold text-purple-700">
                    {(data.bloodPressure.reduce((a, b) => a + b.dia, 0) / data.bloodPressure.length || 0).toFixed(0)}
                  </p>
                </div>
                <div className="bg-green-50 p-3 rounded-xl text-center">
                  <p className="text-sm text-green-600">数据条数</p>
                  <p className="text-lg font-bold text-green-700">{data.bloodPressure.length}</p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 健康告警 */}
      <div className="px-5 mt-6">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center space-x-2 mb-4">
            <AlertTriangle className="w-6 h-6 text-red-500" />
            <h2 className="text-xl font-bold text-gray-800">健康告警</h2>
            {alerts.length > 0 && (
              <span className="bg-red-500 text-white text-sm px-2 py-0.5 rounded-full">
                {alerts.length}
              </span>
            )}
          </div>

          {alerts.length === 0 ? (
            <div className="flex flex-col items-center py-8">
              <CheckCircle className="w-16 h-16 text-green-400 mb-3" />
              <p className="text-lg text-gray-600">目前没有健康告警</p>
              <p className="text-base text-gray-400">您的各项指标正常</p>
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-4 rounded-xl border-2 ${getAlertColor(alert.severity)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-lg font-bold">{alert.indicator_name}</p>
                      <p className="text-base mt-1">
                        异常值: {alert.abnormal_value} (正常范围: {alert.normal_range})
                      </p>
                      <p className="text-sm mt-2">{alert.risk_assessment}</p>
                    </div>
                    <button
                      onClick={() => resolveAlert(alert.id!)}
                      className="ml-3 px-3 py-1.5 bg-white/50 rounded-lg text-sm font-medium hover:bg-white/70 transition-colors"
                    >
                      已处理
                    </button>
                  </div>
                  <p className="text-sm mt-3 opacity-80">
                    <Clock className="w-4 h-4 inline mr-1" />
                    {format(new Date(alert.created_at), 'MM/dd HH:mm')}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
