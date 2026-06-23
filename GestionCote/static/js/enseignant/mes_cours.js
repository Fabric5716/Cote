// Premium interactions pour la page "Mes cours"
document.addEventListener('DOMContentLoaded', function() {
    // Appliquer une animation progressive sur les lignes du tableau
    const rows = document.querySelectorAll('.course-row');
    rows.forEach((row, index) => {
        row.style.setProperty('--row-index', index);
    });

    // Ajouter un effet de confirmation au clic sur "Saisir notes"
    const links = document.querySelectorAll('.btn-primary');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            // Optionnel : message de confirmation élégant
            // On peut activer un toast ou une modale si besoin
            console.log('Redirection vers la saisie des notes pour', this.href);
        });
    });

    // Tooltips (si vous utilisez Bootstrap)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});