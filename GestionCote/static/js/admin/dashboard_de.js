// static/js/admin/dashboard_de.js

// Fonction pour ouvrir un modal
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

// Fonction pour fermer un modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Fermer modal en cliquant à l'extérieur
window.onclick = function(event) {
    if (event.target.classList && event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Menu actif - Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', function() {
    // Gestion du menu actif
    const currentUrl = window.location.pathname;
    document.querySelectorAll('.menu-item').forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentUrl === href) {
            item.classList.add('active');
        }
        
        item.addEventListener('click', function() {
            if (!this.getAttribute('href')) {
                document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
});

// Formulaire d'ajout d'enseignant
const enseignantForm = document.getElementById('enseignantForm');
if (enseignantForm) {
    enseignantForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validation des champs
        const nom = this.querySelector('[name="nom"]').value.trim();
        const prenom = this.querySelector('[name="prenom"]').value.trim();
        const email = this.querySelector('[name="email"]').value.trim();
        const specialite = this.querySelector('[name="specialite"]').value.trim();
        
        if (!nom || !prenom || !email || !specialite) {
            Swal.fire('Erreur', 'Veuillez remplir tous les champs obligatoires', 'error');
            return;
        }
        
        const submitBtn = this.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enregistrement...';
        
        const formData = new FormData(this);
        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire('Succès', data.message || 'Enseignant ajouté avec succès !', 'success');
                closeModal('modalEnseignant');
                setTimeout(() => location.reload(), 1500);
            } else {
                Swal.fire('Erreur', data.error || 'Une erreur est survenue', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Enregistrer';
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            Swal.fire('Erreur', 'Erreur de connexion au serveur', 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Enregistrer';
        });
    });
}

// Formulaire d'ajout d'élève
const eleveForm = document.getElementById('eleveForm');
if (eleveForm) {
    eleveForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const nom = this.querySelector('[name="nom"]').value.trim();
        const prenom = this.querySelector('[name="prenom"]').value.trim();
        
        if (!nom || !prenom) {
            Swal.fire('Erreur', 'Veuillez remplir le nom et le prénom', 'error');
            return;
        }
        
        const submitBtn = this.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enregistrement...';
        
        const formData = new FormData(this);
        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire('Succès', data.message || 'Élève ajouté avec succès !', 'success');
                closeModal('modalEleve');
                setTimeout(() => location.reload(), 1500);
            } else {
                Swal.fire('Erreur', data.error || 'Une erreur est survenue', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Enregistrer';
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            Swal.fire('Erreur', 'Erreur de connexion au serveur', 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Enregistrer';
        });
    });
}

// Formulaire année scolaire
const anneeForm = document.getElementById('anneeForm');
if (anneeForm) {
    anneeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const anneeScolaire = this.querySelector('[name="annee_scolaire"]').value.trim();
        const dateDebut = this.querySelector('[name="date_debut"]').value;
        const dateFin = this.querySelector('[name="date_fin"]').value;
        
        if (!anneeScolaire || !dateDebut || !dateFin) {
            Swal.fire('Erreur', 'Veuillez remplir tous les champs', 'error');
            return;
        }
        
        const submitBtn = this.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enregistrement...';
        
        const formData = new FormData(this);
        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire('Succès', data.message || 'Année scolaire définie avec succès !', 'success');
                closeModal('modalAnnee');
                setTimeout(() => location.reload(), 1500);
            } else {
                Swal.fire('Erreur', data.error || 'Une erreur est survenue', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Enregistrer';
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            Swal.fire('Erreur', 'Erreur de connexion au serveur', 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Enregistrer';
        });
    });
}

// Export PDF
function exportPDF() {
    Swal.fire({
        title: 'Export PDF',
        text: 'Préparation de l\'export des archives...',
        icon: 'info',
        confirmButtonColor: '#1e3c72'
    });
}

// Export Excel
function exportExcel() {
    Swal.fire({
        title: 'Export Excel',
        text: 'Préparation de l\'export des rapports...',
        icon: 'info',
        confirmButtonColor: '#1e3c72'
    });
}

// Générer palmarès
function genererPalmares() {
    Swal.fire({
        title: 'Génération du palmarès',
        text: 'Voulez-vous générer le palmarès de l\'année ?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#1e3c72',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Oui, générer',
        cancelButtonText: 'Annuler'
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'Génération en cours...',
                text: 'Veuillez patienter',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            fetch('/api/palmares/generer/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire('Généré!', data.message || 'Palmarès généré avec succès!', 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    Swal.fire('Erreur', data.error || 'Une erreur est survenue', 'error');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                Swal.fire('Erreur', 'Erreur de connexion au serveur', 'error');
            });
        }
    });
}

// Chargement des données en temps réel
function loadStats() {
    fetch('/api/stats/data/')
        .then(response => response.json())
        .then(data => {
            const totalEleves = document.getElementById('totalEleves');
            const totalEnseignants = document.getElementById('totalEnseignants');
            const totalClasses = document.getElementById('totalClasses');
            const tauxReussite = document.getElementById('tauxReussite');
            
            if (totalEleves && data.total_eleves !== undefined) {
                totalEleves.textContent = data.total_eleves;
            }
            if (totalEnseignants && data.total_enseignants !== undefined) {
                totalEnseignants.textContent = data.total_enseignants;
            }
            if (totalClasses && data.total_classes !== undefined) {
                totalClasses.textContent = data.total_classes;
            }
            if (tauxReussite && data.taux_reussite !== undefined) {
                tauxReussite.textContent = data.taux_reussite + '%';
            }
        })
        .catch(error => console.error('Erreur chargement stats:', error));
}

// Décommentez la ligne suivante si vous voulez un rafraîchissement automatique toutes les 30 secondes
// setInterval(loadStats, 30000);