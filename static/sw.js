self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open('smart-parking-v1').then(function(cache) {
      return cache.addAll([
        '/',
        '/login',
        '/static/styles.css',
        '/static/manifest.json',
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
        'https://cdn-icons-png.flaticon.com/512/743/743007.png'
      ]);
    })
  );
});

self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});
