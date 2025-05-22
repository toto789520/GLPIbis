// Fonction pour fermer un ticket
window.closeTicket = function(ticketId) {
    if (confirm('Êtes-vous sûr de vouloir fermer ce ticket ?')) {
        fetch('/tickets/' + ticketId + '/close', {
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
            var alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show';
            alertDiv.innerHTML = '<strong>Succès!</strong> ' + (data.message || 'Le ticket a été fermé avec succès.') +
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
        })
        .catch(function(error) {
            console.error('Erreur:', error);
        });
    }
};
