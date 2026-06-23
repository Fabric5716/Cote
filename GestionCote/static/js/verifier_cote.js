// Chargement des années scolaires et de la classe du titulaire
async function chargerAnnees() {
    try {
        const response = await fetch('/api/enseignant/annees/'); // API existante
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
            // Sélectionner l'année active si possible
            const activeYear = data.annees.find(a => a.est_active === true);
            if (activeYear) {
                select.value = activeYear.id;
                chargerClasseTitulaire(activeYear.id);
            } else if (data.annees.length > 0) {
                select.value = data.annees[0].id;
                chargerClasseTitulaire(data.annees[0].id);
            }
        } else {
            select.innerHTML = '<option value="">Aucune année disponible</option>';
        }
        select.addEventListener('change', (e) => {
            if (e.target.value) {
                chargerClasseTitulaire(e.target.value);
            } else {
                document.getElementById('classeInfo').value = '';
                document.getElementById('cotesContainer').innerHTML = '<div class="alert alert-info">Sélectionnez une année.</div>';
            }
        });
    } catch (err) {
        console.error('Erreur chargement années:', err);
        document.getElementById('anneeSelect').innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

async function chargerClasseTitulaire(anneeId) {
    try {
        const response = await fetch(`/api/titulaire/classe/?annee_id=${anneeId}`);
        const data = await response.json();
        if (data.success && data.classe) {
            document.getElementById('classeInfo').value = `${data.classe.nom} ${data.classe.est_cycle_orientation ? '(CO)' : '(Secondaire)'}`;
            chargerCotesEleves(anneeId);
        } else {
            document.getElementById('classeInfo').value = data.error || 'Vous n\'êtes titulaire d\'aucune classe';
            document.getElementById('cotesContainer').innerHTML = `<div class="alert alert-warning">${data.error || 'Aucune classe trouvée'}</div>`;
        }
    } catch (err) {
        console.error('Erreur classe titulaire:', err);
        document.getElementById('classeInfo').value = 'Erreur de chargement';
    }
}

async function chargerCotesEleves(anneeId) {
    const container = document.getElementById('cotesContainer');
    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin fa-2x"></i><p>Chargement des cotes...</p></div>';
    try {
        const response = await fetch(`/api/titulaire/cotes-eleves/?annee_id=${anneeId}`);
        const result = await response.json();
        if (!result.success) {
            container.innerHTML = `<div class="alert alert-danger">${result.error || 'Erreur de chargement'}</div>`;
            return;
        }
        const data = result.data;
        if (!data.eleves || data.eleves.length === 0) {
            container.innerHTML = '<div class="alert alert-info">Aucun élève inscrit dans cette classe.</div>';
            return;
        }
        genererTableau(data);
    } catch (err) {
        console.error(err);
        container.innerHTML = '<div class="alert alert-danger">Erreur lors du chargement des cotes.</div>';
    }
}

function genererTableau(data) {
    const container = document.getElementById('cotesContainer');
    const cours = data.cours; // [{id, nom}, ...]
    const eleves = data.eleves;

    // Construction de l'en-tête : une colonne Élève, puis pour chaque cours : 11 colonnes (notes + validation)
    let html = `<div class="table-responsive" style="overflow-x: auto;">
        <table class="cotes-table detail-table" style="min-width: 1200px;">
            <thead>
                <tr>
                    <th rowspan="2">Élève</th>`;
    for (let c of cours) {
        html += `<th colspan="11" style="text-align:center; background:#f0f4f8;">${c.nom}</th>`;
    }
    html += `</tr><tr>`;
    for (let i = 0; i < cours.length; i++) {
        html += `
            <th>P1</th><th>P2</th><th>Ex S1</th><th>Total S1</th>
            <th>P3</th><th>P4</th><th>Ex S2</th><th>Total S2</th>
            <th>Total général</th><th>%</th><th>Validation</th>
        `;
    }
    html += `</tr></thead><tbody>`;

    for (const eleve of eleves) {
        html += `<tr class="eleve-row">
            <td><strong>${eleve.nom} ${eleve.prenom}</strong><br><small class="text-muted">${eleve.matricule}</small></td>`;
        for (let idx = 0; idx < cours.length; idx++) {
            const cote = eleve.cotes.find(c => c.cours_id === cours[idx].id);
            if (cote && cote.cote_id) {
                // Calcul des totaux manquants (si l'API ne les fournit pas)
                const p1 = cote.p1 ?? null;
                const p2 = cote.p2 ?? null;
                const ex1 = cote.ex1 ?? null;
                const p3 = cote.p3 ?? null;
                const p4 = cote.p4 ?? null;
                const ex2 = cote.ex2 ?? null;
                const totalS1 = (p1 !== null && p2 !== null && ex1 !== null) ? (p1 + p2 + ex1) : (cote.total_s1 ?? null);
                const totalS2 = (p3 !== null && p4 !== null && ex2 !== null) ? (p3 + p4 + ex2) : (cote.total_s2 ?? null);
                const totalGeneral = cote.total_general ?? (totalS1 !== null && totalS2 !== null ? totalS1 + totalS2 : null);
                const pourcentage = cote.pourcentage ?? (totalGeneral !== null && totalGeneral > 0 ? (totalGeneral / (cours[idx].points_totaux ?? 240) * 100).toFixed(1) : null);
                const validee = cote.validee;

                html += `
                    <td>${p1 !== null ? p1 : '—'}</td>
                    <td>${p2 !== null ? p2 : '—'}</td>
                    <td>${ex1 !== null ? ex1 : '—'}</td>
                    <td class="total-cell">${totalS1 !== null ? totalS1 : '—'}</td>
                    <td>${p3 !== null ? p3 : '—'}</td>
                    <td>${p4 !== null ? p4 : '—'}</td>
                    <td>${ex2 !== null ? ex2 : '—'}</td>
                    <td class="total-cell">${totalS2 !== null ? totalS2 : '—'}</td>
                    <td class="total-cell">${totalGeneral !== null ? totalGeneral : '—'}</td>
                    <td class="pourcentage-cell">${pourcentage !== null ? pourcentage + '%' : '—'}</td>
                    <td class="validation-cell">
                        <button class="btn-valider" data-cote-id="${cote.cote_id}" data-validee="${validee}">
                            <i class="fas ${validee ? 'fa-check-circle validated' : 'fa-circle'}"></i>
                        </button>
                    </td>
                `;
            } else {
                // Aucune cote saisie
                html += `<td colspan="11" style="text-align:center;">Aucune cote</td>`;
            }
        }
        html += `</tr>`;
    }
    html += `</tbody></table></div>
        <div class="mt-3 text-muted">
            <i class="fas fa-info-circle"></i> 
            Cliquez sur le cercle à côté de chaque cours pour valider/dévalider la cote complète.
            La validation est requise pour l'édition du bulletin.
        </div>`;
    container.innerHTML = html;

    // Attacher les événements aux boutons de validation (même code qu'avant)
    document.querySelectorAll('.btn-valider').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const coteId = btn.dataset.coteId;
            if (!coteId) return;
            const icon = btn.querySelector('i');
            const wasValidated = icon.classList.contains('validated');
            btn.disabled = true;
            btn.style.opacity = '0.6';
            try {
                const response = await fetch('/api/titulaire/valider-cote/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cote_id: parseInt(coteId) })
                });
                const result = await response.json();
                if (result.success) {
                    if (result.validee) {
                        icon.classList.add('validated');
                        icon.classList.remove('fa-circle');
                        icon.classList.add('fa-check-circle');
                        btn.closest('td').classList.add('validated');
                    } else {
                        icon.classList.remove('validated');
                        icon.classList.remove('fa-check-circle');
                        icon.classList.add('fa-circle');
                        btn.closest('td').classList.remove('validated');
                    }
                    btn.dataset.validee = result.validee;
                } else {
                    alert('Erreur : ' + (result.error || 'Validation impossible'));
                }
            } catch (err) {
                alert('Erreur réseau lors de la validation.');
                console.error(err);
            } finally {
                btn.disabled = false;
                btn.style.opacity = '1';
            }
        });
    });
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    chargerAnnees();
});