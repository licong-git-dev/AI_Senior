/**
 * Service Worker for 安心宝 PWA
 * 提供离线支持和推送通知功能
 */

const CACHE_NAME = 'anxinbao-v1';
const STATIC_CACHE = 'anxinbao-static-v1';
const DYNAMIC_CACHE = 'anxinbao-dynamic-v1';

// 需要缓存的静态资源
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// 需要网络优先的API路径
const NETWORK_FIRST_PATHS = [
  '/api/health',
  '/api/alerts',
  '/api/devices',
  '/api/auth'
];

// 安装事件 - 缓存静态资源
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Static assets cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Failed to cache static assets:', error);
      })
  );
});

// 激活事件 - 清理旧缓存
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => {
              return name !== STATIC_CACHE && name !== DYNAMIC_CACHE;
            })
            .map((name) => {
              console.log('[SW] Removing old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('[SW] Service worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch事件 - 处理网络请求
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 跳过非同源请求
  if (url.origin !== location.origin) {
    return;
  }

  // API请求 - 网络优先，失败时使用缓存
  if (isApiRequest(url.pathname)) {
    event.respondWith(networkFirst(request));
    return;
  }

  // 静态资源 - 缓存优先
  event.respondWith(cacheFirst(request));
});

// 缓存优先策略
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    // 后台更新缓存
    fetchAndCache(request);
    return cachedResponse;
  }

  return fetchAndCache(request);
}

// 网络优先策略
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);

    // 缓存成功的GET请求
    if (request.method === 'GET' && networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network request failed, trying cache:', request.url);

    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
      return cachedResponse;
    }

    // 返回离线页面（针对导航请求）
    if (request.mode === 'navigate') {
      return caches.match('/offline.html');
    }

    throw error;
  }
}

// 获取并缓存
async function fetchAndCache(request) {
  try {
    const networkResponse = await fetch(request);

    if (request.method === 'GET' && networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.error('[SW] Fetch failed:', error);
    throw error;
  }
}

// 判断是否为API请求
function isApiRequest(pathname) {
  return NETWORK_FIRST_PATHS.some((path) => pathname.startsWith(path));
}

// 推送通知事件
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');

  let data = {
    title: '安心宝',
    body: '您有新的通知',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    tag: 'default',
    requireInteraction: false
  };

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (error) {
      console.error('[SW] Failed to parse push data:', error);
    }
  }

  const options = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    tag: data.tag,
    data: data.data || {},
    requireInteraction: data.requireInteraction,
    actions: data.actions || [],
    vibrate: [200, 100, 200]
  };

  // 紧急告警使用特殊配置
  if (data.type === 'sos' || data.type === 'critical') {
    options.requireInteraction = true;
    options.vibrate = [500, 200, 500, 200, 500];
    options.actions = [
      { action: 'view', title: '查看详情' },
      { action: 'call', title: '拨打电话' }
    ];
  }

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// 通知点击事件
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.action);

  event.notification.close();

  const data = event.notification.data || {};
  let targetUrl = '/';

  // 根据通知类型和操作确定跳转URL
  if (event.action === 'view') {
    targetUrl = data.url || '/alerts';
  } else if (event.action === 'call') {
    // 处理拨打电话
    if (data.phone) {
      targetUrl = `tel:${data.phone}`;
    }
  } else {
    // 默认点击通知体
    targetUrl = data.url || '/';
  }

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // 如果已有窗口打开，聚焦并导航
        for (const client of clientList) {
          if ('focus' in client) {
            return client.focus().then(() => {
              if (client.navigate) {
                return client.navigate(targetUrl);
              }
            });
          }
        }

        // 否则打开新窗口
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
  );
});

// 通知关闭事件
self.addEventListener('notificationclose', (event) => {
  console.log('[SW] Notification closed');
});

// 后台同步事件
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-health-data') {
    event.waitUntil(syncHealthData());
  }
});

// 同步健康数据
async function syncHealthData() {
  try {
    // 获取本地存储的待同步数据
    const cache = await caches.open(DYNAMIC_CACHE);
    const pendingData = await cache.match('/pending-sync');

    if (pendingData) {
      const data = await pendingData.json();

      // 发送到服务器
      const response = await fetch('/api/health/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        // 清除待同步数据
        await cache.delete('/pending-sync');
        console.log('[SW] Health data synced successfully');
      }
    }
  } catch (error) {
    console.error('[SW] Failed to sync health data:', error);
    throw error;
  }
}

// 消息处理
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);

  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((names) => {
        return Promise.all(names.map((name) => caches.delete(name)));
      })
    );
  }
});
