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
            })
            .catch(error => {
                console.error('Erreur:', error);
            });
        }
    };
});
