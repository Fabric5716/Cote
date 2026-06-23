// Chargement des années
async function chargerAnnees() {
    try {
        const response = await fetch('/api/enseignant/annees/');
        const data = await response.json();
        const select = document.getElementById('anneeSelect');
        select.innerHTML = '<option value="">Sélectionner une année</option>';
        if (data.annees && data.annees.length) {
            data.annees.forEach(annee => {
                const option = document.createElement('option');
                option.value = annee.id;
                option.textContent = annee.annee_scolaire;
                select.appendChild(option);
            });
            const active = data.annees.find(a => a.est_active === true);
            if (active) select.value = active.id;
        } else {
            select.innerHTML = '<option value="">Aucune année disponible</option>';
        }
        select.addEventListener('change', () => {
            document.getElementById('classeSelect').disabled = false;
            document.getElementById('classeSelect').innerHTML = '<option value="">Chargement...</option>';
            document.getElementById('coursSelect').disabled = true;
            document.getElementById('coursSelect').innerHTML = '<option value="">Sélectionnez d\'abord une classe</option>';
            document.getElementById('chargerBtn').disabled = true;
            if (select.value) chargerClasses(select.value);
        });
    } catch (err) {
        console.error(err);
        document.getElementById('anneeSelect').innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

async function chargerClasses(anneeId) {
    try {
        const response = await fetch(`/api/enseignant/classes/?annee_id=${anneeId}`);
        const data = await response.json();
        const select = document.getElementById('classeSelect');
        if (data.classes && data.classes.length) {
            select.innerHTML = '<option value="">Sélectionner une classe</option>';
            data.classes.forEach(classe => {
                const option = document.createElement('option');
                option.value = classe.id;
                option.textContent = classe.nom_classe;
                select.appendChild(option);
            });
            select.disabled = false;
            select.addEventListener('change', () => {
                document.getElementById('coursSelect').disabled = false;
                document.getElementById('coursSelect').innerHTML = '<option value="">Chargement...</option>';
                document.getElementById('chargerBtn').disabled = true;
                if (select.value) chargerCours(anneeId, select.value);
            });
        } else {
            select.innerHTML = '<option value="">Aucune classe trouvée</option>';
            select.disabled = true;
        }
    } catch (err) {
        console.error(err);
        document.getElementById('classeSelect').innerHTML = '<option value="">Erreur</option>';
    }
}

async function chargerCours(anneeId, classeId) {
    try {
        const response = await fetch(`/api/enseignant/cours/?annee_id=${anneeId}&classe_id=${classeId}`);
        const data = await response.json();
        const select = document.getElementById('coursSelect');
        if (data.cours && data.cours.length) {
            select.innerHTML = '<option value="">Sélectionner un cours</option>';
            data.cours.forEach(cours => {
                const option = document.createElement('option');
                option.value = cours.id;
                option.textContent = `${cours.nom_cours} (coeff ${cours.coefficient}, ${cours.points_par_periode} pts/période)`;
                option.dataset.points = cours.points_par_periode;
                select.appendChild(option);
            });
            select.disabled = false;
            select.addEventListener('change', () => {
                document.getElementById('chargerBtn').disabled = !select.value;
            });
        } else {
            select.innerHTML = '<option value="">Aucun cours attribué</option>';
            select.disabled = true;
        }
    } catch (err) {
        console.error(err);
        document.getElementById('coursSelect').innerHTML = '<option value="">Erreur</option>';
    }
}

async function afficherListe() {
    const anneeId = document.getElementById('anneeSelect').value;
    const classeId = document.getElementById('classeSelect').value;
    const coursId = document.getElementById('coursSelect').value;
    if (!anneeId || !classeId || !coursId) {
        alert("Veuillez sélectionner tous les filtres.");
        return;
    }
    const classeSelect = document.getElementById('classeSelect');
    const classeNom = classeSelect.options[classeSelect.selectedIndex]?.text || 'Classe';

    const container = document.getElementById('resultContainer');
    container.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin fa-2x"></i><p>Chargement des cotes...</p></div>';
    try {
        const response = await fetch(`/api/enseignant/liste-cotes/?annee_id=${anneeId}&classe_id=${classeId}&cours_id=${coursId}`);
        const result = await response.json();
        if (!result.success) {
            container.innerHTML = `<div class="alert alert-danger">${result.error || 'Erreur de chargement'}</div>`;
            return;
        }
        const data = result.data;
        if (!data.eleves || data.eleves.length === 0) {
            container.innerHTML = '<div class="alert alert-info">Aucun élève inscrit dans cette classe pour ce cours.</div>';
            return;
        }
        genererTableau(data, classeNom);
    } catch (err) {
        console.error(err);
        container.innerHTML = '<div class="alert alert-danger">Erreur lors de la récupération des données.</div>';
    }
}

function genererTableau(data, classeNom) {
    const colonne = document.getElementById('colonneSelect').value;
    const pointsParPeriode = data.points_par_periode;
    const maxPeriode = pointsParPeriode;
    const maxExamen = pointsParPeriode * 2;
    const maxTotalS1 = maxPeriode * 2 + maxExamen;
    const maxTotalS2 = maxPeriode * 2 + maxExamen;
    const maxTotalGeneral = maxTotalS1 + maxTotalS2;

    let titreColonne = '';
    let maxValeur = null;
    switch (colonne) {
        case 'p1': titreColonne = `P1 (/${maxPeriode})`; maxValeur = maxPeriode; break;
        case 'p2': titreColonne = `P2 (/${maxPeriode})`; maxValeur = maxPeriode; break;
        case 'ex1': titreColonne = `Examen S1 (/${maxExamen})`; maxValeur = maxExamen; break;
        case 'total_s1': titreColonne = `Total S1 (/${maxTotalS1})`; maxValeur = maxTotalS1; break;
        case 'p3': titreColonne = `P3 (/${maxPeriode})`; maxValeur = maxPeriode; break;
        case 'p4': titreColonne = `P4 (/${maxPeriode})`; maxValeur = maxPeriode; break;
        case 'ex2': titreColonne = `Examen S2 (/${maxExamen})`; maxValeur = maxExamen; break;
        case 'total_s2': titreColonne = `Total S2 (/${maxTotalS2})`; maxValeur = maxTotalS2; break;
        case 'total_general': titreColonne = `Total général (/${maxTotalGeneral})`; maxValeur = maxTotalGeneral; break;
        case 'pourcentage': titreColonne = `Pourcentage (%)`; maxValeur = null; break;
        default: titreColonne = 'Valeur';
    }

    // Ordre : d'abord la classe (avec les points), puis le nom du cours
    let html = `
        <div class="cours-header">
            <p class="classe-info"><strong>Classe :</strong> ${classeNom} | ${pointsParPeriode} points par période</p>
            <h2><i class="fas fa-book-open"></i> ${data.cours_nom}</h2>
        </div>
        <div class="table-responsive">
            <table class="liste-table">
                <thead>
                    <tr><th>Élève</th><th>${titreColonne}</th></tr>
                </thead>
                <tbody>
    `;

    for (let eleve of data.eleves) {
        const c = eleve.cote || {};
        let valeur = '—';
        if (c[colonne] !== undefined && c[colonne] !== null) {
            if (colonne === 'pourcentage') {
                valeur = c[colonne].toFixed(1) + '%';
            } else {
                valeur = c[colonne];
                if (maxValeur && !isNaN(parseFloat(valeur)) && parseFloat(valeur) < maxValeur * 0.5) {
                    valeur = `<span class="text-danger">${valeur}</span>`;
                }
            }
        }
        html += `
            <tr>
                <td><strong>${eleve.nom} ${eleve.prenom}</strong><br><small>${eleve.matricule}</small></td>
                <td class="valeur-cell">${valeur}</td>
            </tr>
        `;
    }
    html += `
                </tbody>
            </table>
        </div>
    `;
    document.getElementById('resultContainer').innerHTML = html;
}

// Initialisation des écouteurs
document.addEventListener('DOMContentLoaded', () => {
    chargerAnnees();
    document.getElementById('chargerBtn').addEventListener('click', afficherListe);
    document.getElementById('resetBtn').addEventListener('click', () => {
        document.getElementById('anneeSelect').value = '';
        document.getElementById('classeSelect').innerHTML = '<option value="">Sélectionnez d\'abord une année</option>';
        document.getElementById('classeSelect').disabled = true;
        document.getElementById('coursSelect').innerHTML = '<option value="">Sélectionnez d\'abord une classe</option>';
        document.getElementById('coursSelect').disabled = true;
        document.getElementById('chargerBtn').disabled = true;
        document.getElementById('resultContainer').innerHTML = '<div class="alert alert-info">Veuillez sélectionner une année, une classe et un cours.</div>';
        if (document.getElementById('anneeSelect').options.length > 1) chargerAnnees();
    });
    document.getElementById('printBtn').addEventListener('click', () => window.print());
});