self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open('junior-fretes-store').then((cache) => cache.addAll([
            './',
            './index.html',
            './manifest.json',
            './style.css',
            './script.js'
        ]))
    );
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request).then((response) => response || fetch(e.request))
    );
});
