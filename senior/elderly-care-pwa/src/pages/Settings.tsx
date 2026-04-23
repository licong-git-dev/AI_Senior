import React, { useState, useEffect } from 'react'
import { 
  Activity, Bell, TrendingUp, AlertCircle, Eye, Volume2,
  Settings as SettingsIcon, Moon, Sun, Smartphone
} from 'lucide-react'
import { supabase } from '../lib/supabase'
import { 
  requestNotificationPermission, 
  isPWA, 
  speak,
  showNotification 
} from '../lib/pwa-utils'

interface SettingsData {
  notifications: boolean
  voiceReminders: boolean
  autoSync: boolean
  dataFrequency: number
  fontSize: 'normal' | 'large' | 'extra-large'
  theme: 'light' | 'dark' | 'auto'
  language: 'zh-CN' | 'en-US'
  emergencyContacts: string[]
  healthThresholds: {
    heartRate: { min: number; max: number }
    bloodPressure: { min: number; max: number }
    temperature: { min: number; max: number }
  }
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsData>({
    notifications: true,
    voiceReminders: true,
    autoSync: true,
    dataFrequency: 30,
    fontSize: 'large',
    theme: 'light',
    language: 'zh-CN',
    emergencyContacts: [],
    healthThresholds: {
      heartRate: { min: 50, max: 100 },
      bloodPressure: { min: 90, max: 140 },
      temperature: { min: 36.0, max: 37.5 }
    }
  })

  const [pwaInstalled, setPwaInstalled] = useState(false)
  const [saving, setSaving] = useState(false)

  // 检查PWA安装状态
  useEffect(() => {
    setPwaInstalled(isPWA())
  }, [])

  // 加载设置
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const saved = localStorage.getItem('elderlycare-settings')
        if (saved) {
          setSettings(JSON.parse(saved))
        }
      } catch (error) {
        console.error('Load settings error:', error)
      }
    }
    loadSettings()
  }, [])

  // 保存设置
  const saveSettings = async () => {
    setSaving(true)
    try {
      localStorage.setItem('elderlycare-settings', JSON.stringify(settings))
      
      // 应用字体大小
      document.documentElement.style.fontSize = 
        settings.fontSize === 'extra-large' ? '20px' : 
        settings.fontSize === 'large' ? '16px' : '14px'
      
      showNotification('设置已保存', {
        body: '您的设置已成功保存',
        tag: 'settings-saved'
      })
      
      speak('设置已保存')
      
      setTimeout(() => setSaving(false), 1000)
    } catch (error) {
      console.error('Save settings error:', error)
      speak('设置保存失败')
      setSaving(false)
    }
  }

  // 更新设置
  const updateSetting = (key: keyof SettingsData, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  // 请求通知权限
  const handleNotificationToggle = async (enabled: boolean) => {
    if (enabled) {
      const permission = await requestNotificationPermission()
      if (permission === 'granted') {
        updateSetting('notifications', true)
        speak('通知权限已开启')
      } else {
        speak('通知权限被拒绝，请在系统设置中开启')
      }
    } else {
      updateSetting('notifications', false)
    }
  }

  // 更新健康阈值
  const updateThreshold = (
    type: 'heartRate' | 'bloodPressure' | 'temperature',
    boundary: 'min' | 'max',
    value: number
  ) => {
    setSettings(prev => ({
      ...prev,
      healthThresholds: {
        ...prev.healthThresholds,
        [type]: {
          ...prev.healthThresholds[type],
          [boundary]: value
        }
      }
    }))
  }

  // 字体大小选项
  const fontSizeOptions = [
    { value: 'normal', label: '标准', size: 'text-base' },
    { value: 'large', label: '大字体', size: 'text-lg' },
    { value: 'extra-large', label: '超大字体', size: 'text-xl' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 pb-24">
      {/* 顶部标题 */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-5 py-8 rounded-b-3xl shadow-lg">
        <div className="flex items-center justify-center mb-3">
          <SettingsIcon className="w-12 h-12" />
        </div>
        <h1 className="text-3xl font-bold text-center mb-2">设置中心</h1>
        <p className="text-lg text-center text-indigo-100">个性化您的健康助手</p>
      </div>

      <div className="px-5 mt-6 space-y-5">
        {/* PWA安装状态 */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Smartphone className="w-6 h-6 text-indigo-500" />
              <div>
                <p className="text-lg font-bold text-gray-800">应用安装状态</p>
                <p className="text-base text-gray-500">
                  {pwaInstalled ? '已安装到主屏幕' : '未安装'}
                </p>
              </div>
            </div>
            {pwaInstalled ? (
              <div className="bg-green-100 text-green-700 px-4 py-2 rounded-xl font-medium text-base">
                已安装
              </div>
            ) : (
              <div className="bg-yellow-100 text-yellow-700 px-4 py-2 rounded-xl font-medium text-base">
                未安装
              </div>
            )}
          </div>
        </div>

        {/* 通知设置 */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center space-x-2 mb-4">
            <Bell className="w-6 h-6 text-indigo-500" />
            <h2 className="text-xl font-bold text-gray-800">通知设置</h2>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-lg font-medium text-gray-800">推送通知</p>
                <p className="text-base text-gray-500">接收健康提醒和异常告警</p>
              </div>
              <button
                onClick={() => handleNotificationToggle(!settings.notifications)}
                className={`w-16 h-8 rounded-full transition-colors ${
                  settings.notifications ? 'bg-green-500' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-6 h-6 bg-white rounded-full transform transition-transform ${
                    settings.notifications ? 'translate-x-9' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-lg font-medium text-gray-800">语音提醒</p>
                <p className="text-base text-gray-500">使用语音播报健康信息</p>
              </div>
              <button
                onClick={() => updateSetting('voiceReminders', !settings.voiceReminders)}
                className={`w-16 h-8 rounded-full transition-colors ${
                  settings.voiceReminders ? 'bg-green-500' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-6 h-6 bg-white rounded-full transform transition-transform ${
                    settings.voiceReminders ? 'translate-x-9' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* 字体大小设置 */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center space-x-2 mb-4">
            <Eye className="w-6 h-6 text-indigo-500" />
            <h2 className="text-xl font-bold text-gray-800">显示设置</h2>
          </div>
          
          <div className="space-y-3">
            <p className="text-lg font-medium text-gray-700 mb-3">字体大小</p>
            <div className="grid grid-cols-3 gap-3">
              {fontSizeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => updateSetting('fontSize', option.value)}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    settings.fontSize === option.value
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-gray-200 bg-white text-gray-700'
                  }`}
                >
                  <span className={`font-medium ${option.size}`}>
                    {option.label}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 数据同步设置 */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center space-x-2 mb-4">
            <Activity className="w-6 h-6 text-indigo-500" />
            <h2 className="text-xl font-bold text-gray-800">数据同步</h2>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-lg font-medium text-gray-800">自动同步</p>
                <p className="text-base text-gray-500">离线数据自动上传</p>
              </div>
              <button
                onClick={() => updateSetting('autoSync', !settings.autoSync)}
                className={`w-16 h-8 rounded-full transition-colors ${
                  settings.autoSync ? 'bg-green-500' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-6 h-6 bg-white rounded-full transform transition-transform ${
                    settings.autoSync ? 'translate-x-9' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div>
              <p className="text-lg font-medium text-gray-800 mb-2">刷新频率</p>
              <select
                value={settings.dataFrequency}
                onChange={(e) => updateSetting('dataFrequency', parseInt(e.target.value))}
                className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 text-lg focus:border-indigo-500 focus:outline-none"
              >
                <option value={10}>10秒</option>
                <option value={30}>30秒</option>
                <option value={60}>1分钟</option>
                <option value={300}>5分钟</option>
              </select>
            </div>
          </div>
        </div>

        {/* 健康阈值设置 */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center space-x-2 mb-4">
            <AlertCircle className="w-6 h-6 text-indigo-500" />
            <h2 className="text-xl font-bold text-gray-800">健康阈值</h2>
          </div>
          
          <div className="space-y-5">
            {/* 心率阈值 */}
            <div>
              <p className="text-lg font-medium text-gray-800 mb-3">心率范围 (bpm)</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-base text-gray-600 mb-1 block">最低值</label>
                  <input
                    type="number"
                    value={settings.healthThresholds.heartRate.min}
                    onChange={(e) => updateThreshold('heartRate', 'min', parseInt(e.target.value))}
                    className="w-full px-4 py-2 rounded-xl border-2 border-gray-200 text-lg focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-base text-gray-600 mb-1 block">最高值</label>
                  <input
                    type="number"
                    value={settings.healthThresholds.heartRate.max}
                    onChange={(e) => updateThreshold('heartRate', 'max', parseInt(e.target.value))}
                    className="w-full px-4 py-2 rounded-xl border-2 border-gray-200 text-lg focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            {/* 血压阈值 */}
            <div>
              <p className="text-lg font-medium text-gray-800 mb-3">血压范围 (mmHg)</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-base text-gray-600 mb-1 block">最低值</label>
                  <input
                    type="number"
                    value={settings.healthThresholds.bloodPressure.min}
                    onChange={(e) => updateThreshold('bloodPressure', 'min', parseInt(e.target.value))}
                    className="w-full px-4 py-2 rounded-xl border-2 border-gray-200 text-lg focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-base text-gray-600 mb-1 block">最高值</label>
                  <input
                    type="number"
                    value={settings.healthThresholds.bloodPressure.max}
                    onChange={(e) => updateThreshold('bloodPressure', 'max', parseInt(e.target.value))}
                    className="w-full px-4 py-2 rounded-xl border-2 border-gray-200 text-lg focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            {/* 体温阈值 */}
            <div>
              <p className="text-lg font-medium text-gray-800 mb-3">体温范围 (°C)</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-base text-gray-600 mb-1 block">最低值</label>
                  <input
                    type="number"
                    step="0.1"
                    value={settings.healthThresholds.temperature.min}
                    onChange={(e) => updateThreshold('temperature', 'min', parseFloat(e.target.value))}
                    className="w-full px-4 py-2 rounded-xl border-2 border-gray-200 text-lg focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-base text-gray-600 mb-1 block">最高值</label>
                  <input
                    type="number"
                    step="0.1"
                    value={settings.healthThresholds.temperature.max}
                    onChange={(e) => updateThreshold('temperature', 'max', parseFloat(e.target.value))}
                    className="w-full px-4 py-2 rounded-xl border-2 border-gray-200 text-lg focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 保存按钮 */}
        <button
          onClick={saveSettings}
          disabled={saving}
          className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xl font-bold rounded-2xl hover:from-indigo-700 hover:to-purple-700 transition-all active:scale-95 disabled:opacity-50 shadow-lg"
        >
          {saving ? '保存中...' : '保存设置'}
        </button>

        {/* 版本信息 */}
        <div className="bg-gray-50 rounded-2xl p-5 text-center">
          <p className="text-lg text-gray-600">智能养老助手 PWA</p>
          <p className="text-base text-gray-500 mt-1">版本 1.0.0</p>
          <p className="text-sm text-gray-400 mt-2">© 2024 MiniMax Agent</p>
        </div>
      </div>
    </div>
  )
}
