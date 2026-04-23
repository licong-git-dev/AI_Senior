// Service Worker - 智能养老平台PWA
const CACHE_NAME = 'elderly-care-v1';
const API_CACHE = 'api-cache-v1';
const DATA_CACHE = 'data-cache-v1';

// 需要预缓存的静态资源
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/manifest.json'
];

// 安装事件 - 预缓存静态资源
self.addEventListener('install', event => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Precaching static assets');
        return cache.addAll(PRECACHE_URLS);
      })
      .then(() => self.skipWaiting())
  );
});

// 激活事件 - 清理旧缓存
self.addEventListener('activate', event => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME && name !== API_CACHE && name !== DATA_CACHE)
          .map(name => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// 请求拦截 - 缓存优先策略
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // API请求 - 网络优先，失败则使用缓存
  if (url.origin.includes('supabase.co')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // 克隆响应以便缓存
          const responseClone = response.clone();
          caches.open(API_CACHE).then(cache => {
            cache.put(request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // 网络失败，返回缓存
          return caches.match(request).then(cached => {
            if (cached) {
              console.log('[SW] Using cached API response:', request.url);
              return cached;
            }
            // 返回离线页面
            return new Response(JSON.stringify({
              error: 'Network unavailable',
              offline: true,
              message: '当前网络不可用，请检查网络连接'
            }), {
              status: 503,
              headers: { 'Content-Type': 'application/json' }
            });
          });
        })
    );
    return;
  }

  // 静态资源 - 缓存优先
  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) {
        console.log('[SW] Serving from cache:', request.url);
        return cached;
      }

      return fetch(request).then(response => {
        // 只缓存成功的GET请求
        if (request.method === 'GET' && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(request, responseClone);
          });
        }
        return response;
      });
    }).catch(() => {
      // 返回离线页面
      if (request.destination === 'document') {
        return caches.match('/index.html');
      }
    })
  );
});

// 后台同步 - 离线数据同步
self.addEventListener('sync', event => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'sync-health-data') {
    event.waitUntil(syncHealthData());
  }
});

// 推送通知
self.addEventListener('push', event => {
  console.log('[SW] Push notification received');
  
  const data = event.data ? event.data.json() : {};
  const title = data.title || '智能养老助手';
  const options = {
    body: data.body || '您有新的健康提醒',
    icon: '/icon-192.png',
    badge: '/badge-72.png',
    vibrate: [200, 100, 200],
    data: data.data || {},
    actions: data.actions || [
      { action: 'view', title: '查看详情' },
      { action: 'dismiss', title: '忽略' }
    ],
    requireInteraction: data.requireInteraction || false
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// 通知点击事件
self.addEventListener('notificationclick', event => {
  console.log('[SW] Notification clicked:', event.action);
  
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow(event.notification.data.url || '/')
    );
  }
});

// 同步健康数据函数
async function syncHealthData() {
  try {
    // 从IndexedDB获取离线数据
    const offlineData = await getOfflineData();
    
    if (offlineData.length === 0) {
      console.log('[SW] No offline data to sync');
      return;
    }

    // 发送到服务器
    const response = await fetch('/api/sync-health-data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(offlineData)
    });

    if (response.ok) {
      console.log('[SW] Health data synced successfully');
      await clearOfflineData();
    }
  } catch (error) {
    console.error('[SW] Failed to sync health data:', error);
    throw error;
  }
}

// 模拟IndexedDB操作（实际应使用真实的IndexedDB）
async function getOfflineData() {
  // TODO: 实现实际的IndexedDB读取
  return [];
}

async function clearOfflineData() {
  // TODO: 实现实际的IndexedDB清理
}

console.log('[SW] Service Worker loaded');
