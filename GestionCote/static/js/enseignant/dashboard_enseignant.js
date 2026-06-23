// static/js/enseignant/dashboard_enseignant.js
console.log("Dashboard enseignant chargé");

document.addEventListener('DOMContentLoaded', function() {
    chargerDonneesEnseignant();
});

function chargerDonneesEnseignant() {
    fetch('/api/enseignant/data/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Mettre à jour les cartes
                document.getElementById('totalCours').innerText = data.total_cours;
                document.getElementById('totalClasses').innerText = data.total_classes;
                document.getElementById('totalEleves').innerText = data.total_eleves;
                
                const titulaireStatus = data.titulaire.est_titulaire ? 
                    `✅ ${data.titulaire.classe_nom}` : '❌ Aucune';
                document.getElementById('titulaireStatus').innerHTML = titulaireStatus;
                
                // Badges
                document.getElementById('coursCount').innerText = data.total_cours;
                document.getElementById('classesCount').innerText = data.classes_enseignees.length;
                
                // Remplir le tableau des cours (avec colonne Points/période)
                const tbody = document.getElementById('coursTableBody');
                tbody.innerHTML = '';
                if (data.cours.length === 0) {
                    tbody.innerHTML = '<tr class="empty-row"><td colspan="6">Aucun cours assigné</td></tr>';
                } else {
                    data.cours.forEach(c => {
                        const row = tbody.insertRow();
                        row.insertCell(0).innerText = c.cours_nom;
                        row.insertCell(1).innerText = c.classe_nom;
                        row.insertCell(2).innerText = c.option_nom || '—';
                        row.insertCell(3).innerText = c.points_par_periode || 40;
                        row.insertCell(4).innerText = c.effectif;
                        const actionsCell = row.insertCell(5);
                        const btn = document.createElement('button');
                        btn.className = 'btn-sm';
                        btn.innerHTML = '<i class="fas fa-chart-line"></i> Notes';
                        // Correction : redirection vers 'saisir-cotes' avec les IDs
                        btn.onclick = () => {
                            window.location.href = `/saisir-cotes/?classe=${c.classe_id}&cours=${c.cours_id}`;
                        };
                        actionsCell.appendChild(btn);
                    });
                }
                
                // Remplir la liste des classes enseignées
                const classesList = document.getElementById('classesList');
                classesList.innerHTML = '';
                if (data.classes_enseignees.length === 0) {
                    classesList.innerHTML = '<p class="empty-message">Aucune classe</p>';
                } else {
                    data.classes_enseignees.forEach(classe => {
                        const tag = document.createElement('span');
                        tag.className = 'class-tag';
                        tag.innerText = classe;
                        classesList.appendChild(tag);
                    });
                }
            } else {
                console.error('Erreur API:', data.error);
                Swal.fire('Erreur', data.error || 'Données invalides', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur fetch:', error);
            Swal.fire('Erreur', 'Impossible de charger les données. Vérifiez la console.', 'error');
            const tbody = document.getElementById('coursTableBody');
            if (tbody) tbody.innerHTML = '<tr class="empty-row"><td colspan="6">Erreur de chargement</td></tr>';
        });
}