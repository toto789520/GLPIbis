// Fonction pour fermer un ticket
window.closeTicket = function(ticketId) {
    if (confirm('Êtes-vous sûr de vouloir fermer ce ticket ?')) {
        fetch('/tickets/close/' + ticketId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (response.ok) {
                // Créer et afficher l'alerte de succès
                var alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-success alert-dismissible fade show';
                alertDiv.innerHTML = '<strong>Succès!</strong> Le ticket a été fermé avec succès.' +
                    '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
                
                // Insérer l'alerte au début du container
                var container = document.querySelector('.container-fluid');
                if (container) {
                    container.insertBefore(alertDiv, container.firstChild);
                }
                
                // Recharger la page après un court délai
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error('Erreur lors de la fermeture du ticket');
            }
        })
        .catch(function(error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la fermeture du ticket');
        });
    }
};

// Fonction pour générer un QR code
window.generateQRCode = function(itemId, itemName) {
    if (confirm('Voulez-vous générer un QR code pour cet équipement ?')) {
        // Afficher un indicateur de chargement
        const loadingAlert = document.createElement('div');
        loadingAlert.className = 'alert alert-info';
        loadingAlert.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Génération du QR code en cours...';
        
        const container = document.querySelector('.container-fluid') || document.querySelector('.container');
        if (container) {
            container.insertBefore(loadingAlert, container.firstChild);
        }

        fetch('/inventory/generate-qr/' + itemId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            // Supprimer l'indicateur de chargement
            loadingAlert.remove();
            
            if (data.success) {
                // Créer et afficher l'alerte de succès avec liens
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-success alert-dismissible fade show';
                alertDiv.innerHTML = `
                    <strong>Succès!</strong> QR code généré avec succès pour ${itemName}<br>
                    <div class="mt-2">
                        <a href="/static/qr_codes/${data.filename}" target="_blank" class="btn btn-sm btn-outline-primary me-2">
                            <i class="fas fa-qrcode"></i> Voir QR Code
                        </a>
                        <a href="/static/qr_codes/${data.label_filename}" target="_blank" class="btn btn-sm btn-outline-secondary me-2">
                            <i class="fas fa-tag"></i> Voir Étiquette
                        </a>
                        <button type="button" class="btn btn-sm btn-outline-success" onclick="downloadQRFiles('${data.filename}', '${data.label_filename}', '${itemName}')">
                            <i class="fas fa-download"></i> Télécharger
                        </button>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                // Insérer l'alerte au début du container
                if (container) {
                    container.insertBefore(alertDiv, container.firstChild);
                }
            } else {
                throw new Error(data.error || 'Erreur lors de la génération du QR code');
            }
        })
        .catch(function(error) {
            // Supprimer l'indicateur de chargement
            loadingAlert.remove();
            
            console.error('Erreur:', error);
            
            // Afficher l'erreur
            const errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger alert-dismissible fade show';
            errorAlert.innerHTML = `
                <strong>Erreur!</strong> ${error.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            if (container) {
                container.insertBefore(errorAlert, container.firstChild);
            }
        });
    }
};

// Fonction pour télécharger les fichiers QR
window.downloadQRFiles = function(qrFilename, labelFilename, itemName) {
    // Télécharger le QR code
    const qrLink = document.createElement('a');
    qrLink.href = `/static/qr_codes/${qrFilename}`;
    qrLink.download = `QRCode_${itemName.replace(/[^a-zA-Z0-9]/g, '_')}.png`;
    qrLink.click();
    
    // Télécharger l'étiquette après un petit délai
    setTimeout(() => {
        const labelLink = document.createElement('a');
        labelLink.href = `/static/qr_codes/${labelFilename}`;
        labelLink.download = `Etiquette_${itemName.replace(/[^a-zA-Z0-9]/g, '_')}.png`;
        labelLink.click();
    }, 500);
};
