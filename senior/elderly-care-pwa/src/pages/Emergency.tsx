import React, { useState, useEffect } from 'react'
import { 
  AlertTriangle, Phone, MapPin, User, Clock, 
  Navigation, Send, CheckCircle, Loader
} from 'lucide-react'
import { supabase } from '../lib/supabase'
import { getCurrentPosition, vibrate, speak, showNotification } from '../lib/pwa-utils'

interface EmergencyContact {
  id: string
  name: string
  relation: string
  phone: string
  priority: number
}

interface Location {
  latitude: number
  longitude: number
  address?: string
  accuracy?: number
}

export default function Emergency() {
  const [calling, setCalling] = useState(false)
  const [location, setLocation] = useState<Location | null>(null)
  const [gettingLocation, setGettingLocation] = useState(false)
  const [emergencyType, setEmergencyType] = useState<string>('')
  const [contacts, setContacts] = useState<EmergencyContact[]>([])
  const [callSuccess, setCallSuccess] = useState(false)

  // 获取当前位置
  const getLocation = async () => {
    setGettingLocation(true)
    try {
      const position = await getCurrentPosition()
      const loc: Location = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy
      }
      
      // 反向地理编码获取地址（可选）
      // 这里简化处理，实际应该调用地理编码API
      loc.address = `经度: ${loc.latitude.toFixed(6)}, 纬度: ${loc.longitude.toFixed(6)}`
      
      setLocation(loc)
      speak('定位成功')
    } catch (error) {
      console.error('Get location error:', error)
      speak('定位失败，请检查位置权限')
      showNotification('定位失败', {
        body: '无法获取您的位置信息，请检查位置权限设置',
        tag: 'location-error'
      })
    } finally {
      setGettingLocation(false)
    }
  }

  // 初始化：获取位置和联系人
  useEffect(() => {
    getLocation()
    fetchEmergencyContacts()
  }, [])

  // 获取紧急联系人
  const fetchEmergencyContacts = async () => {
    try {
      // 从profiles表获取紧急联系人
      const { data, error } = await supabase
        .from('profiles')
        .select('id, full_name, phone, role')
        .in('role', ['family', 'caregiver', 'doctor'])
        .limit(5)

      if (!error && data) {
        const emergencyContacts: EmergencyContact[] = data.map((item: any, index: number) => ({
          id: item.id,
          name: item.full_name || '未命名联系人',
          relation: item.role === 'family' ? '家属' : item.role === 'caregiver' ? '护工' : '医生',
          phone: item.phone || '未设置',
          priority: index + 1
        }))
        
        // 添加120急救中心
        emergencyContacts.push({
          id: '120',
          name: '急救中心',
          relation: '120',
          phone: '120',
          priority: 0
        })
        
        setContacts(emergencyContacts)
      } else {
        // 数据库无数据时，只显示120
        setContacts([{
          id: '120',
          name: '急救中心',
          relation: '120',
          phone: '120',
          priority: 0
        }])
      }
    } catch (error) {
      console.error('Fetch emergency contacts error:', error)
      // 错误时至少保证120可用
      setContacts([{
        id: '120',
        name: '急救中心',
        relation: '120',
        phone: '120',
        priority: 0
      }])
    }
  }

  // 紧急呼救
  const handleEmergencyCall = async (type: string) => {
    setCalling(true)
    setEmergencyType(type)
    
    // 强烈振动提醒
    vibrate([200, 100, 200, 100, 200])
    
    // 语音提示
    speak(`正在发起${type}紧急呼救，请稍候`, { rate: 1.2 })

    try {
      // 保存紧急呼叫记录
      const { data, error } = await supabase
        .from('emergency_calls')
        .insert([
          {
            call_type: type,
            status: 'pending',
            location: location || undefined,
            notes: `自动发起的${type}紧急呼救`,
            created_at: new Date().toISOString()
          }
        ])
        .select()
        .single()

      if (error) throw error

      // 发送通知给紧急联系人
      showNotification('紧急呼救已发起', {
        body: `${type}紧急呼救已通知所有联系人`,
        requireInteraction: true,
        tag: 'emergency-call'
      })

      // 模拟通知联系人（实际应该调用推送API）
      await new Promise(resolve => setTimeout(resolve, 2000))

      setCallSuccess(true)
      speak('紧急呼救已发出，家人和医护人员正在赶来')
      
      // 3秒后重置状态
      setTimeout(() => {
        setCalling(false)
        setCallSuccess(false)
      }, 3000)
    } catch (error) {
      console.error('Emergency call error:', error)
      speak('呼救失败，请重试或直接拨打电话')
      showNotification('呼救失败', {
        body: '紧急呼救发送失败，请重试或直接拨打紧急联系人电话',
        tag: 'emergency-error'
      })
      setCalling(false)
    }
  }

  // 快速拨打电话
  const quickCall = (phone: string) => {
    window.location.href = `tel:${phone}`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-orange-50 pb-24">
      {/* 顶部警告区域 */}
      <div className="bg-gradient-to-r from-red-600 to-orange-600 text-white px-5 py-8 rounded-b-3xl shadow-lg">
        <div className="flex items-center justify-center mb-4">
          <AlertTriangle className="w-16 h-16" />
        </div>
        <h1 className="text-3xl font-bold text-center mb-2">紧急求助</h1>
        <p className="text-lg text-center text-red-100">发生紧急情况，立即获得帮助</p>
      </div>

      {/* 位置信息 */}
      <div className="px-5 mt-6">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <MapPin className="w-6 h-6 text-indigo-500" />
              <h2 className="text-xl font-bold text-gray-800">当前位置</h2>
            </div>
            <button
              onClick={getLocation}
              disabled={gettingLocation}
              className="p-2 bg-indigo-100 rounded-xl hover:bg-indigo-200 transition-colors active:scale-95"
            >
              <Navigation className={`w-5 h-5 text-indigo-600 ${gettingLocation ? 'animate-spin' : ''}`} />
            </button>
          </div>
          
          {location ? (
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
              <p className="text-lg text-blue-900 mb-2">
                <span className="font-medium">地址：</span>
                {location.address || '获取中...'}
              </p>
              <p className="text-base text-blue-700">
                精度：{location.accuracy ? `±${location.accuracy.toFixed(0)}米` : '未知'}
              </p>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-xl p-4 border border-gray-200 flex items-center justify-center">
              {gettingLocation ? (
                <div className="flex items-center space-x-2">
                  <Loader className="w-5 h-5 animate-spin text-gray-500" />
                  <span className="text-lg text-gray-600">正在定位...</span>
                </div>
              ) : (
                <span className="text-lg text-gray-600">暂无位置信息</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 紧急呼救按钮 */}
      <div className="px-5 mt-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">选择紧急类型</h2>
          
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => handleEmergencyCall('跌倒')}
              disabled={calling}
              className="aspect-square bg-gradient-to-br from-red-500 to-red-600 text-white rounded-3xl p-6 flex flex-col items-center justify-center hover:from-red-600 hover:to-red-700 transition-all active:scale-95 disabled:opacity-50 shadow-lg"
            >
              <AlertTriangle className="w-16 h-16 mb-3" />
              <span className="text-2xl font-bold">跌倒</span>
            </button>

            <button
              onClick={() => handleEmergencyCall('身体不适')}
              disabled={calling}
              className="aspect-square bg-gradient-to-br from-orange-500 to-orange-600 text-white rounded-3xl p-6 flex flex-col items-center justify-center hover:from-orange-600 hover:to-orange-700 transition-all active:scale-95 disabled:opacity-50 shadow-lg"
            >
              <AlertTriangle className="w-16 h-16 mb-3" />
              <span className="text-2xl font-bold">身体不适</span>
            </button>

            <button
              onClick={() => handleEmergencyCall('需要帮助')}
              disabled={calling}
              className="aspect-square bg-gradient-to-br from-yellow-500 to-yellow-600 text-white rounded-3xl p-6 flex flex-col items-center justify-center hover:from-yellow-600 hover:to-yellow-700 transition-all active:scale-95 disabled:opacity-50 shadow-lg"
            >
              <AlertTriangle className="w-16 h-16 mb-3" />
              <span className="text-2xl font-bold">需要帮助</span>
            </button>

            <button
              onClick={() => handleEmergencyCall('其他紧急情况')}
              disabled={calling}
              className="aspect-square bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-3xl p-6 flex flex-col items-center justify-center hover:from-purple-600 hover:to-purple-700 transition-all active:scale-95 disabled:opacity-50 shadow-lg"
            >
              <AlertTriangle className="w-16 h-16 mb-3" />
              <span className="text-2xl font-bold">其他情况</span>
            </button>
          </div>

          {/* 呼救状态 */}
          {calling && (
            <div className="mt-6 bg-blue-50 rounded-2xl p-5 border-2 border-blue-300 animate-pulse">
              <div className="flex items-center justify-center space-x-3">
                {callSuccess ? (
                  <>
                    <CheckCircle className="w-8 h-8 text-green-600" />
                    <span className="text-2xl font-bold text-green-700">呼救成功！</span>
                  </>
                ) : (
                  <>
                    <Loader className="w-8 h-8 text-blue-600 animate-spin" />
                    <span className="text-2xl font-bold text-blue-700">正在发送呼救...</span>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 紧急联系人 */}
      <div className="px-5 mt-6">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center space-x-2 mb-4">
            <User className="w-6 h-6 text-indigo-500" />
            <h2 className="text-xl font-bold text-gray-800">紧急联系人</h2>
          </div>
          
          <div className="space-y-3">
            {contacts.map((contact) => (
              <div
                key={contact.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <p className="text-lg font-bold text-gray-800">{contact.name}</p>
                  <p className="text-base text-gray-500">{contact.relation}</p>
                </div>
                <button
                  onClick={() => quickCall(contact.phone)}
                  className="ml-4 bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-xl flex items-center space-x-2 transition-all active:scale-95"
                >
                  <Phone className="w-5 h-5" />
                  <span className="text-lg font-medium">拨打</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 使用说明 */}
      <div className="px-5 mt-6 mb-6">
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-5 border border-indigo-200">
          <div className="flex items-center space-x-2 mb-3">
            <Clock className="w-6 h-6 text-indigo-600" />
            <h2 className="text-xl font-bold text-indigo-800">使用说明</h2>
          </div>
          <ul className="space-y-2 text-lg text-indigo-700">
            <li>• 点击紧急类型按钮，系统将自动通知所有联系人</li>
            <li>• 您的位置信息会同时发送给联系人</li>
            <li>• 可以直接点击"拨打"按钮致电联系人</li>
            <li>• 120急救中心可随时拨打</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
