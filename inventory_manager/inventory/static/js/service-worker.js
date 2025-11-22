// Service worker for Web Push notifications.
// Push event'lerini dinler ve gelen payload'a göre bildirim gösterir.

self.addEventListener('push', function(event) {
    let data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            // JSON parse edilemezse düz text kullan
            data = { head: 'Bildirim', body: event.data.text() };
        }
    }

    const title = data.head || 'Bildirim';
    const options = {
        body: data.body || '',
        icon: data.icon || '/static/img/icons/icon-192x192.png',
        data: {
            url: data.url || '/'
        }
    };

    // Bildirimin güvenilir şekilde gösterilmesi için waitUntil
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Bildirime tıklanınca ilgili sayfaya git / o sekmeyi fokusla
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    const url = event.notification.data.url;

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url === url && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});
