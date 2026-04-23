// PWA工具函数

// 注册Service Worker
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      })
      console.log('Service Worker registered:', registration.scope)
      
      // 检查更新
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              console.log('New Service Worker available')
              // 可以提示用户刷新页面
            }
          })
        }
      })
      
      return registration
    } catch (error) {
      console.error('Service Worker registration failed:', error)
      return null
    }
  }
  return null
}

// 请求通知权限
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if ('Notification' in window) {
    const permission = await Notification.requestPermission()
    console.log('Notification permission:', permission)
    return permission
  }
  return 'denied'
}

// 显示通知
export function showNotification(title: string, options?: NotificationOptions) {
  if ('serviceWorker' in navigator && Notification.permission === 'granted') {
    navigator.serviceWorker.ready.then(registration => {
      registration.showNotification(title, {
        icon: '/icon-192.png',
        badge: '/badge-72.png',
        vibrate: [200, 100, 200],
        ...options
      })
    })
  }
}

// 获取地理位置
export function getCurrentPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      })
    } else {
      reject(new Error('Geolocation not supported'))
    }
  })
}

// 持续监听位置
export function watchPosition(
  callback: (position: GeolocationPosition) => void,
  errorCallback?: (error: GeolocationPositionError) => void
): number {
  if ('geolocation' in navigator) {
    return navigator.geolocation.watchPosition(callback, errorCallback, {
      enableHighAccuracy: true,
      timeout: 5000,
      maximumAge: 0
    })
  }
  return -1
}

// 语音合成
export function speak(text: string, options?: {
  lang?: string
  rate?: number
  pitch?: number
  volume?: number
}) {
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = options?.lang || 'zh-CN'
    utterance.rate = options?.rate || 0.8 // 适老化：放慢语速
    utterance.pitch = options?.pitch || 1
    utterance.volume = options?.volume || 1
    
    window.speechSynthesis.speak(utterance)
  }
}

// 语音识别
export function startVoiceRecognition(
  onResult: (transcript: string) => void,
  onError?: (error: any) => void
): any {
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
    const recognition = new SpeechRecognition()
    
    recognition.lang = 'zh-CN'
    recognition.continuous = false
    recognition.interimResults = false
    
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      onResult(transcript)
    }
    
    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error)
      onError?.(event.error)
    }
    
    recognition.start()
    return recognition
  }
  
  return null
}

// 检查网络状态
export function isOnline(): boolean {
  return navigator.onLine
}

// 监听网络状态变化
export function onNetworkChange(callback: (online: boolean) => void) {
  window.addEventListener('online', () => callback(true))
  window.addEventListener('offline', () => callback(false))
}

// 检查是否安装为PWA
export function isPWA(): boolean {
  return window.matchMedia('(display-mode: standalone)').matches ||
         (window.navigator as any).standalone === true
}

// 提示安装PWA
export function promptPWAInstall(deferredPrompt: any) {
  if (deferredPrompt) {
    deferredPrompt.prompt()
    deferredPrompt.userChoice.then((choiceResult: any) => {
      console.log('PWA install choice:', choiceResult.outcome)
    })
  }
}

// 振动提醒
export function vibrate(pattern: number | number[]) {
  if ('vibrate' in navigator) {
    navigator.vibrate(pattern)
  }
}

// 离线数据存储（使用IndexedDB）
export const offlineDB = {
  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('ElderlyCarePWA', 1)
      
      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve(request.result)
      
      request.onupgradeneeded = (event) => {
        const db = (event.target as any).result
        
        if (!db.objectStoreNames.contains('healthData')) {
          db.createObjectStore('healthData', { keyPath: 'id', autoIncrement: true })
        }
        
        if (!db.objectStoreNames.contains('syncQueue')) {
          db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true })
        }
      }
    })
  },
  
  async addToSyncQueue(data: any) {
    const db: any = await this.init()
    const transaction = db.transaction(['syncQueue'], 'readwrite')
    const store = transaction.objectStore('syncQueue')
    
    return new Promise((resolve, reject) => {
      const request = store.add({ ...data, timestamp: Date.now() })
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  },
  
  async getSyncQueue() {
    const db: any = await this.init()
    const transaction = db.transaction(['syncQueue'], 'readonly')
    const store = transaction.objectStore('syncQueue')
    
    return new Promise((resolve, reject) => {
      const request = store.getAll()
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  },
  
  async clearSyncQueue() {
    const db: any = await this.init()
    const transaction = db.transaction(['syncQueue'], 'readwrite')
    const store = transaction.objectStore('syncQueue')
    
    return new Promise((resolve, reject) => {
      const request = store.clear()
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })
  }
}
