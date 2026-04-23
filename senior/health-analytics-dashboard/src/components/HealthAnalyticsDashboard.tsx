import { useState, useEffect, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import { supabase } from '../lib/supabase'
import type {
  UserRole,
  TimeRange,
  HealthData,
  PhysiologicalAnalysis,
  BehaviorPattern,
  HealthPrediction,
  HealthAlert
} from '../types'
import { format, subDays, subHours } from 'date-fns'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import { Activity, Brain, Heart, TrendingUp, AlertTriangle, Download, RefreshCw, Users, Clock } from 'lucide-react'

const HealthAnalyticsDashboard = () => {
  const [userRole, setUserRole] = useState<UserRole>('family')
  const [timeRange, setTimeRange] = useState<TimeRange>('7d')
  const [selectedUserId] = useState<string>('94547eee-5f39-4f76-a08e-ba4540a101ae')
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  
  const [healthData, setHealthData] = useState<HealthData[]>([])
  const [physiologicalData, setPhysiologicalData] = useState<PhysiologicalAnalysis[]>([])
  const [behaviorData, setBehaviorData] = useState<BehaviorPattern[]>([])
  const [predictionData, setPredictionData] = useState<HealthPrediction[]>([])
  const [alertData, setAlertData] = useState<HealthAlert[]>([])
  
  const [realtimePrediction, setRealtimePrediction] = useState<any>(null)
  const [anomalyDetection, setAnomalyDetection] = useState<any>(null)

  const getTimeRangeDate = useCallback(() => {
    const now = new Date()
    switch (timeRange) {
      case '24h': return subHours(now, 24)
      case '7d': return subDays(now, 7)
      case '30d': return subDays(now, 30)
      case '90d': return subDays(now, 90)
      default: return subDays(now, 7)
    }
  }, [timeRange])

  const loadHealthData = useCallback(async () => {
    if (!selectedUserId) return
    setLoading(true)
    const startDate = getTimeRangeDate()

    try {
      // 使用sensor_data表替代health_data
      const { data: sensorRaw } = await supabase.from('sensor_data').select('*').eq('user_id', selectedUserId).gte('timestamp', startDate.toISOString()).order('timestamp', { ascending: true }).limit(100)
      
      // 转换sensor_data为health_data格式
      const health = (sensorRaw || []).map(s => ({
        id: s.id,
        user_id: s.user_id,
        data_type: s.data_type,
        value: typeof s.processed_value === 'object' ? 
          (s.processed_value?.value || s.processed_value?.heartRate || 0) : 
          (s.processed_value || 0),
        unit: s.data_type === 'heart_rate' ? 'bpm' : 
              s.data_type === 'blood_pressure' ? 'mmHg' : 
              s.data_type === 'temperature' ? '°C' : '',
        timestamp: s.timestamp,
        metadata: s.processed_value
      }))
      setHealthData(health || [])

      const { data: physio } = await supabase.from('physiological_analysis').select('*').eq('user_id', selectedUserId).gte('analysis_time', startDate.toISOString()).order('analysis_time', { ascending: false }).limit(20)
      setPhysiologicalData(physio || [])

      const { data: behavior } = await supabase.from('behavior_patterns').select('*').eq('user_id', selectedUserId).gte('detection_time', startDate.toISOString()).order('detection_time', { ascending: false }).limit(20)
      setBehaviorData(behavior || [])

      const { data: predictions } = await supabase.from('health_predictions').select('*').eq('user_id', selectedUserId).order('prediction_time', { ascending: false }).limit(5)
      setPredictionData(predictions || [])

      // 使用真实的health_alerts表
      const { data: alerts } = await supabase.from('health_alerts').select('*').eq('user_id', selectedUserId).gte('alert_time', startDate.toISOString()).eq('resolved', false).order('alert_time', { ascending: false }).limit(10)
      setAlertData(alerts || [])

      setLastUpdate(new Date())
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      setLoading(false)
    }
  }, [selectedUserId, getTimeRangeDate])

  const runRealtimePrediction = useCallback(async () => {
    if (!selectedUserId || healthData.length === 0) return

    try {
      const historicalData = healthData.filter(d => d.data_type === 'blood_pressure' || d.data_type === 'heart_rate').slice(-7).map(d => ({
        heartRate: d.data_type === 'heart_rate' ? d.value : 75,
        systolic: d.data_type === 'blood_pressure' ? d.metadata?.systolic || 120 : 120,
        diastolic: d.data_type === 'blood_pressure' ? d.metadata?.diastolic || 80 : 80
      }))

      if (historicalData.length === 0) return

      const { data } = await supabase.functions.invoke('ai-core-engine', {
        body: {
          action: 'health-prediction',
          userId: selectedUserId,
          timeRange: timeRange === '24h' ? '24h' : '7d',
          data: historicalData
        }
      })

      if (data) setRealtimePrediction(data.data)
    } catch (error) {
      console.error('实时预测失败:', error)
    }
  }, [selectedUserId, healthData, timeRange])

  const runAnomalyDetection = useCallback(async () => {
    if (!selectedUserId || physiologicalData.length === 0) return

    try {
      const latestPhysio = physiologicalData[0]
      const latestBehavior = behaviorData[0]

      const { data } = await supabase.functions.invoke('ai-core-engine', {
        body: {
          action: 'anomaly-detection',
          userId: selectedUserId,
          data: {
            vitalSigns: {
              heartRate: latestPhysio?.heart_rate_variability?.mean || 75,
              systolic: latestPhysio?.blood_pressure_prediction?.predicted?.systolic || 120,
              diastolic: latestPhysio?.blood_pressure_prediction?.predicted?.diastolic || 80,
              temperature: 36.5,
              oxygenSaturation: 98
            },
            behavior: {
              nightActivity: latestBehavior?.abnormal_behaviors?.length || 0,
              dailySteps: latestBehavior?.activity_trajectory?.totalDistance || 5000,
              sleepDuration: latestPhysio?.sleep_quality_score ? latestPhysio.sleep_quality_score * 8 : 7
            },
            environment: {
              temperature: 22,
              humidity: 50
            }
          }
        }
      })

      if (data) setAnomalyDetection(data.data)
    } catch (error) {
      console.error('异常检测失败:', error)
    }
  }, [selectedUserId, physiologicalData, behaviorData])

  useEffect(() => {
    loadHealthData()
    const interval = setInterval(loadHealthData, 60000)
    return () => clearInterval(interval)
  }, [loadHealthData])

  useEffect(() => {
    if (healthData.length > 0) runRealtimePrediction()
    if (physiologicalData.length > 0) runAnomalyDetection()
  }, [healthData, physiologicalData, runRealtimePrediction, runAnomalyDetection])

  useEffect(() => {
    if (!selectedUserId) return
    const channel = supabase.channel('health_updates').on('postgres_changes', { event: '*', schema: 'public', table: 'sensor_data', filter: `user_id=eq.${selectedUserId}` }, () => { loadHealthData() }).subscribe()
    return () => { supabase.removeChannel(channel) }
  }, [selectedUserId, loadHealthData])

  const exportPDF = async () => {
    const element = document.getElementById('dashboard-content')
    if (!element) return
    try {
      const canvas = await html2canvas(element, { scale: 2, useCORS: true })
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF('p', 'mm', 'a4')
      const pdfWidth = pdf.internal.pageSize.getWidth()
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)
      pdf.save(`health-report-${format(new Date(), 'yyyy-MM-dd')}.pdf`)
      alert('PDF导出成功！')
    } catch (error) {
      console.error('导出PDF失败:', error)
      alert('PDF导出失败，请重试')
    }
  }

  const exportExcel = () => {
    try {
      let csvContent = '\uFEFF' // BOM for UTF-8
      csvContent += '时间戳,数据类型,数值,单位,用户ID\n'
      
      healthData.forEach(item => {
        const row = [
          format(new Date(item.timestamp), 'yyyy-MM-dd HH:mm:ss'),
          item.data_type,
          item.value,
          item.unit,
          item.user_id
        ].join(',')
        csvContent += row + '\n'
      })

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `health-data-${format(new Date(), 'yyyy-MM-dd')}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      alert('Excel导出成功！')
    } catch (error) {
      console.error('导出Excel失败:', error)
      alert('Excel导出失败，请重试')
    }
  }

  const getLineChartOption = () => {
    const dates = healthData.map(d => format(new Date(d.timestamp), 'MM-dd HH:mm'))
    const heartRates = healthData.filter(d => d.data_type === 'heart_rate').map(d => d.value)
    const bloodPressures = healthData.filter(d => d.data_type === 'blood_pressure').map(d => d.metadata?.systolic || 0)

    return {
      title: { text: '健康指标趋势', left: 'center', textStyle: { fontWeight: 700, fontSize: 16 } },
      tooltip: { 
        trigger: 'axis',
        axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } }
      },
      legend: { data: ['心率 (bpm)', '收缩压 (mmHg)'], top: 30 },
      grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
      toolbox: {
        feature: {
          dataZoom: { yAxisIndex: 'none', title: { zoom: '区域缩放', back: '还原' } },
          restore: { title: '还原' },
          saveAsImage: { title: '保存为图片' },
          magicType: { show: true, type: ['line', 'bar'], title: { line: '切换为折线图', bar: '切换为柱状图' } }
        }
      },
      xAxis: { type: 'category', data: dates.slice(-20), boundaryGap: false },
      yAxis: { type: 'value' },
      series: [
        { 
          name: '心率 (bpm)', 
          type: 'line', 
          data: heartRates.slice(-20), 
          smooth: true, 
          itemStyle: { color: '#3b82f6' },
          areaStyle: { opacity: 0.3 },
          markLine: {
            data: [
              { type: 'average', name: '平均值' },
              [{ name: '正常范围下限', yAxis: 60 }, { yAxis: 60, x: '100%' }],
              [{ name: '正常范围上限', yAxis: 100 }, { yAxis: 100, x: '100%' }]
            ]
          }
        },
        { 
          name: '收缩压 (mmHg)', 
          type: 'line', 
          data: bloodPressures.slice(-20), 
          smooth: true, 
          itemStyle: { color: '#ef4444' },
          areaStyle: { opacity: 0.3 },
          markLine: {
            data: [
              { type: 'average', name: '平均值' },
              [{ name: '正常范围下限', yAxis: 90 }, { yAxis: 90, x: '100%' }],
              [{ name: '正常范围上限', yAxis: 140 }, { yAxis: 140, x: '100%' }]
            ]
          }
        }
      ],
      dataZoom: [
        { type: 'inside', start: 0, end: 100 }, 
        { start: 0, end: 100, height: 30, bottom: 10 }
      ]
    }
  }

  const getBarChartOption = () => {
    const dates = behaviorData.map(d => format(new Date(d.detection_time), 'MM-dd'))
    const activeTime = behaviorData.map(d => d.activity_trajectory?.activeTime || 0)
    const sedentaryTime = behaviorData.map(d => d.activity_trajectory?.sedentaryTime || 0)

    return {
      title: { text: '日常活动统计', left: 'center', textStyle: { fontWeight: 700, fontSize: 16 } },
      tooltip: { 
        trigger: 'axis', 
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          let result = `<b>${params[0].axisValue}</b><br/>`
          params.forEach((item: any) => {
            result += `${item.marker} ${item.seriesName}: ${item.value} 分钟<br/>`
          })
          return result
        }
      },
      legend: { data: ['活动时间', '久坐时间'], top: 30 },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      toolbox: {
        feature: {
          magicType: { show: true, type: ['line', 'bar', 'stack'], title: { line: '折线图', bar: '柱状图', stack: '堆叠' } },
          restore: { title: '还原' },
          saveAsImage: { title: '保存为图片' }
        }
      },
      xAxis: { type: 'category', data: dates.slice(-7).reverse() },
      yAxis: { type: 'value', name: '分钟' },
      series: [
        { 
          name: '活动时间', 
          type: 'bar', 
          data: activeTime.slice(-7).reverse(), 
          itemStyle: { color: '#10b981' },
          emphasis: { focus: 'series' },
          markPoint: { data: [{ type: 'max', name: '最大值' }, { type: 'min', name: '最小值' }] },
          markLine: { data: [{ type: 'average', name: '平均值' }] }
        },
        { 
          name: '久坐时间', 
          type: 'bar', 
          data: sedentaryTime.slice(-7).reverse(), 
          itemStyle: { color: '#f59e0b' },
          emphasis: { focus: 'series' },
          markPoint: { data: [{ type: 'max', name: '最大值' }, { type: 'min', name: '最小值' }] },
          markLine: { data: [{ type: 'average', name: '平均值' }] }
        }
      ]
    }
  }

  const getPieChartOption = () => {
    const sleepQualities = physiologicalData.filter(d => d.sleep_quality_score).map(d => d.sleep_quality_score)
    const good = sleepQualities.filter(s => s > 0.7).length
    const fair = sleepQualities.filter(s => s >= 0.5 && s <= 0.7).length
    const poor = sleepQualities.filter(s => s < 0.5).length

    return {
      title: { text: '睡眠质量分布', left: 'center', textStyle: { fontWeight: 700, fontSize: 16 } },
      tooltip: { 
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: { orient: 'vertical', left: 'left', top: 'center' },
      toolbox: {
        feature: {
          saveAsImage: { title: '保存为图片' }
        }
      },
      series: [{
        name: '睡眠质量',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        data: [
          { value: good, name: '良好', itemStyle: { color: '#10b981' } },
          { value: fair, name: '一般', itemStyle: { color: '#f59e0b' } },
          { value: poor, name: '较差', itemStyle: { color: '#ef4444' } }
        ],
        emphasis: { 
          itemStyle: { 
            shadowBlur: 10, 
            shadowOffsetX: 0, 
            shadowColor: 'rgba(0, 0, 0, 0.5)' 
          },
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 700
          }
        },
        label: { 
          formatter: '{b}: {c} ({d}%)',
          fontSize: 12
        }
      }]
    }
  }

  const getHeatmapOption = () => {
    const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
    const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    const data: [number, number, number][] = []
    
    // 使用真实的behavior_patterns数据
    behaviorData.forEach(b => {
      const date = new Date(b.detection_time)
      const hour = date.getHours()
      const day = date.getDay()
      // 只使用真实数据，不生成随机数
      const activity = b.activity_trajectory?.activeTime || 0
      if (activity > 0) {
        data.push([hour, day, activity])
      }
    })
    
    // 使用sensor_data中的活动数据补充热力图
    sensorData.forEach(s => {
      if (s.data_type === 'activity' || s.data_type === 'steps') {
        const date = new Date(s.timestamp)
        const hour = date.getHours()
        const day = date.getDay()
        const value = typeof s.processed_value === 'number' ? s.processed_value : 
                     (s.processed_value?.value || 0)
        if (value > 0) {
          // 归一化到0-100范围
          const normalizedValue = s.data_type === 'steps' ? Math.min(value / 100, 100) : value
          data.push([hour, day, normalizedValue])
        }
      }
    })

    // 数据完整性提示
    const hasData = data.length > 0
    const dataCompletion = (data.length / (7 * 24)) * 100

    return {
      title: { 
        text: hasData ? '24小时活动热力图' : '24小时活动热力图（数据不足）',
        subtext: hasData ? `数据完整度: ${dataCompletion.toFixed(1)}%` : '暂无足够数据展示',
        left: 'center', 
        textStyle: { fontWeight: 700, fontSize: 16 }
      },
      tooltip: { 
        position: 'top',
        formatter: (params: any) => {
          return `${days[params.value[1]]} ${hours[params.value[0]]}<br/>活动强度: ${params.value[2].toFixed(1)}`
        }
      },
      grid: { height: '60%', top: '20%' },
      toolbox: {
        feature: {
          saveAsImage: { title: '保存为图片' },
          dataZoom: { title: { zoom: '区域缩放', back: '还原' } },
          restore: { title: '还原' }
        }
      },
      xAxis: { type: 'category', data: hours, splitArea: { show: true } },
      yAxis: { type: 'category', data: days, splitArea: { show: true } },
      visualMap: { 
        min: 0, 
        max: 100, 
        calculable: true, 
        orient: 'horizontal', 
        left: 'center', 
        bottom: '5%', 
        inRange: { color: ['#e0f2fe', '#7dd3fc', '#0ea5e9', '#0369a1', '#1e40af'] },
        text: ['高', '低'],
        textStyle: { color: '#333' }
      },
      series: [{ 
        name: '活动强度', 
        type: 'heatmap', 
        data: hasData ? data : [], 
        label: { show: false }, 
        emphasis: { 
          itemStyle: { 
            shadowBlur: 10, 
            shadowColor: 'rgba(0, 0, 0, 0.5)' 
          } 
        } 
      }]
    }
  }

  const getScatterOption = () => {
    const scatterData = healthData.filter(d => d.data_type === 'heart_rate' || d.data_type === 'blood_pressure').reduce((acc: any[], curr) => {
      if (curr.data_type === 'heart_rate') {
        const bp = healthData.find(d => d.data_type === 'blood_pressure' && Math.abs(new Date(d.timestamp).getTime() - new Date(curr.timestamp).getTime()) < 3600000)
        if (bp) acc.push([curr.value, bp.metadata?.systolic || 0])
      }
      return acc
    }, [])

    return {
      title: { text: '心率与血压关系', left: 'center', textStyle: { fontWeight: 700, fontSize: 16 } },
      tooltip: { 
        trigger: 'item', 
        formatter: (params: any) => `心率: ${params.value[0]} bpm<br/>收缩压: ${params.value[1]} mmHg` 
      },
      grid: { left: '10%', right: '10%', bottom: '10%', containLabel: true },
      toolbox: {
        feature: {
          dataZoom: { title: { zoom: '区域缩放', back: '还原' } },
          restore: { title: '还原' },
          saveAsImage: { title: '保存为图片' }
        }
      },
      xAxis: { 
        type: 'value', 
        name: '心率 (bpm)', 
        min: 50, 
        max: 100,
        splitLine: { show: true, lineStyle: { type: 'dashed' } }
      },
      yAxis: { 
        type: 'value', 
        name: '收缩压 (mmHg)', 
        min: 100, 
        max: 150,
        splitLine: { show: true, lineStyle: { type: 'dashed' } }
      },
      series: [{ 
        name: '心率-血压', 
        type: 'scatter', 
        data: scatterData, 
        symbolSize: 12, 
        itemStyle: { 
          color: '#8b5cf6',
          opacity: 0.7
        },
        emphasis: {
          itemStyle: {
            color: '#7c3aed',
            borderColor: '#333',
            borderWidth: 2,
            shadowBlur: 10,
            shadowColor: 'rgba(139, 92, 246, 0.5)'
          }
        }
      }],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0], start: 0, end: 100 },
        { type: 'inside', yAxisIndex: [0], start: 0, end: 100 }
      ]
    }
  }

  const getPredictionChartOption = () => {
    if (!realtimePrediction || !realtimePrediction.predictions) {
      return { title: { text: '健康预测 (数据加载中...)', left: 'center' } }
    }

    const predictions = realtimePrediction.predictions || []
    const dates = predictions.map((p: any) => p.date)
    const heartRates = predictions.map((p: any) => p.heartRate)
    const systolic = predictions.map((p: any) => p.systolic)

    return {
      title: { text: `未来${timeRange === '24h' ? '24小时' : '7天'}健康预测`, left: 'center' },
      tooltip: { trigger: 'axis' },
      legend: { data: ['预测心率', '预测收缩压'], top: 30 },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value' },
      series: [
        { name: '预测心率', type: 'line', data: heartRates, smooth: true, lineStyle: { type: 'dashed' }, itemStyle: { color: '#3b82f6' } },
        { name: '预测收缩压', type: 'line', data: systolic, smooth: true, lineStyle: { type: 'dashed' }, itemStyle: { color: '#ef4444' } }
      ]
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Activity className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">健康数据分析仪表盘</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <select value={userRole} onChange={(e) => setUserRole(e.target.value as UserRole)} className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="elderly">老人视图</option>
                <option value="family">家属视图</option>
                <option value="doctor">医生视图</option>
                <option value="nurse">护理视图</option>
                <option value="admin">管理视图</option>
              </select>

              <select value={timeRange} onChange={(e) => setTimeRange(e.target.value as TimeRange)} className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="24h">24小时</option>
                <option value="7d">7天</option>
                <option value="30d">30天</option>
                <option value="90d">90天</option>
              </select>

              <button onClick={loadHealthData} disabled={loading} className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50">
                <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
              </button>

              <button onClick={exportPDF} className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                <Download className="h-5 w-5" />
                <span>导出PDF</span>
              </button>
              
              <button onClick={exportExcel} className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                <Download className="h-5 w-5" />
                <span>导出Excel</span>
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between pb-3">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="h-4 w-4" />
              <span>最后更新: {format(lastUpdate, 'yyyy-MM-dd HH:mm:ss')}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Users className="h-4 w-4" />
              <span>用户ID: {selectedUserId.slice(0, 8)}...</span>
            </div>
          </div>
        </div>
      </div>

      <div id="dashboard-content" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 数据完整性提示 */}
        {!loading && (
          <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded-lg">
            <h4 className="text-sm font-semibold text-blue-900 mb-2 flex items-center">
              <Activity className="h-4 w-4 mr-2" />
              数据完整性状态
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className={`flex items-center ${healthData.length > 0 ? 'text-green-700' : 'text-gray-500'}`}>
                <span className={`w-2 h-2 rounded-full mr-2 ${healthData.length > 0 ? 'bg-green-500' : 'bg-gray-400'}`}></span>
                健康数据: {healthData.length > 0 ? `${healthData.length}条` : '暂无数据'}
              </div>
              <div className={`flex items-center ${physiologicalData.length > 0 ? 'text-green-700' : 'text-gray-500'}`}>
                <span className={`w-2 h-2 rounded-full mr-2 ${physiologicalData.length > 0 ? 'bg-green-500' : 'bg-gray-400'}`}></span>
                生理分析: {physiologicalData.length > 0 ? `${physiologicalData.length}份` : '暂无数据'}
              </div>
              <div className={`flex items-center ${behaviorData.length > 0 ? 'text-green-700' : 'text-gray-500'}`}>
                <span className={`w-2 h-2 rounded-full mr-2 ${behaviorData.length > 0 ? 'bg-green-500' : 'bg-gray-400'}`}></span>
                行为模式: {behaviorData.length > 0 ? `${behaviorData.length}条` : '暂无数据'}
              </div>
              <div className={`flex items-center ${alertData.length > 0 ? 'text-green-700' : 'text-gray-500'}`}>
                <span className={`w-2 h-2 rounded-full mr-2 ${alertData.length > 0 ? 'bg-green-500' : 'bg-gray-400'}`}></span>
                健康预警: {alertData.length > 0 ? `${alertData.length}条` : '暂无预警'}
              </div>
            </div>
            {(healthData.length === 0 || physiologicalData.length === 0) && (
              <div className="mt-3 text-xs text-orange-700 bg-orange-50 p-2 rounded">
                ⚠️ 部分数据缺失，图表可能显示不完整。请确保已有足够的历史数据。
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">健康数据记录</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{healthData.length}</p>
              </div>
              <Heart className="h-12 w-12 text-blue-500 opacity-80" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">生理分析报告</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{physiologicalData.length}</p>
              </div>
              <Brain className="h-12 w-12 text-green-500 opacity-80" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">健康预测</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{predictionData.length}</p>
              </div>
              <TrendingUp className="h-12 w-12 text-purple-500 opacity-80" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-red-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">健康预警</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{alertData.length}</p>
              </div>
              <AlertTriangle className="h-12 w-12 text-red-500 opacity-80" />
            </div>
          </div>
        </div>

        {alertData.length > 0 && (
          <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-red-900 mb-3 flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              健康预警
            </h3>
            <div className="space-y-3">
              {alertData.slice(0, 5).map((alert) => (
                <div key={alert.id} className="flex items-start space-x-3 text-sm bg-white p-3 rounded-lg">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${alert.severity === 'high' ? 'bg-red-200 text-red-800' : alert.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' : 'bg-blue-200 text-blue-800'}`}>
                    {alert.severity === 'high' ? '高' : alert.severity === 'medium' ? '中' : '低'}风险
                  </span>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{alert.indicator_name}异常</div>
                    <div className="text-gray-600 mt-1">
                      异常值: <span className="font-semibold text-red-600">{alert.abnormal_value}</span>
                      {alert.normal_range && <span className="ml-2 text-gray-500">（正常范围: {alert.normal_range}）</span>}
                    </div>
                    {alert.risk_assessment && (
                      <div className="text-gray-700 mt-1">{alert.risk_assessment}</div>
                    )}
                    {alert.recommended_actions && (
                      <div className="text-blue-600 mt-1 text-xs">建议: {alert.recommended_actions}</div>
                    )}
                  </div>
                  <span className="text-gray-500 text-xs whitespace-nowrap">{format(new Date(alert.alert_time), 'MM-dd HH:mm')}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {anomalyDetection && anomalyDetection.alerts && anomalyDetection.alerts.length > 0 && (
          <div className="bg-yellow-50 border-l-4 border-yellow-500 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-yellow-900 mb-3">AI异常检测</h3>
            <div className="space-y-2">
              {anomalyDetection.alerts.map((alert: any, idx: number) => (
                <div key={idx} className="flex items-start space-x-3 text-sm">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${alert.priority === 'urgent' ? 'bg-red-200 text-red-800' : alert.priority === 'high' ? 'bg-orange-200 text-orange-800' : 'bg-blue-200 text-blue-800'}`}>
                    {alert.priority}
                  </span>
                  <span className="text-gray-700">{alert.message}</span>
                </div>
              ))}
            </div>
            <p className="mt-3 text-sm text-gray-600">异常评分: {(anomalyDetection.anomalyScore * 100).toFixed(0)}%</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <ReactECharts option={getLineChartOption()} style={{ height: '400px' }} />
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <ReactECharts option={getBarChartOption()} style={{ height: '400px' }} />
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <ReactECharts option={getPieChartOption()} style={{ height: '400px' }} />
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <ReactECharts option={getScatterOption()} style={{ height: '400px' }} />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <ReactECharts option={getHeatmapOption()} style={{ height: '500px' }} />
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <ReactECharts option={getPredictionChartOption()} style={{ height: '400px' }} />
          {realtimePrediction && realtimePrediction.riskFactors && realtimePrediction.riskFactors.length > 0 && (
            <div className="mt-6 p-4 bg-amber-50 rounded-lg">
              <h4 className="text-sm font-semibold text-amber-900 mb-2">风险因素识别</h4>
              <div className="space-y-2">
                {realtimePrediction.riskFactors.map((risk: any, idx: number) => (
                  <div key={idx} className="text-sm text-gray-700">
                    <span className="font-medium">{risk.factor}:</span> {risk.description}
                    <span className="ml-2 text-amber-600">概率: {(risk.probability * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default HealthAnalyticsDashboard
