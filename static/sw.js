// Service Worker pour GLPIbis - Gestion offline et cache
const CACHE_NAME = 'glpibis-v1';
const WAITING_CACHE = 'glpibis-waiting-v1';

// Ressources essentielles à mettre en cache
const ESSENTIAL_RESOURCES = [
    '/waiting',
    '/static/script.js',
];

// HTML de la page waiting intégrée directement
const WAITING_PAGE_HTML = `
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GLPIbis - Redémarrage en cours...</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 4px solid #fff;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .status {
            margin-top: 20px;
            font-size: 14px;
            opacity: 0.8;
        }
        .retry-count {
            font-size: 12px;
            margin-top: 10px;
            opacity: 0.6;
        }
        .offline-mode {
            background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
        }
        .commenter {
            font-size: 12px;
            margin-top: 1px;
            color: #fff;
            opacity: 0.7;
            text-decoration: none;
        }
    </style>
</head>
<body class="offline-mode">
    <div class="container">
        <h1>GLPIbis</h1>
        <div class="spinner"></div>
        <p>Serveur indisponible - Mode hors ligne</p>
        <p class="status" id="status">Tentative de reconnexion...</p>
        <p class="retry-count" id="retryCount">Tentative: 1</p>
        <p class="commenter">Veuillez patienter pendant que nous essayons de rétablir la connexion.</p>
        <p class="commenter">Merci de votre patience !</p>
    </div>

    <script>
        let retryCount = 1;
        let maxRetries = 60;

        function updateStatus(message) {
            const statusEl = document.getElementById('status');
            if (statusEl) statusEl.textContent = message;
        }
        
        function updateRetryCount() {
            const retryEl = document.getElementById('retryCount');
            if (retryEl) retryEl.textContent = 'Tentative: ' + retryCount;
        }
        
        function checkServer() {
            fetch('/health', {
                method: 'HEAD',
                cache: 'no-cache'
            })
            .then(response => {
                if (response.ok) {
                    updateStatus('Serveur disponible ! Redirection...');
                    setTimeout(() => {
                        if (document.referrer && !document.referrer.includes('/waiting')) {
                            window.location.href = document.referrer;
                        } else {
                            window.location.href = '/';
                        }
                    }, 1000);
                } else {
                    throw new Error('Serveur non disponible');
                }
            })
            .catch(error => {
                retryCount++;
                updateRetryCount();
                
                if (retryCount > maxRetries) {
                    updateStatus('Le serveur met trop de temps à redémarrer. Veuillez actualiser manuellement.');
                    return;
                }
                
                updateStatus('Serveur non disponible, nouvelle tentative dans 5s...');
                setTimeout(checkServer, 5000);
            });
        }
        
        setTimeout(checkServer, 2000);
        updateRetryCount();
    </script>
</body>
</html>`;

// Installation du service worker
self.addEventListener('install', event => {
    console.log('[SW] Installation...');
    event.waitUntil(
        caches.open(WAITING_CACHE).then(cache => {
            // Stocker la page waiting directement dans le cache
            return cache.put('/waiting-offline', new Response(WAITING_PAGE_HTML, {
                headers: { 'Content-Type': 'text/html' }
            }));
        })
    );
    self.skipWaiting();
});

// Activation du service worker
self.addEventListener('activate', event => {
    console.log('[SW] Activation...');
    event.waitUntil(self.clients.claim());
});

// Interception des requêtes
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    
    // Si c'est une requête vers /waiting
    if (url.pathname === '/waiting') {
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    console.log('[SW] Serveur indisponible, retour version offline pour /waiting');
                    // Si le fetch échoue, retourner la version offline
                    return caches.match('/waiting-offline');
                })
        );
        return;
    }
    
    // Pour les requêtes de navigation (pages HTML)
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request, { cache: 'no-cache' })
                .catch(() => {
                    console.log('[SW] Navigation échouée, redirection vers waiting offline');
                    // Si la navigation échoue, rediriger vers la page waiting offline
                    return caches.match('/waiting-offline');
                })
        );
        return;
    }
    
    // Pour les autres requêtes (API, assets, etc.)
    if (url.pathname === '/health') {
        // Laisser les requêtes /health échouer normalement pour déclencher la logique JS
        event.respondWith(fetch(event.request));
        return;
    }
    
    // Pour toutes les autres requêtes, essayer le réseau
    event.respondWith(
        fetch(event.request)
            .catch(() => {
                // Si c'est une ressource critique, essayer le cache
                return caches.match(event.request);
            })
    );
});

// Message du client principal pour forcer la redirection
self.addEventListener('message', event => {
    if (event.data && event.data.action === 'redirect-to-waiting') {
        // Informer tous les clients de rediriger vers waiting
        self.clients.matchAll().then(clients => {
            clients.forEach(client => {
                client.postMessage({ action: 'go-to-waiting-offline' });
            });
        });
    }
});