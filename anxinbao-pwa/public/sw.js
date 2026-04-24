/**
 * 安心宝 PWA Service Worker
 *
 * 设计原则：
 * 1. **API 永不缓存** —— /api/* 全部走网络，避免老人看到陈旧的健康数据
 * 2. **静态资源 stale-while-revalidate** —— 离线可用 + 在线时静默更新
 * 3. **CACHE_NAME 必须随每次发布递增** —— 否则浏览器无法识别新版本，老人卡在旧 UI
 * 4. **不缓存 sw.js / index.html** —— 否则更新链路自己被卡死
 * 5. **缓存大小有限** —— 老人设备空间不足时不能让 PWA 自己变成黑洞
 */

// 每次发布递增（与 anxinbao-pwa/package.json 的 version 同步）
// v1: 初版 (2026-04 r0)  ·  v2: 修缓存范围 + 大小限制 (2026-04 r8)
const CACHE_VERSION = 'v2';
const CACHE_NAME = `anxinbao-${CACHE_VERSION}`;

// 离线兜底白名单：只缓存"必有就能开"的资源
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
];

// 缓存大小上限：超过这个数量就 LRU 删旧的（保护老人设备空间）
const MAX_CACHE_ITEMS = 60;

// 不能缓存的路径前缀（走网络优先 + 不写缓存）
const NO_CACHE_PREFIXES = [
  '/api/',           // 接口数据必须实时
  '/sw.js',          // service worker 自身
  '/health',         // 健康探针
  '/metrics',        // Prometheus
];

// HTML 入口：使用 network-first，避免老人卡在旧 UI（更新关键）
const HTML_PATHS = ['/', '/index.html'];

// ===== install =====
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// ===== activate：清理旧版本缓存 =====
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name.startsWith('anxinbao-') && name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// ===== fetch =====
self.addEventListener('fetch', (event) => {
  const { request } = event;
  // 只处理 GET（POST / PUT / DELETE 永远不缓存）
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // 1) API 等敏感路径：网络优先 + 离线兜底友好响应（不缓存）
  if (NO_CACHE_PREFIXES.some((p) => url.pathname.startsWith(p))) {
    event.respondWith(
      fetch(request).catch(() => {
        if (url.pathname.startsWith('/api/')) {
          return new Response(
            JSON.stringify({
              error: '当前离线，无法连接服务器',
              code: 'offline',
              hint: '请检查网络后重试；紧急情况请直接电话联系家人',
            }),
            {
              status: 503,
              headers: { 'Content-Type': 'application/json; charset=utf-8' },
            }
          );
        }
        return new Response('offline', { status: 503 });
      })
    );
    return;
  }

  // 2) HTML 入口：network-first（拿不到才用缓存），避免卡旧 UI
  if (HTML_PATHS.includes(url.pathname) || request.destination === 'document') {
    event.respondWith(
      fetch(request)
        .then((resp) => {
          // 入口 HTML 不长期缓存，仅供离线兜底
          const clone = resp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          return resp;
        })
        .catch(() => caches.match(request) || caches.match('/'))
    );
    return;
  }

  // 3) 其它静态资源：stale-while-revalidate
  event.respondWith(
    caches.match(request).then((cached) => {
      const networkFetch = fetch(request)
        .then((resp) => {
          if (resp && resp.status === 200 && resp.type === 'basic') {
            const clone = resp.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, clone);
              trimCache(cache, MAX_CACHE_ITEMS);
            });
          }
          return resp;
        })
        .catch(() => cached); // 网络挂了用缓存
      return cached || networkFetch;
    })
  );
});

// LRU 风格的缓存裁剪（粗粒度但够用）
async function trimCache(cache, maxItems) {
  const keys = await cache.keys();
  if (keys.length <= maxItems) return;
  const toDelete = keys.length - maxItems;
  for (let i = 0; i < toDelete; i++) {
    await cache.delete(keys[i]);
  }
}

// ===== 推送通知 =====
self.addEventListener('push', (event) => {
  const data = event.data?.json() || {};
  const options = {
    body: data.body || '您有新的健康提醒',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    vibrate: [200, 100, 200],
    tag: 'health-notification',
    requireInteraction: true,
    actions: [
      { action: 'view', title: '查看详情' },
      { action: 'dismiss', title: '稍后提醒' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || '安心宝提醒', options)
  );
});

// ===== 通知点击 =====
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(clients.openWindow('/'));
  }
});

// ===== 让前端能显式触发更新（用于"我刷新没反应"场景）=====
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
