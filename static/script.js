document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("myForm");
    const inputValue = document.getElementById("input_value");
    const savedValueDisplay = document.getElementById("saved_value");

    // Vérifier que les éléments existent avant de les utiliser
    if (form && inputValue && savedValueDisplay) {
        // Charger la valeur sauvegardée au chargement de la page
        const savedValue = localStorage.getItem("savedValue");
        if (savedValue) {
            savedValueDisplay.textContent = savedValue;
        }

        form.addEventListener("submit", function(event) {
            const value = inputValue.value;
            // Sauvegarder la valeur dans le stockage local
            localStorage.setItem("savedValue", value);
            // Mettre à jour l'affichage
            savedValueDisplay.textContent = value;
            // Réinitialiser le formulaire
            form.reset();
        });
    }
    
    // Fonctionnalité pour le formulaire de création de tickets
    const typeSelect = document.getElementById('type');
    const categorieSelect = document.getElementById('categorie');
    
    if (typeSelect && categorieSelect) {
        // Définition des catégories pour chaque type
        const categoriesByType = {
            'hardware': [
                {value: 'desktop', text: 'Ordinateur de bureau'},
                {value: 'laptop', text: 'Ordinateur portable'},
                {value: 'printer', text: 'Imprimante'},
                {value: 'scanner', text: 'Scanner'},
                {value: 'phone', text: 'Téléphone'},
                {value: 'peripheral', text: 'Périphérique'},
                {value: 'other_hw', text: 'Autre matériel'}
            ],
            'software': [
                {value: 'os', text: 'Système d\'exploitation'},
                {value: 'office', text: 'Suite bureautique'},
                {value: 'email', text: 'Email / Messagerie'},
                {value: 'browser', text: 'Navigateur web'},
                {value: 'antivirus', text: 'Antivirus / Sécurité'},
                {value: 'erp', text: 'ERP / Logiciel métier'},
                {value: 'other_sw', text: 'Autre logiciel'}
            ],
            'network': [
                {value: 'internet', text: 'Connexion Internet'},
                {value: 'wifi', text: 'Wi-Fi'},
                {value: 'lan', text: 'Réseau local (LAN)'},
                {value: 'vpn', text: 'VPN'},
                {value: 'other_net', text: 'Autre problème réseau'}
            ],
            'security': [
                {value: 'password', text: 'Problème de mot de passe'},
                {value: 'access_denied', text: 'Accès refusé'},
                {value: 'virus', text: 'Virus / Malware'},
                {value: 'data_breach', text: 'Fuite de données'},
                {value: 'other_sec', text: 'Autre problème de sécurité'}
            ],
            'access': [
                {value: 'new_account', text: 'Création de compte'},
                {value: 'permissions', text: 'Demande de permissions'},
                {value: 'software_install', text: 'Installation de logiciel'},
                {value: 'other_acc', text: 'Autre demande d\'accès'}
            ],
            'other': [
                {value: 'training', text: 'Formation'},
                {value: 'consultation', text: 'Consultation'},
                {value: 'info', text: 'Demande d\'information'},
                {value: 'other_req', text: 'Autre demande'}
            ]
        };
        
        // Fonction globale pour mettre à jour les catégories
        window.updateCategories = function() {
            const selectedType = typeSelect.value;
            console.log('Type sélectionné:', selectedType);
            
            // Vider le select de catégories
            categorieSelect.innerHTML = '';
            
            // Désactiver si aucun type n'est sélectionné
            if (!selectedType) {
                categorieSelect.disabled = true;
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'Sélectionnez d\'abord un type';
                option.selected = true;
                categorieSelect.appendChild(option);
                return;
            }
            
            // Activer le select
            categorieSelect.disabled = false;
            
            // Ajouter l'option par défaut
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Sélectionnez une catégorie';
            defaultOption.selected = true;
            defaultOption.disabled = true;
            categorieSelect.appendChild(defaultOption);
            
            // Ajouter les options correspondant au type
            const categories = categoriesByType[selectedType] || [];
            categories.forEach(function(category) {
                const option = document.createElement('option');
                option.value = category.value;
                option.textContent = category.text;
                categorieSelect.appendChild(option);
            });
            
            console.log('Catégories mises à jour, champ désactivé?', categorieSelect.disabled);
        };
        
        // Appliquer le gestionnaire d'événements
        typeSelect.addEventListener('change', window.updateCategories);
        
        // Si un type est déjà sélectionné au chargement
        if (typeSelect.value) {
            window.updateCategories();
        }
    }
    
    // Fonction pour fermer un ticket
    window.closeTicket = function(ticketId) {
        if (confirm('Êtes-vous sûr de vouloir fermer ce ticket ?')) {
            fetch(`/tickets/${ticketId}/close`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'same-origin'
            })
            .then(response => {
                return response.json().then(data => {
                    if (!response.ok) {
                        alert(data.error || 'Une erreur est survenue lors de la fermeture du ticket');
                        throw new Error(data.error || 'Une erreur est survenue lors de la fermeture du ticket');
                    }
                    return data;
                });
            })
            .then(data => {
                // Créer et afficher l'alerte de succès
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-success alert-dismissible fade show';
                alertDiv.innerHTML = `
                    <strong>Succès!</strong> ${data.message || 'Le ticket a été fermé avec succès.'}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                // Insérer l'alerte au début du container
                const container = document.querySelector('.container-fluid');
                if (container) {
                    container.insertBefore(alertDiv, container.firstChild);
                }
                
                // Recharger la page après un court délai
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            })            .catch(error => {
                console.error('Erreur:', error);
            });
        }
    };    // Vérification de la connexion avec health (retourne : 'status': 'ok', 'timestamp': datetime.now().isoformat()) sinon envoyer utilisateur vers la page d'attente /waiting tout les 5s
    // Préchargement de la page waiting en cas de problème
    const waitingUrl = '/waiting';
    
    // Fonction pour précharger la page waiting
    function preloadWaitingPage() {
        // Précharger via link prefetch
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = waitingUrl;
        document.head.appendChild(link);
        
        // Précharger via fetch pour mise en cache
        fetch(waitingUrl, { method: 'HEAD' }).catch(() => {
            console.log('[Preload] Page waiting non accessible pour préchargement');
        });
    }
    
    // Précharger la page dès le chargement
    preloadWaitingPage();
      // Fonction pour rediriger vers waiting de manière fiable
    function redirectToWaiting() {
        try {
            // Si service worker disponible, lui demander d'aider
            if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
                navigator.serviceWorker.controller.postMessage({
                    action: 'redirect-to-waiting'
                });
            }
            
            // Essayer de rediriger normalement
            window.location.href = waitingUrl;
        } catch (error) {
            // En cas d'erreur, essayer les méthodes alternatives
            console.log('[Redirect] Erreur lors de la redirection, tentative de forçage');
            try {
                window.location.replace(waitingUrl);
            } catch (replaceError) {
                // Si tout échoue, créer une page d'attente inline
                console.log('[Redirect] Toutes les redirections ont échoué, création inline');
                createInlineWaitingPage();
            }
        }
    }
    
    // Fonction pour créer une page d'attente directement dans le DOM
    function createInlineWaitingPage() {
        document.body.innerHTML = `
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
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
            </style>
            <div class="container">
                <h1>GLPIbis</h1>
                <div class="spinner"></div>
                <p>Serveur indisponible - Mode d'urgence</p>
                <p class="status" id="status">Tentative de reconnexion...</p>
                <p class="retry-count" id="retryCount">Tentative: 1</p>
                <p style="margin-top: 20px; font-size: 12px; opacity: 0.7;">
                    Actualisez la page manuellement une fois le serveur redémarré
                </p>
            </div>
        `;
        
        // Relancer la vérification de santé sur la nouvelle page
        let retryCount = 1;
        const maxRetries = 60;
        
        function updateStatus(message) {
            const statusEl = document.getElementById('status');
            if (statusEl) statusEl.textContent = message;
        }
        
        function updateRetryCount() {
            const retryEl = document.getElementById('retryCount');
            if (retryEl) retryEl.textContent = `Tentative: ${retryCount}`;
        }
        
        function checkServerInline() {
            fetch('/health', { cache: 'no-cache' })
                .then(response => {
                    if (response.ok) {
                        updateStatus('Serveur disponible ! Rechargement...');
                        setTimeout(() => {
                            window.location.reload();
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
                    setTimeout(checkServerInline, 5000);
                });
        }
        
        // Commencer la vérification après 2 secondes
        setTimeout(checkServerInline, 2000);
    }
    
    // Variable pour éviter les redirections multiples
    let isRedirecting = false;
    
    setInterval(function() {
        // Éviter les redirections multiples
        if (isRedirecting) return;
        
        fetch('/health')
            .then(response => {
                if (!response.ok) {
                    // Si la réponse n'est pas OK (503 par exemple), rediriger vers waiting
                    console.log('Application en pause ou erreur - redirection vers /waiting');
                    isRedirecting = true;
                    redirectToWaiting();
                    return;
                }
                return response.json();
            })
            .then(data => {
                if (data && data.status !== 'ok') {
                    console.log('Status de santé non OK - redirection vers /waiting');
                    isRedirecting = true;
                    redirectToWaiting();
                }
            })
            .catch(error => {
                console.error('Erreur lors de la vérification de santé:', error);
                // En cas d'erreur de connexion, rediriger vers waiting
                isRedirecting = true;
                redirectToWaiting();
            });
    }, 5000);
});
