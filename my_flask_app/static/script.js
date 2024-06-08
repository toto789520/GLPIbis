document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("myForm");
    const inputValue = document.getElementById("input_value");
    const savedValueDisplay = document.getElementById("saved_value");

    // Charger la valeur sauvegardée au chargement de la page
    const savedValue = localStorage.getItem("savedValue");
    if (savedValue) {
        savedValueDisplay.textContent = savedValue;
    }

    form.addEventListener("submit", function(event) {
        event.preventDefault();
        const value = inputValue.value;
        // Sauvegarder la valeur dans le stockage local
        localStorage.setItem("savedValue", value);
        // Mettre à jour l'affichage
        savedValueDisplay.textContent = value;
        // Réinitialiser le formulaire
        form.reset();
    });
});
