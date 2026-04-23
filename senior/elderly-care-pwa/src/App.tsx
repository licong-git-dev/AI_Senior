import React, { useState, useEffect } from 'react'
import { registerServiceWorker, requestNotificationPermission, offlineDB } from './lib/pwa-utils'
import BottomNav from './components/BottomNav'
import Dashboard from './pages/Dashboard'
import Monitor from './pages/Monitor'
import Emergency from './pages/Emergency'
import Analysis from './pages/Analysis'
import Care from './pages/Care'
import Settings from './pages/Settings'
import './App.css'

// PWA安装提示组件
function InstallPrompt({ onInstall, onDismiss }: { onInstall: () => void; onDismiss: () => void }) {
  return (
    <div className="fixed top-4 left-4 right-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4 rounded-2xl shadow-lg z-50 animate-slide-down">
      <p className="text-lg font-bold mb-2">安装智能养老助手</p>
      <p className="text-sm text-indigo-100 mb-3">
        安装到主屏幕，随时随地关注健康
      </p>
      <div className="flex space-x-3">
        <button
          onClick={onInstall}
          className="flex-1 py-2 bg-white text-indigo-600 font-bold rounded-xl hover:bg-indigo-50 transition-colors"
        >
          安装
        </button>
        <button
          onClick={onDismiss}
          className="flex-1 py-2 bg-white/20 text-white font-bold rounded-xl hover:bg-white/30 transition-colors"
        >
          稍后
        </button>
      </div>
    </div>
  )
}

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null)
  const [showInstallPrompt, setShowInstallPrompt] = useState(false)
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  // 初始化PWA
  useEffect(() => {
    // 注册Service Worker
    registerServiceWorker().then((registration) => {
      console.log('Service Worker registered:', registration)
    })

    // 请求通知权限
    requestNotificationPermission().then((permission) => {
      console.log('Notification permission:', permission)
    })

    // 初始化离线数据库
    offlineDB.init().then(() => {
      console.log('Offline database initialized')
    })

    // 监听安装提示事件
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e)
      // 延迟显示安装提示
      setTimeout(() => {
        setShowInstallPrompt(true)
      }, 3000)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

    // 监听网络状态
    const handleOnline = () => {
      setIsOnline(true)
      console.log('App is online')
      // 触发离线数据同步
      if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
        navigator.serviceWorker.ready.then((registration: any) => {
          registration.sync.register('sync-health-data')
        })
      }
    }

    const handleOffline = () => {
      setIsOnline(false)
      console.log('App is offline')
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // 清理
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // 处理PWA安装
  const handleInstall = () => {
    if (deferredPrompt) {
      deferredPrompt.prompt()
      deferredPrompt.userChoice.then((choiceResult: any) => {
        if (choiceResult.outcome === 'accepted') {
          console.log('User accepted the install prompt')
        }
        setDeferredPrompt(null)
        setShowInstallPrompt(false)
      })
    }
  }

  // 渲染当前页面
  const renderPage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />
      case 'monitor':
        return <Monitor />
      case 'emergency':
        return <Emergency />
      case 'analysis':
        return <Analysis />
      case 'care':
        return <Care />
      case 'settings':
        return <Settings />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="App min-h-screen bg-gray-50">
      {/* PWA安装提示 */}
      {showInstallPrompt && (
        <InstallPrompt
          onInstall={handleInstall}
          onDismiss={() => setShowInstallPrompt(false)}
        />
      )}

      {/* 离线提示 */}
      {!isOnline && (
        <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-white text-center py-2 z-40">
          <span className="text-sm font-medium">
            当前处于离线模式，数据将在联网后自动同步
          </span>
        </div>
      )}

      {/* 主内容区域 */}
      <main className="relative">
        {renderPage()}
      </main>

      {/* 底部导航栏 */}
      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  )
}

export default App
