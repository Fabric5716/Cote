// static/js/admin/annee_scolaire.js

console.log("=== FICHIER ANNEE SCOLAIRE CHARGÉ ===");

let currentYearId = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    initializeModals();
    
    const anneeInput = document.getElementById('annee_scolaire');
    if (anneeInput) {
        anneeInput.addEventListener('input', function() {
            validateYearFormat(this);
        });
        anneeInput.addEventListener('blur', function() {
            autoCompleteYear(this);
        });
    }
});

// ---------- Validation année scolaire ----------
function validateYearFormat(input) {
    const yearPattern = /^\d{4}-\d{4}$/;
    const value = input.value.trim();
    
    if (value && !yearPattern.test(value)) {
        input.classList.add('error');
        return false;
    } else if (value && yearPattern.test(value)) {
        const years = value.split('-');
        const startYear = parseInt(years[0]);
        const endYear = parseInt(years[1]);
        
        if (endYear !== startYear + 1) {
            input.classList.add('error');
            input.setCustomValidity('L\'année de fin doit être l\'année suivante (ex: 2026-2027)');
            return false;
        } else {
            input.classList.remove('error');
            input.setCustomValidity('');
            return true;
        }
    } else {
        input.classList.remove('error');
        input.setCustomValidity('');
        return true;
    }
}

function autoCompleteYear(input) {
    let value = input.value.trim();
    const yearPattern = /^\d{4}-\d{4}$/;
    
    if (value && !yearPattern.test(value)) {
        const match = value.match(/\d{4}/g);
        if (match && match.length >= 2) {
            let startYear = parseInt(match[0]);
            let endYear = parseInt(match[1]);
            if (endYear !== startYear + 1) {
                endYear = startYear + 1;
            }
            const corrected = `${startYear}-${endYear}`;
            input.value = corrected;
            validateYearFormat(input);
        } else if (match && match.length === 1) {
            const startYear = parseInt(match[0]);
            const endYear = startYear + 1;
            const corrected = `${startYear}-${endYear}`;
            input.value = corrected;
            validateYearFormat(input);
        }
    }
}

// ---------- Initialisation du formulaire ----------
function initializeForm() {
    const form = document.getElementById('anneeForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const anneeInput = document.getElementById('annee_scolaire');
            if (!validateYearFormat(anneeInput)) {
                showToast('Format invalide. Utilisez AAAA-AAAA avec années consécutives (ex: 2026-2027)', 'error');
                return;
            }
            
            saveAnnee();
        });
    } else {
        console.error("Formulaire 'anneeForm' non trouvé !");
    }
}

// ---------- Gestion des modales ----------
function initializeModals() {
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
            document.body.style.overflow = 'auto';
            resetForm();
        }
    };
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        resetForm();
    }
}

function resetForm() {
    const anneeId = document.getElementById('annee_id');
    const anneeScolaire = document.getElementById('annee_scolaire');
    const dateDebut = document.getElementById('date_debut');
    const dateFin = document.getElementById('date_fin');
    const estActive = document.getElementById('est_active');
    const modalTitle = document.getElementById('modalAnneeTitle');
    
    if (anneeId) anneeId.value = '';
    if (anneeScolaire) {
        anneeScolaire.value = '';
        anneeScolaire.classList.remove('error');
        anneeScolaire.setCustomValidity('');
    }
    if (dateDebut) {
        dateDebut.value = '';
        dateDebut.classList.remove('error');
    }
    if (dateFin) {
        dateFin.value = '';
        dateFin.classList.remove('error');
    }
    if (estActive) estActive.checked = false;
    if (modalTitle) modalTitle.textContent = 'Ajouter une année scolaire';
    
    document.querySelectorAll('.error').forEach(field => {
        field.classList.remove('error');
    });
}

// ---------- Sauvegarde AJAX ----------
function saveAnnee() {
    const anneeScolaire = document.getElementById('annee_scolaire').value.trim();
    const dateDebut = document.getElementById('date_debut').value.trim();
    const dateFin = document.getElementById('date_fin').value.trim();
    const estActive = document.getElementById('est_active').checked;

    if (!anneeScolaire || !dateDebut || !dateFin) {
        showToast('Veuillez remplir tous les champs', 'error');
        return;
    }

    const submitBtn = document.querySelector('.btn-save');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enregistrement...';
    }

    // Récupération du token CSRF
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!csrfToken) {
        showToast('Erreur : Token CSRF manquant. Rechargez la page.', 'error');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Enregistrer';
        }
        return;
    }

    const data = {
        annee_scolaire: anneeScolaire,
        date_debut: dateDebut,
        date_fin: dateFin,
        est_active: estActive
    };

    fetch('/api/annee/ajouter/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken.value
        },
        body: JSON.stringify(data)
    })
    .then(async response => {
        let responseData;
        try {
            responseData = await response.json();
        } catch (e) {
            throw new Error('Le serveur a retourné une réponse invalide (non JSON)');
        }
        if (!response.ok) {
            throw new Error(responseData.error || `Erreur HTTP ${response.status}`);
        }
        return responseData;
    })
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            closeModal('modalAnnee');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Erreur inconnue', 'error');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Enregistrer';
            }
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        showToast(error.message, 'error');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Enregistrer';
        }
    });
}

// ---------- Affichage des détails d'une année ----------
function viewYearDetails(id) {
    currentYearId = id;
    const modal = document.getElementById('modalYearDetails');
    const content = document.getElementById('yearDetailsContent');
    
    if (!modal || !content) return;
    
    content.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Chargement...</div>';
    modal.style.display = 'block';
    
    fetch(`/api/annee/${id}/stats/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const isActive = data.est_active;
                content.innerHTML = `
                    <div class="stats-grid-mini">
                        <div class="stat-card-mini">
                            <div class="stat-number">${data.inscriptions || 0}</div>
                            <div class="stat-label">Inscriptions</div>
                        </div>
                        <div class="stat-card-mini">
                            <div class="stat-number">${data.notes || 0}</div>
                            <div class="stat-label">Notes saisies</div>
                        </div>
                        <div class="stat-card-mini">
                            <div class="stat-number">${data.classes || 0}</div>
                            <div class="stat-label">Classes actives</div>
                        </div>
                        <div class="stat-card-mini">
                            <div class="stat-number">${data.enseignants || 0}</div>
                            <div class="stat-label">Enseignants</div>
                        </div>
                    </div>
                    <div class="details-list">
                        <div class="details-item">
                            <span class="details-label">Année scolaire</span>
                            <span class="details-value"><strong>${data.annee_scolaire}</strong></span>
                        </div>
                        <div class="details-item">
                            <span class="details-label">Période</span>
                            <span class="details-value">Du ${data.date_debut} au ${data.date_fin}</span>
                        </div>
                        <div class="details-item">
                            <span class="details-label">Statut</span>
                            <span class="details-value">${isActive ? '<span class="status-badge active">Active</span>' : '<span class="status-badge inactive">Inactive</span>'}</span>
                        </div>
                        <div class="details-item">
                            <span class="details-label">Taux de réussite</span>
                            <span class="details-value">${data.taux_reussite || 0}%</span>
                        </div>
                    </div>
                    ${!isActive ? '<div class="alert-info"><i class="fas fa-info-circle"></i> Cette année est inactive. Les données sont en lecture seule.</div>' : ''}
                `;
            } else {
                content.innerHTML = `<div class="error-message">Erreur: ${data.error}</div>`;
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            content.innerHTML = '<div class="error-message">Erreur de chargement des données</div>';
        });
}

function printYearReport(id) {
    const printWindow = window.open(`/api/annee/${id}/print/`, '_blank');
    if (printWindow) {
        printWindow.focus();
    } else {
        alert("Veuillez autoriser les popups pour imprimer");
    }
}

function printYearModal() {
    if (currentYearId) {
        printYearReport(currentYearId);
    }
}

// ---------- Activation / Désactivation ----------
function activateAnnee(id) {
    Swal.fire({
        title: 'Activation',
        text: 'Voulez-vous réactiver cette année scolaire ? L\'année deviendra active et vous pourrez la modifier.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#10b981',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Oui, réactiver',
        cancelButtonText: 'Annuler'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/annee/${id}/activer/`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire('Activée!', data.message, 'success');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    Swal.fire('Erreur', data.error, 'error');
                }
            })
            .catch(error => {
                Swal.fire('Erreur', 'Erreur de connexion au serveur', 'error');
            });
        }
    });
}

function deactivateAnnee(id) {
    Swal.fire({
        title: 'Désactivation',
        text: 'Voulez-vous désactiver cette année scolaire ? Elle deviendra inactive et vous ne pourrez plus la modifier (seulement consultation).',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Oui, désactiver',
        cancelButtonText: 'Annuler'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/annee/${id}/desactiver/`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire('Désactivée!', data.message, 'success');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    Swal.fire('Erreur', data.error, 'error');
                }
            })
            .catch(error => {
                Swal.fire('Erreur', 'Erreur de connexion au serveur', 'error');
            });
        }
    });
}

// ---------- Notification toast ----------
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
}