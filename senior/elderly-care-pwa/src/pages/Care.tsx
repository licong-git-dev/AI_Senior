import React, { useState, useEffect, useCallback } from 'react'
import { 
  Pill, Clock, Calendar, CheckCircle2, AlertCircle,
  Bell, ListChecks, RefreshCw, ChevronRight, Play, Pause
} from 'lucide-react'
import { supabase } from '../lib/supabase'
import { speak, showNotification, vibrate } from '../lib/pwa-utils'
import { format, isToday, isTomorrow } from 'date-fns'

interface Medication {
  id: string
  name: string
  dosage: string
  frequency: string
  times: string[]
  remaining: number
  notes?: string
  nextDose?: Date
  taken?: boolean
}

interface CarePlan {
  id: string
  title: string
  type: string
  description: string
  schedule: string
  progress: number
  tasks: CareTask[]
}

interface CareTask {
  id: string
  title: string
  time: string
  completed: boolean
  notes?: string
}

export default function Care() {
  const [medications, setMedications] = useState<Medication[]>([])
  const [carePlans, setCarePlans] = useState<CarePlan[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'medication' | 'care'>('medication')
  const [todayTasks, setTodayTasks] = useState<CareTask[]>([])

  // 获取用药数据
  const fetchMedications = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('medication_management')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10)

      if (error) throw error

      if (data && data.length > 0) {
        const meds: Medication[] = data.map((item: any) => ({
          id: item.id,
          name: item.name,
          dosage: item.dosage,
          frequency: item.frequency,
          times: item.times || ['08:00', '12:00', '20:00'],
          remaining: item.remaining || 30,
          notes: item.notes,
          nextDose: new Date(),
          taken: false
        }))
        setMedications(meds)
      } else {
        // 数据库无数据，显示空状态
        setMedications([])
      }
    } catch (error) {
      console.error('Fetch medications error:', error)
      setMedications([])
    }
  }, [])

  // 获取护理计划
  const fetchCarePlans = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('rehabilitation_plans')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(5)

      if (error) throw error

      if (data && data.length > 0) {
        const plans: CarePlan[] = data.map((item: any) => ({
          id: item.id,
          title: item.title,
          type: item.type,
          description: item.description,
          schedule: item.schedule,
          progress: item.progress || 0,
          tasks: item.tasks || []
        }))
        setCarePlans(plans)
      } else {
        // 数据库无数据，显示空状态
        setCarePlans([])
      }
    } catch (error) {
      console.error('Fetch care plans error:', error)
      setCarePlans([])
    }
  }, [])

  // 初始化
  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true)
      await Promise.all([fetchMedications(), fetchCarePlans()])
      setLoading(false)
    }
    fetchAll()
  }, [fetchMedications, fetchCarePlans])

  // 生成今日任务
  useEffect(() => {
    const tasks: CareTask[] = []
    
    // 从药物中生成任务
    medications.forEach(med => {
      med.times.forEach((time, idx) => {
        tasks.push({
          id: `med-${med.id}-${idx}`,
          title: `服用${med.name} ${med.dosage}`,
          time,
          completed: med.taken && idx === 0,
          notes: med.notes
        })
      })
    })

    // 从护理计划中生成任务
    carePlans.forEach(plan => {
      plan.tasks.forEach(task => {
        tasks.push(task)
      })
    })

    // 按时间排序
    tasks.sort((a, b) => a.time.localeCompare(b.time))
    setTodayTasks(tasks)
  }, [medications, carePlans])

  // 标记用药完成
  const markMedicationTaken = (medId: string) => {
    setMedications(prev => prev.map(med => 
      med.id === medId ? { ...med, taken: true } : med
    ))
    speak('已记录用药')
    vibrate([100])
    showNotification('用药提醒', {
      body: '已成功记录您的用药',
      tag: 'medication-taken'
    })
  }

  // 标记任务完成
  const markTaskCompleted = (taskId: string) => {
    setTodayTasks(prev => prev.map(task =>
      task.id === taskId ? { ...task, completed: true } : task
    ))
    speak('任务已完成')
    vibrate([100])
  }

  // 获取下一个待完成任务
  const getNextTask = () => {
    const now = format(new Date(), 'HH:mm')
    return todayTasks.find(task => !task.completed && task.time >= now)
  }

  const nextTask = getNextTask()

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 pb-24">
      {/* 顶部标题 */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-5 py-6 rounded-b-3xl shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Pill className="w-8 h-8" />
            <h1 className="text-2xl font-bold">护理中心</h1>
          </div>
          <button
            onClick={() => {
              fetchMedications()
              fetchCarePlans()
            }}
            className="p-2 bg-white/20 rounded-xl hover:bg-white/30 transition-colors active:scale-95"
          >
            <RefreshCw className={`w-6 h-6 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* 今日任务概览 */}
        <div className="bg-white/20 rounded-2xl p-4 backdrop-blur-sm">
          <p className="text-indigo-100 text-base mb-2">今日任务完成情况</p>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="h-3 bg-white/30 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-white rounded-full transition-all"
                  style={{ 
                    width: `${todayTasks.length > 0 
                      ? (todayTasks.filter(t => t.completed).length / todayTasks.length * 100) 
                      : 0}%` 
                  }}
                />
              </div>
            </div>
            <span className="text-lg font-bold">
              {todayTasks.filter(t => t.completed).length}/{todayTasks.length}
            </span>
          </div>
        </div>
      </div>

      {/* 下一个任务提醒 */}
      {nextTask && (
        <div className="px-5 -mt-4">
          <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-2xl p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-amber-100 text-base flex items-center">
                  <Bell className="w-4 h-4 mr-1" />
                  下一个任务
                </p>
                <p className="text-xl font-bold mt-1">{nextTask.title}</p>
                <p className="text-lg text-amber-100 mt-1">{nextTask.time}</p>
              </div>
              <button
                onClick={() => markTaskCompleted(nextTask.id)}
                className="bg-white/30 p-3 rounded-xl hover:bg-white/40 transition-colors active:scale-95"
              >
                <CheckCircle2 className="w-8 h-8" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 标签页切换 */}
      <div className="px-5 mt-6">
        <div className="flex space-x-3">
          <button
            onClick={() => setActiveTab('medication')}
            className={`flex-1 py-3 rounded-xl text-lg font-medium transition-all ${
              activeTab === 'medication'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200'
            }`}
          >
            <Pill className="w-5 h-5 inline mr-2" />
            用药管理
          </button>
          <button
            onClick={() => setActiveTab('care')}
            className={`flex-1 py-3 rounded-xl text-lg font-medium transition-all ${
              activeTab === 'care'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200'
            }`}
          >
            <ListChecks className="w-5 h-5 inline mr-2" />
            护理计划
          </button>
        </div>
      </div>

      {/* 用药管理 */}
      {activeTab === 'medication' && (
        <div className="px-5 mt-6 space-y-4">
          {medications.map((med) => (
            <div
              key={med.id}
              className={`bg-white rounded-2xl p-5 shadow-sm border-2 transition-all ${
                med.taken ? 'border-green-300 bg-green-50' : 'border-gray-100'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="text-xl font-bold text-gray-800">{med.name}</h3>
                    {med.taken && (
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                    )}
                  </div>
                  <p className="text-lg text-gray-600 mt-1">{med.dosage} - {med.frequency}</p>
                  <div className="flex items-center space-x-4 mt-2">
                    <span className="text-base text-gray-500">
                      <Clock className="w-4 h-4 inline mr-1" />
                      {med.times.join('、')}
                    </span>
                    <span className="text-base text-gray-500">
                      剩余 {med.remaining} 天
                    </span>
                  </div>
                  {med.notes && (
                    <p className="text-base text-indigo-600 mt-2 bg-indigo-50 px-3 py-1 rounded-lg inline-block">
                      {med.notes}
                    </p>
                  )}
                </div>
                
                {!med.taken && (
                  <button
                    onClick={() => markMedicationTaken(med.id)}
                    className="ml-4 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-xl flex items-center space-x-2 transition-all active:scale-95"
                  >
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="text-base font-medium">已服用</span>
                  </button>
                )}
              </div>

              {/* 库存预警 */}
              {med.remaining <= 7 && (
                <div className="mt-3 bg-orange-100 text-orange-700 px-4 py-2 rounded-xl flex items-center">
                  <AlertCircle className="w-5 h-5 mr-2" />
                  <span className="text-base">药物即将用完，请及时补充</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 护理计划 */}
      {activeTab === 'care' && (
        <div className="px-5 mt-6 space-y-4">
          {carePlans.map((plan) => (
            <div
              key={plan.id}
              className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-800">{plan.title}</h3>
                  <p className="text-base text-gray-600 mt-1">{plan.description}</p>
                  <p className="text-sm text-indigo-600 mt-2">
                    <Calendar className="w-4 h-4 inline mr-1" />
                    {plan.schedule}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-indigo-600">{plan.progress}%</p>
                  <p className="text-sm text-gray-500">完成度</p>
                </div>
              </div>

              {/* 进度条 */}
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all"
                  style={{ width: `${plan.progress}%` }}
                />
              </div>

              {/* 今日任务 */}
              <div className="space-y-2">
                {plan.tasks.map((task) => (
                  <div
                    key={task.id}
                    className={`flex items-center justify-between p-3 rounded-xl ${
                      task.completed ? 'bg-green-50' : 'bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => markTaskCompleted(task.id)}
                        className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                          task.completed
                            ? 'bg-green-500 border-green-500 text-white'
                            : 'border-gray-300 hover:border-indigo-500'
                        }`}
                      >
                        {task.completed && <CheckCircle2 className="w-4 h-4" />}
                      </button>
                      <div>
                        <p className={`text-base font-medium ${
                          task.completed ? 'text-gray-400 line-through' : 'text-gray-800'
                        }`}>
                          {task.title}
                        </p>
                        <p className="text-sm text-gray-500">{task.time}</p>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* 今日任务列表 */}
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-5 border border-indigo-200">
            <div className="flex items-center space-x-2 mb-4">
              <ListChecks className="w-6 h-6 text-indigo-600" />
              <h3 className="text-xl font-bold text-indigo-800">今日全部任务</h3>
            </div>
            
            <div className="space-y-2">
              {todayTasks.map((task) => (
                <div
                  key={task.id}
                  className={`flex items-center justify-between p-3 rounded-xl ${
                    task.completed ? 'bg-white/50' : 'bg-white'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className={`text-base font-medium ${
                      task.completed ? 'text-gray-400 line-through' : 'text-gray-800'
                    }`}>
                      {task.time}
                    </span>
                    <span className={`text-base ${
                      task.completed ? 'text-gray-400 line-through' : 'text-gray-700'
                    }`}>
                      {task.title}
                    </span>
                  </div>
                  {task.completed ? (
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                  ) : (
                    <button
                      onClick={() => markTaskCompleted(task.id)}
                      className="text-indigo-500 text-base font-medium"
                    >
                      完成
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
