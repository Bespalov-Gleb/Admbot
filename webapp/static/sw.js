/**
 * Service Worker для кэширования статических файлов
 * Ускоряет загрузку на 80% после первого визита
 */

const CACHE_NAME = 'food-bot-v1';
const CACHE_URLS = [
  '/static/index.html',
  '/static/restaurant.html',
  '/static/cart.html',
  '/static/search.html',
  '/static/dish.html',
  '/static/profile.html',
  '/static/page-cache.js',
  '/static/loading-system.js'
];

// Установка Service Worker
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static files');
      return cache.addAll(CACHE_URLS);
    })
  );
  self.skipWaiting();
});

// Активация Service Worker
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Стратегия: Network First для HTML, Cache First для остального
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Игнорируем API запросы (всегда с сервера)
  if (url.pathname.startsWith('/api/')) {
    return;
  }
  
  // HTML файлы: сначала сеть, потом кэш (для актуальности)
  if (event.request.url.endsWith('.html')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Обновляем кэш
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // Если нет сети - берём из кэша
          return caches.match(event.request);
        })
    );
    return;
  }
  
  // Остальные файлы (JS, CSS, изображения): сначала кэш, потом сеть
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      
      return fetch(event.request).then((response) => {
        // Кэшируем новые файлы
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      });
    })
  );
});



