import React from 'react'
import { Home, Activity, AlertTriangle, Brain, Settings } from 'lucide-react'

interface BottomNavProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

const tabs = [
  { id: 'dashboard', label: '首页', icon: Home },
  { id: 'monitor', label: '监测', icon: Activity },
  { id: 'emergency', label: '紧急', icon: AlertTriangle, highlight: true },
  { id: 'analysis', label: '分析', icon: Brain },
  { id: 'settings', label: '设置', icon: Settings }
]

export default function BottomNav({ activeTab, onTabChange }: BottomNavProps) {
  const handleTabClick = (tabId: string) => {
    console.log('Tab clicked:', tabId)
    onTabChange(tabId)
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50">
      <div className="flex items-center justify-around px-2 py-2 safe-area-pb">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          const isEmergency = tab.highlight

          return (
            <button
              key={tab.id}
              data-tab-id={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`flex flex-col items-center justify-center py-2 px-3 rounded-2xl transition-all ${
                isActive
                  ? isEmergency
                    ? 'bg-red-500 text-white shadow-lg transform scale-110'
                    : 'bg-indigo-100 text-indigo-600'
                  : isEmergency
                    ? 'bg-red-100 text-red-600 hover:bg-red-200 transform scale-110'
                    : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Icon 
                className={`${isActive && isEmergency ? 'w-8 h-8 animate-pulse' : 'w-7 h-7'}`}
                strokeWidth={isActive ? 2.5 : 2}
              />
              <span className={`text-xs mt-1 font-medium ${
                isActive ? 'font-bold' : ''
              }`}>
                {tab.label}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
