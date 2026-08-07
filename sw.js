// Jinba Auto Export - Service Worker
const CACHE_NAME = 'jinba-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/cars.html',
  '/cars-detail.html',
  '/about.html',
  '/services.html',
  '/contact.html',
  '/404.html',
  '/js/cars-data.js',
  '/js/i18n.js',
  '/css/style.css',
  '/sitemap.xml'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(name => {
          if (name !== CACHE_NAME) return caches.delete(name);
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request).then(resp => {
        return caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, resp.clone());
          return resp;
        });
      }).catch(() => caches.match('/404.html'))
  );
});
