// static/js/admin/liste_eleves.js
console.log("Liste des élèves chargée – version pro");

document.addEventListener('DOMContentLoaded', function() {
    // Animation d'apparition du tableau
    const tableContainer = document.querySelector('.table-container');
    if (tableContainer) {
        tableContainer.style.opacity = '0';
        tableContainer.style.transform = 'translateY(12px)';
        setTimeout(() => {
            tableContainer.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            tableContainer.style.opacity = '1';
            tableContainer.style.transform = 'translateY(0)';
        }, 100);
    }

    // Effet de focus sur les filtres
    const filterSelects = document.querySelectorAll('.filter-group select');
    filterSelects.forEach(select => {
        select.addEventListener('focus', function() {
            this.style.borderColor = '#1e3c72';
            this.style.boxShadow = '0 0 0 3px rgba(30,60,114,0.1)';
        });
        select.addEventListener('blur', function() {
            this.style.borderColor = '#e2e8f0';
            this.style.boxShadow = 'none';
        });
    });
});