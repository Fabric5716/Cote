// static/js/admin/cours_de.js

let toutesLesClasses = [];

document.addEventListener('DOMContentLoaded', function() {
    const classesData = document.getElementById('classes_data');
    if (classesData && classesData.value) {
        try { toutesLesClasses = JSON.parse(classesData.value); } catch(e) { console.error(e); }
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`tab-${tabId}`).classList.add('active');
            if (tabId === 'attribution') {
                loadClassesForAttribution();
                loadAttributions();
            }
            if (tabId === 'titulaire') {
                loadTitulairesList();
                loadTitulaireInfo();
            }
        });
    });

    const attribCycle = document.getElementById('attrib_cycle');
    if (attribCycle) {
        attribCycle.addEventListener('change', function() {
            const optionGroup = document.getElementById('attrib_option_group');
            if (this.value === 'SECONDAIRE') {
                optionGroup.style.display = 'block';
                document.getElementById('attrib_option').required = true;
            } else {
                optionGroup.style.display = 'none';
                document.getElementById('attrib_option').required = false;
                document.getElementById('attrib_option').value = '';
            }
            loadClassesForAttribution();
            loadCoursForAttribution();
        });
    }

    document.getElementById('attrib_option')?.addEventListener('change', loadCoursForAttribution);
    document.getElementById('attrib_classe')?.addEventListener('change', loadAttributions);
    document.getElementById('titulaire_classe')?.addEventListener('change', loadTitulaireInfo);

    if (document.getElementById('attrib_classe')) {
        loadClassesForAttribution();
        loadAttributions();
    }
    loadTitulaireInfo();
    loadTitulairesList();

    // Cycle dans le modal cours
    const coursCycle = document.getElementById('cours_cycle');
    if (coursCycle) {
        coursCycle.addEventListener('change', function() {
            const optionGroup = document.getElementById('cours_option_group');
            if (this.value === 'SECONDAIRE') {
                optionGroup.style.display = 'block';
                document.getElementById('cours_option').required = true;
            } else {
                optionGroup.style.display = 'none';
                document.getElementById('cours_option').required = false;
                document.getElementById('cours_option').value = '';
            }
        });
    }
});

// ----- Gestion des cours (CRUD) -----
document.getElementById('coursForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const id = document.getElementById('cours_id').value;
    const url = id ? `/api/cours/${id}/modifier/` : '/api/cours/ajouter/';
    const formData = new FormData(this);
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            Swal.fire('Succès', data.message, 'success');
            closeModal('modalCours');
            location.reload();
        } else Swal.fire('Erreur', data.error, 'error');
    });
});

function editCours(id) {
    fetch(`/api/cours/${id}/get/`)
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById('cours_id').value = data.cours.id;
                document.getElementById('code_cours').value = data.cours.code_cours;
                document.getElementById('nom_cours').value = data.cours.nom_cours;
                document.getElementById('points_par_periode').value = data.cours.points_par_periode || 40;
                document.getElementById('description').value = data.cours.description || '';
                if (data.cours.id_option) {
                    document.getElementById('cours_option').value = data.cours.id_option;
                    document.getElementById('cours_cycle').value = 'SECONDAIRE';
                    document.getElementById('cours_option_group').style.display = 'block';
                } else {
                    document.getElementById('cours_cycle').value = 'CO';
                    document.getElementById('cours_option_group').style.display = 'none';
                }
                document.getElementById('modalCoursTitle').innerText = 'Modifier le cours';
                openModal('modalCours');
            } else Swal.fire('Erreur', data.error, 'error');
        })
        .catch(() => Swal.fire('Erreur', 'Impossible de charger le cours', 'error'));
}

function deleteCours(id) {
    Swal.fire({
        title: 'Confirmation', text: 'Supprimer ce cours ?', icon: 'warning',
        showCancelButton: true, confirmButtonColor: '#d33', confirmButtonText: 'Oui, supprimer'
    }).then(result => {
        if (result.isConfirmed) {
            fetch(`/api/cours/${id}/supprimer/`, { method: 'DELETE', headers: { 'X-CSRFToken': getCsrfToken() } })
            .then(r => r.json()).then(data => {
                if (data.success) { Swal.fire('Supprimé', data.message, 'success'); location.reload(); }
                else Swal.fire('Erreur', data.error, 'error');
            });
        }
    });
}

// ----- Attribution : classes filtrées par cycle -----
function loadClassesForAttribution() {
    const cycle = document.getElementById('attrib_cycle').value;
    const classeSelect = document.getElementById('attrib_classe');
    if (!cycle) {
        classeSelect.innerHTML = '<option value="">-- Sélectionnez d\'abord un cycle --</option>';
        return;
    }
    let classesFiltrees = [];
    if (cycle === 'CO') classesFiltrees = toutesLesClasses.filter(c => c.est_cycle_orientation === true);
    else if (cycle === 'SECONDAIRE') classesFiltrees = toutesLesClasses.filter(c => c.est_cycle_orientation === false);
    classeSelect.innerHTML = '<option value="">-- Classe --</option>';
    classesFiltrees.forEach(c => { classeSelect.innerHTML += `<option value="${c.id}">${c.nom_classe}</option>`; });
    if (classesFiltrees.length === 0) classeSelect.innerHTML += '<option value="">Aucune classe disponible</option>';
}

function loadCoursForAttribution() {
    const cycle = document.getElementById('attrib_cycle').value;
    const option = document.getElementById('attrib_option').value;
    if (!cycle) return;
    let url = `/api/cours/par-option/?cycle=${cycle}`;
    if (cycle === 'SECONDAIRE' && option) url += `&option_id=${option}`;
    fetch(url)
        .then(r => r.json())
        .then(data => {
            const select = document.getElementById('attrib_cours');
            select.innerHTML = '<option value="">-- Choisir --</option>';
            if (data.cours && data.cours.length) {
                data.cours.forEach(c => {
                    select.innerHTML += `<option value="${c.id}">${c.nom} (${c.code}) - ${c.points_par_periode} pts/période</option>`;
                });
            } else select.innerHTML += '<option value="">Aucun cours disponible</option>';
        });
}

function attribuerCours() {
    const cours_id = document.getElementById('attrib_cours').value;
    const personnel_id = document.getElementById('attrib_enseignant').value;
    const classe_id = document.getElementById('attrib_classe').value;
    const annee_id = document.getElementById('annee_active_id')?.value;
    if (!cours_id || !personnel_id || !classe_id || !annee_id) {
        Swal.fire('Erreur', 'Veuillez remplir tous les champs', 'error');
        return;
    }
    const formData = new FormData();
    formData.append('cours_id', cours_id);
    formData.append('personnel_id', personnel_id);
    formData.append('classe_id', classe_id);
    formData.append('annee_id', annee_id);
    fetch('/api/attributions/ajouter/', {
        method: 'POST', body: formData, headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) { Swal.fire('Succès', data.message, 'success'); loadAttributions(); }
        else Swal.fire('Erreur', data.error, 'error');
    });
}

function loadAttributions() {
    const classe_id = document.getElementById('attrib_classe').value;
    const annee_id = document.getElementById('annee_active_id')?.value;
    if (!classe_id || !annee_id) return;
    fetch(`/api/attributions/classe/?classe_id=${classe_id}&annee_id=${annee_id}`)
        .then(r => r.json())
        .then(data => {
            const tbody = document.querySelector('#attributionsTable tbody');
            tbody.innerHTML = '';
            if (data.attributions && data.attributions.length) {
                data.attributions.forEach(a => {
                    tbody.innerHTML += `<tr>
                        <td>${a.cours_nom} (${a.cours_code})</td>
                        <td>${a.enseignant}</td>
                        <td>${a.classe_nom || classe_id}</td>
                        <td><button class="action-btn delete" onclick="deleteAttribution(${a.id})"><i class="fas fa-trash"></i></button></td>
                    </tr>`;
                });
            } else {
                tbody.innerHTML = '<tr class="empty-message"><td colspan="4">Aucune attribution</td></tr>';
            }
        });
}

function deleteAttribution(id) {
    Swal.fire({
        title: 'Confirmation', text: 'Retirer ce cours de cette classe ?', icon: 'warning',
        showCancelButton: true, confirmButtonColor: '#d33', confirmButtonText: 'Oui'
    }).then(result => {
        if (result.isConfirmed) {
            fetch(`/api/attributions/${id}/supprimer/`, { method: 'DELETE', headers: { 'X-CSRFToken': getCsrfToken() } })
            .then(r => r.json()).then(data => {
                if (data.success) { loadAttributions(); Swal.fire('Supprimé', data.message, 'success'); }
                else Swal.fire('Erreur', data.error, 'error');
            });
        }
    });
}

// ----- Gestion des titulaires (rafraîchissement dynamique) -----
function definirTitulaire() {
    const classe_id = document.getElementById('titulaire_classe').value;
    const personnel_id = document.getElementById('titulaire_enseignant').value;
    const annee_id = document.getElementById('annee_active_id')?.value;
    if (!classe_id || !annee_id) { Swal.fire('Erreur', 'Sélectionnez une classe', 'error'); return; }
    if (!personnel_id) { Swal.fire('Erreur', 'Sélectionnez un enseignant', 'error'); return; }
    const formData = new FormData();
    formData.append('classe_id', classe_id);
    formData.append('personnel_id', personnel_id);
    formData.append('annee_id', annee_id);
    fetch('/api/titulaire/definir/', {
        method: 'POST', body: formData, headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            Swal.fire('Succès', data.message, 'success');
            loadTitulaireInfo();
            loadTitulairesList();
        } else {
            Swal.fire('Erreur', data.error, 'error');
        }
    });
}

function supprimerTitulaire() {
    const classe_id = document.getElementById('titulaire_classe').value;
    const annee_id = document.getElementById('annee_active_id')?.value;
    if (!classe_id || !annee_id) { Swal.fire('Erreur', 'Sélectionnez une classe', 'error'); return; }
    const formData = new FormData();
    formData.append('classe_id', classe_id);
    formData.append('personnel_id', '');
    formData.append('annee_id', annee_id);
    fetch('/api/titulaire/definir/', {
        method: 'POST', body: formData, headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            Swal.fire('Supprimé', data.message, 'success');
            loadTitulaireInfo();
            loadTitulairesList();
        } else {
            Swal.fire('Erreur', data.error, 'error');
        }
    });
}

function supprimerTitulaireById(titulaire_id) {
    Swal.fire({
        title: 'Confirmation',
        text: 'Supprimer ce titulaire ?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Oui, supprimer'
    }).then(result => {
        if (result.isConfirmed) {
            fetch(`/api/titulaire/${titulaire_id}/supprimer/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken() }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire('Supprimé', data.message, 'success');
                    loadTitulairesList();
                    loadTitulaireInfo();
                } else {
                    Swal.fire('Erreur', data.error, 'error');
                }
            })
            .catch(error => {
                console.error(error);
                Swal.fire('Erreur', 'Impossible de supprimer le titulaire', 'error');
            });
        }
    });
}

function loadTitulaireInfo() {
    const classe_id = document.getElementById('titulaire_classe').value;
    const annee_id = document.getElementById('annee_active_id')?.value;
    if (!classe_id || !annee_id) return;
    fetch(`/api/titulaire/get/?classe_id=${classe_id}&annee_id=${annee_id}`)
        .then(r => r.json())
        .then(data => {
            const infoDiv = document.getElementById('titulaire_info');
            if (data.titulaire) {
                infoDiv.innerHTML = `<i class="fas fa-check-circle"></i> <strong>Titulaire actuel :</strong> ${data.titulaire.nom}`;
                document.getElementById('titulaire_enseignant').value = data.titulaire.personnel_id;
            } else {
                infoDiv.innerHTML = '<i class="fas fa-info-circle"></i> Aucun titulaire désigné pour cette classe';
                document.getElementById('titulaire_enseignant').value = '';
            }
        });
}

function loadTitulairesList() {
    const annee_id = document.getElementById('annee_active_id')?.value;
    if (!annee_id) return;
    fetch(`/api/titulaires/liste/?annee_id=${annee_id}`)
        .then(r => r.json())
        .then(data => {
            const tbody = document.querySelector('#titulairesTable tbody');
            tbody.innerHTML = '';
            if (data.titulaires && data.titulaires.length) {
                data.titulaires.forEach(t => {
                    tbody.innerHTML += `<tr data-id="${t.id}">
                        <td>${t.enseignant_nom}</td>
                        <td>${t.classe_nom}</td>
                        <td>${t.annee_scolaire}</td>
                        <td><button class="action-btn delete" onclick="supprimerTitulaireById(${t.id})"><i class="fas fa-trash"></i></button></td>
                    </tr>`;
                });
            } else {
                tbody.innerHTML = '<tr class="empty-message"><td colspan="4">Aucun titulaire désigné</td></tr>';
            }
        });
}

// Utilitaires
function getCsrfToken() { return document.querySelector('[name=csrfmiddlewaretoken]').value; }
function openModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }
window.onclick = function(e) { if (e.target.classList.contains('modal')) e.target.style.display = 'none'; }