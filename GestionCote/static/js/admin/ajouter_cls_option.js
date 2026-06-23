// static/js/admin/ajouter_cls_option.js

let currentTab = 'classes';
let originalCycle = '';

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM chargé - Initialisation du gestionnaire de classes et options');
    initializeTabs();
    initializeForms();
    initializeModals();
    initClasseFormDynamic();
});

function initializeTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`tab-${this.dataset.tab}`).classList.add('active');
            console.log(`✅ Onglet changé: ${this.dataset.tab}`);
        });
    });
}

function initializeForms() {
    // Classe Form
    const classeForm = document.getElementById('classeForm');
    if (classeForm) {
        // Supprimer l'événement submit par défaut
        classeForm.onsubmit = function(e) {
            e.preventDefault();
            console.log('📝 Formulaire classe soumis');
            saveClasse();
            return false;
        };
        console.log('✅ Formulaire classe initialisé');
    } else {
        console.warn('⚠️ Formulaire classe non trouvé');
    }
    
    // Option Form
    const optionForm = document.getElementById('optionForm');
    if (optionForm) {
        optionForm.onsubmit = function(e) {
            e.preventDefault();
            console.log('📝 Formulaire option soumis');
            saveOption();
            return false;
        };
        console.log('✅ Formulaire option initialisé');
    } else {
        console.warn('⚠️ Formulaire option non trouvé');
    }
}

function initializeModals() {
    window.onclick = event => { 
        if (event.target.classList.contains('modal')) {
            console.log('🔴 Fermeture de la modale:', event.target.id);
            closeModal(event.target.id); 
        }
    };
    console.log('✅ Modales initialisées');
}

function openModal(modalId) {
    console.log('🟢 Ouverture de la modale:', modalId);
    document.getElementById(modalId).style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal(modalId) {
    console.log('🔴 Fermeture de la modale:', modalId);
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    if (modalId === 'modalClasse') resetClasseForm();
    if (modalId === 'modalOption') resetOptionForm();
}

function resetClasseForm() {
    console.log('🔄 Réinitialisation du formulaire classe');
    document.getElementById('classe_id').value = '';
    const cycleSelect = document.getElementById('cycle_select');
    cycleSelect.disabled = false;
    cycleSelect.value = '';
    const anneeSelect = document.getElementById('annee_select');
    anneeSelect.disabled = true;
    anneeSelect.innerHTML = '<option value="">-- Année --</option>';
    document.getElementById('division_select').value = '';
    document.getElementById('classe_capacite').value = '30';
    document.getElementById('classe_actif').checked = true;
    document.getElementById('classe_nom_preview').textContent = '-';
    document.getElementById('classe_nom_hidden').value = '';
    document.getElementById('option_group_classe').style.display = 'none';
    document.getElementById('classe_option').value = '';
    document.getElementById('modalClasseTitle').textContent = 'Ajouter une classe';
    if (typeof window.updateAnneeOptions === 'function') window.updateAnneeOptions();
    originalCycle = '';
}

function resetOptionForm() {
    console.log('🔄 Réinitialisation du formulaire option');
    document.getElementById('option_id').value = '';
    document.getElementById('option_nom').value = '';
    document.getElementById('option_code').value = '';
    document.getElementById('option_actif').checked = true;
    document.getElementById('modalOptionTitle').textContent = 'Ajouter une option';
}

// Dynamique du formulaire classe
function initClasseFormDynamic() {
    console.log('🔄 Initialisation du formulaire dynamique');
    const cycleSelect = document.getElementById('cycle_select');
    const anneeSelect = document.getElementById('annee_select');
    const divisionSelect = document.getElementById('division_select');
    const optionGroup = document.getElementById('option_group_classe');
    const optionSelect = document.getElementById('classe_option');
    const nomPreview = document.getElementById('classe_nom_preview');
    const nomHidden = document.getElementById('classe_nom_hidden');

    const anneeMap = {
        'CO': [{v:'7',l:'7ème année'},{v:'8',l:'8ème année'}],
        'SECONDAIRE': [{v:'1',l:'1ère année'},{v:'2',l:'2ème année'},{v:'3',l:'3ème année'},{v:'4',l:'4ème année (Terminale)'}]
    };
    
    function updateAnneeOptions() {
        const cycle = cycleSelect.value;
        console.log('🔄 Mise à jour des options d\'année pour le cycle:', cycle);
        anneeSelect.innerHTML = '<option value="">-- Année --</option>';
        if (cycle && anneeMap[cycle]) {
            anneeMap[cycle].forEach(a => { 
                let opt = document.createElement('option'); 
                opt.value = a.v; 
                opt.textContent = a.l; 
                anneeSelect.appendChild(opt); 
            });
            anneeSelect.disabled = false;
        } else {
            anneeSelect.disabled = true;
        }
        if (cycle === 'SECONDAIRE') {
            optionGroup.style.display = 'block';
            optionSelect.required = true;
        } else {
            optionGroup.style.display = 'none';
            optionSelect.required = false;
            optionSelect.value = '';
        }
        updateNomClasse();
    }
    
    function updateNomClasse() {
        const cycle = cycleSelect.value;
        const annee = anneeSelect.value;
        const division = divisionSelect.value;
        if (cycle && annee && division) {
            let nom = '';
            if (cycle === 'CO') {
                nom = `${annee}ème ${division} (CO)`;
            } else {
                let anneeTxt = (annee === '1' ? '1ère' : (annee === '4' ? '4ème (Terminale)' : `${annee}ème`));
                nom = `${anneeTxt} ${division}`;
            }
            nomPreview.textContent = nom;
            nomHidden.value = nom;
            let niveauHidden = document.getElementById('classe_niveau_hidden');
            if (!niveauHidden) {
                niveauHidden = document.createElement('input');
                niveauHidden.type = 'hidden';
                niveauHidden.name = 'niveau';
                niveauHidden.id = 'classe_niveau_hidden';
                document.getElementById('classeForm').appendChild(niveauHidden);
            }
            niveauHidden.value = (cycle === 'CO') ? `${annee}ème année - Cycle d'Orientation` : `${annee}ème année - Secondaire`;
            console.log('📝 Nom généré:', nom);
        } else {
            nomPreview.textContent = '-';
            nomHidden.value = '';
        }
    }
    
    cycleSelect.addEventListener('change', function() {
        console.log('🔄 Cycle changé:', this.value);
        updateAnneeOptions();
    });
    anneeSelect.addEventListener('change', function() {
        console.log('🔄 Année changée:', this.value);
        updateNomClasse();
    });
    divisionSelect.addEventListener('change', function() {
        console.log('🔄 Division changée:', this.value);
        updateNomClasse();
    });
    
    window.updateAnneeOptions = updateAnneeOptions;
    updateAnneeOptions();
    console.log('✅ Formulaire dynamique initialisé');
}

// =============================================
// SAUVEGARDE CLASSE - CORRIGÉE
// =============================================

function saveClasse() {
    console.log('📝 Début de la sauvegarde de la classe');
    
    const form = document.getElementById('classeForm');
    if (!form) {
        console.error('❌ Formulaire non trouvé');
        showToast('Formulaire non trouvé', 'error');
        return;
    }
    
    const formData = new FormData(form);
    const classeId = document.getElementById('classe_id').value;
    
    // Récupération des valeurs depuis les champs actifs
    const cycle = document.getElementById('cycle_select').value;
    const annee = document.getElementById('annee_select').value;
    const division = document.getElementById('division_select').value;
    
    console.log('📝 Cycle:', cycle, 'Année:', annee, 'Division:', division);
    
    if (!cycle || !annee || !division) {
        console.warn('⚠️ Champs manquants');
        showToast('Veuillez sélectionner le cycle, l\'année et la division', 'error');
        return;
    }
    
    const optionSelect = document.getElementById('classe_option');
    if (cycle === 'SECONDAIRE' && !optionSelect.value) {
        console.warn('⚠️ Option manquante pour le secondaire');
        showToast('Veuillez sélectionner une option pour le cycle secondaire', 'error');
        return;
    }
    
    // Générer le nom de la classe
    let nomClasse = '';
    if (cycle === 'CO') {
        nomClasse = `${annee}ème ${division} (CO)`;
    } else {
        let anneeTxt = (annee === '1' ? '1ère' : (annee === '4' ? '4ème (Terminale)' : `${annee}ème`));
        nomClasse = `${anneeTxt} ${division}`;
    }
    
    // Mettre à jour les champs cachés
    document.getElementById('classe_nom_hidden').value = nomClasse;
    const niveauHidden = document.getElementById('classe_niveau_hidden');
    if (niveauHidden) {
        niveauHidden.value = (cycle === 'CO') ? `${annee}ème année - Cycle d'Orientation` : `${annee}ème année - Secondaire`;
    }
    
    // Ajouter les données manquantes au FormData
    formData.set('nom_classe', nomClasse);
    formData.set('est_cycle_orientation', cycle === 'CO' ? 'true' : 'false');
    
    if (classeId) {
        formData.append('classe_id', classeId);
        console.log('📝 Modification de la classe ID:', classeId);
    } else {
        console.log('📝 Création d\'une nouvelle classe');
    }
    
    console.log('📝 Nom de la classe:', nomClasse);
    
    // Récupérer le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                      document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
    
    if (!csrfToken) {
        console.error('❌ Token CSRF non trouvé');
        showToast('Erreur de sécurité : token CSRF manquant', 'error');
        return;
    }
    
    // Désactiver le bouton
    const submitBtn = document.querySelector('#classeForm .btn-save');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Enregistrement...';
    }
    
    console.log('📡 Envoi de la requête à /api/classe/ajouter/');
    
    fetch('/api/classe/ajouter/', {
        method: 'POST',
        body: formData,
        headers: { 
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(async response => {
        console.log('📡 Statut de la réponse:', response.status);
        
        // Lire la réponse comme texte d'abord
        const text = await response.text();
        console.log('📡 Réponse brute:', text);
        
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error('❌ Erreur de parsing JSON:', e);
            throw new Error('La réponse du serveur n\'est pas du JSON valide');
        }
        
        if (!response.ok) {
            throw new Error(data.error || `Erreur HTTP ${response.status}`);
        }
        
        return data;
    })
    .then(data => {
        console.log('📡 Données reçues:', data);
        if (data.success) {
            console.log('✅ Classe enregistrée avec succès');
            showToast(data.message, 'success');
            setTimeout(() => {
                closeModal('modalClasse');
                location.reload();
            }, 1500);
        } else {
            console.error('❌ Erreur serveur:', data.error);
            showToast(data.error || 'Erreur lors de l\'enregistrement', 'error');
            // Réactiver le bouton
            const submitBtn = document.querySelector('#classeForm .btn-save');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Enregistrer';
            }
        }
    })
    .catch(err => {
        console.error('❌ Erreur:', err);
        showToast(err.message || 'Erreur réseau, veuillez réessayer', 'error');
        const submitBtn = document.querySelector('#classeForm .btn-save');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Enregistrer';
        }
    });
}

// Édition d'une classe
function editClasse(id) {
    console.log('📝 Édition de la classe ID:', id);
    Swal.fire({
        title: 'Chargement...',
        text: 'Veuillez patienter',
        allowOutsideClick: false,
        didOpen: () => Swal.showLoading()
    });
    
    fetch(`/api/classe/${id}/get/`)
        .then(async response => {
            if (!response.ok) {
                const text = await response.text();
                throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
            }
            return response.json();
        })
        .then(data => {
            Swal.close();
            console.log('📡 Données de la classe:', data);
            if (data.success) {
                const classe = data.classe;
                document.getElementById('classe_id').value = classe.id;
                document.getElementById('classe_capacite').value = classe.capacite_max;
                document.getElementById('classe_actif').checked = classe.actif;
                document.getElementById('modalClasseTitle').textContent = 'Modifier la classe';
                
                const cycle = classe.est_cycle_orientation ? 'CO' : 'SECONDAIRE';
                originalCycle = cycle;
                
                let annee = '';
                let division = '';
                let nom = classe.nom_classe;
                
                if (cycle === 'CO') {
                    let match = nom.match(/^(\d+)ème\s+([A-E])\s+\(CO\)$/);
                    if (match) {
                        annee = match[1];
                        division = match[2];
                    } else {
                        let parts = nom.split(' ');
                        if (parts.length >= 2) {
                            annee = parts[0].replace('ème', '');
                            division = parts[1];
                        }
                    }
                } else {
                    let match = nom.match(/^(1ère|2ème|3ème|4ème(?: \(Terminale\))?)\s+([A-E])$/);
                    if (match) {
                        let anneeRaw = match[1];
                        if (anneeRaw === '1ère') annee = '1';
                        else if (anneeRaw === '2ème') annee = '2';
                        else if (anneeRaw === '3ème') annee = '3';
                        else if (anneeRaw.startsWith('4ème')) annee = '4';
                        division = match[2];
                    } else {
                        let parts = nom.split(' ');
                        if (parts.length >= 2) {
                            let first = parts[0];
                            if (first === '1ère') annee = '1';
                            else if (first === '4ème' || first === '4ème(Terminale)') annee = '4';
                            else if (first.endsWith('ème')) annee = first.replace('ème', '');
                            division = parts[1];
                        }
                    }
                }
                
                const cycleSelect = document.getElementById('cycle_select');
                cycleSelect.value = cycle;
                cycleSelect.dispatchEvent(new Event('change'));
                
                setTimeout(() => {
                    if (annee) {
                        const anneeSelect = document.getElementById('annee_select');
                        anneeSelect.value = annee;
                    }
                    if (division) {
                        const divisionSelect = document.getElementById('division_select');
                        divisionSelect.value = division;
                    }
                    
                    if (cycle === 'SECONDAIRE') {
                        if (classe.id_option) {
                            const optionSelect = document.getElementById('classe_option');
                            optionSelect.value = classe.id_option;
                        }
                    }
                }, 200);
                
                openModal('modalClasse');
                console.log('✅ Classe chargée pour édition');
            } else {
                Swal.fire('Erreur', data.error || 'Impossible de charger la classe', 'error');
            }
        })
        .catch(error => {
            Swal.close();
            console.error('❌ Erreur:', error);
            Swal.fire('Erreur', error.message || 'Impossible de charger la classe', 'error');
        });
}

// Activer/Désactiver une classe
function toggleClasseStatus(id, currentStatus) {
    console.log(`🔄 Changement de statut classe ${id}: ${currentStatus ? 'Actif' : 'Inactif'} → ${currentStatus ? 'Inactif' : 'Actif'}`);
    Swal.fire({ 
        title: 'Confirmation', 
        text: `Voulez-vous ${currentStatus ? 'désactiver' : 'activer'} cette classe ?`, 
        icon: 'question', 
        showCancelButton: true 
    }).then(res => {
        if (res.isConfirmed) {
            fetch(`/api/classe/${id}/toggle/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ actif: !currentStatus })
            })
            .then(async response => {
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) { 
                    showToast(data.message, 'success'); 
                    setTimeout(() => location.reload(), 1000); 
                } else {
                    showToast(data.error, 'error');
                }
            })
            .catch(err => {
                console.error('❌ Erreur:', err);
                showToast('Erreur réseau', 'error');
            });
        }
    });
}

// Supprimer une classe
function deleteClasse(id) {
    console.log(`🗑️ Suppression de la classe ID: ${id}`);
    Swal.fire({ 
        title: 'Suppression', 
        text: 'Cette action est irréversible.', 
        icon: 'warning', 
        showCancelButton: true 
    }).then(res => {
        if (res.isConfirmed) {
            Swal.fire({
                title: 'Suppression en cours...',
                text: 'Veuillez patienter',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });
            fetch(`/api/classe/${id}/supprimer/`, { 
                method: 'DELETE', 
                headers: { 
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value 
                } 
            })
            .then(async response => {
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) { 
                    showToast(data.message, 'success'); 
                    location.reload(); 
                } else {
                    Swal.fire('Erreur', data.error, 'error');
                }
            })
            .catch(err => {
                console.error('❌ Erreur:', err);
                Swal.fire('Erreur', 'Erreur réseau', 'error');
            });
        }
    });
}

// =============================================
// OPTIONS
// =============================================

function saveOption() {
    console.log('📝 Début de la sauvegarde de l\'option');
    
    const form = document.getElementById('optionForm');
    if (!form) {
        console.error('❌ Formulaire option non trouvé');
        showToast('Formulaire option non trouvé', 'error');
        return;
    }
    
    const formData = new FormData(form);
    const optionId = document.getElementById('option_id').value;
    
    if (optionId) {
        console.log('📝 Modification de l\'option ID:', optionId);
    } else {
        console.log('📝 Création d\'une nouvelle option');
    }
    
    const nom = document.getElementById('option_nom').value.trim();
    const code = document.getElementById('option_code').value.trim();
    
    if (!nom || !code) {
        console.warn('⚠️ Champs manquants');
        showToast('Veuillez remplir le nom et le code de l\'option', 'error');
        return;
    }
    
    // Récupérer le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                      document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
    
    if (!csrfToken) {
        console.error('❌ Token CSRF non trouvé');
        showToast('Erreur de sécurité : token CSRF manquant', 'error');
        return;
    }
    
    // Afficher un indicateur de chargement
    const submitBtn = document.querySelector('#optionForm .btn-save');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Enregistrement...';
    }
    
    fetch('/api/option/ajouter/', {
        method: 'POST',
        body: formData,
        headers: { 
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(async response => {
        console.log('📡 Réponse du serveur:', response.status);
        
        const text = await response.text();
        console.log('📡 Réponse brute:', text);
        
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error('❌ Erreur de parsing JSON:', e);
            throw new Error('La réponse du serveur n\'est pas du JSON valide');
        }
        
        if (!response.ok) {
            throw new Error(data.error || `Erreur HTTP ${response.status}`);
        }
        
        return data;
    })
    .then(data => {
        console.log('📡 Données reçues:', data);
        if (data.success) {
            console.log('✅ Option enregistrée avec succès');
            showToast(data.message, 'success');
            setTimeout(() => {
                closeModal('modalOption');
                location.reload();
            }, 1500);
        } else {
            console.error('❌ Erreur serveur:', data.error);
            showToast(data.error || 'Erreur lors de l\'enregistrement', 'error');
            const submitBtn = document.querySelector('#optionForm .btn-save');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Enregistrer';
            }
        }
    })
    .catch(err => {
        console.error('❌ Erreur:', err);
        showToast(err.message || 'Erreur réseau, veuillez réessayer', 'error');
        const submitBtn = document.querySelector('#optionForm .btn-save');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Enregistrer';
        }
    });
}

function editOption(id) {
    console.log('📝 Édition de l\'option ID:', id);
    Swal.fire({ 
        title: 'Chargement...', 
        didOpen: () => Swal.showLoading() 
    });
    
    fetch(`/api/option/${id}/get/`)
        .then(async response => {
            if (!response.ok) {
                const text = await response.text();
                throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
            }
            return response.json();
        })
        .then(data => {
            Swal.close();
            console.log('📡 Données de l\'option:', data);
            if(data.success){
                document.getElementById('option_id').value = data.option.id;
                document.getElementById('option_nom').value = data.option.nom_option;
                document.getElementById('option_code').value = data.option.code_option;
                document.getElementById('option_actif').checked = data.option.actif;
                document.getElementById('modalOptionTitle').textContent = 'Modifier l\'option';
                openModal('modalOption');
                console.log('✅ Option chargée pour édition');
            } else {
                Swal.fire('Erreur', data.error, 'error');
            }
        })
        .catch(error => {
            Swal.close();
            console.error('❌ Erreur:', error);
            Swal.fire('Erreur', error.message || 'Impossible de charger l\'option', 'error');
        });
}

function toggleOptionStatus(id, currentStatus) {
    console.log(`🔄 Changement de statut option ${id}: ${currentStatus ? 'Actif' : 'Inactif'} → ${currentStatus ? 'Inactif' : 'Actif'}`);
    Swal.fire({ 
        title: 'Confirmation', 
        text: `Voulez-vous ${currentStatus ? 'désactiver' : 'activer'} cette option ?`, 
        icon: 'question', 
        showCancelButton: true 
    }).then(res => {
        if(res.isConfirmed){
            fetch(`/api/option/${id}/toggle/`, {
                method:'POST',
                headers:{
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type':'application/json'
                },
                body: JSON.stringify({actif: !currentStatus})
            })
            .then(async response => {
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
                }
                return response.json();
            })
            .then(data => {
                if(data.success){ 
                    showToast(data.message, 'success'); 
                    location.reload(); 
                } else {
                    showToast(data.error, 'error');
                }
            })
            .catch(err => {
                console.error('❌ Erreur:', err);
                showToast('Erreur réseau', 'error');
            });
        }
    });
}

function deleteOption(id) {
    console.log(`🗑️ Suppression de l'option ID: ${id}`);
    Swal.fire({ 
        title:'Suppression', 
        text:'Irréversible', 
        icon:'warning', 
        showCancelButton:true 
    }).then(res => {
        if(res.isConfirmed){
            Swal.fire({ 
                title:'Suppression...', 
                text:'Veuillez patienter', 
                allowOutsideClick:false, 
                didOpen:() => Swal.showLoading() 
            });
            fetch(`/api/option/${id}/supprimer/`, { 
                method:'DELETE', 
                headers:{ 
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value 
                } 
            })
            .then(async response => {
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
                }
                return response.json();
            })
            .then(data => {
                if(data.success){ 
                    showToast(data.message, 'success'); 
                    location.reload(); 
                } else {
                    Swal.fire('Erreur', data.error, 'error');
                }
            })
            .catch(err => {
                console.error('❌ Erreur:', err);
                Swal.fire('Erreur', 'Erreur réseau', 'error');
            });
        }
    });
}

// =============================================
// SYSTEME DE TOAST (NOTIFICATION) - CENTRÉ
// =============================================
function showToast(msg, type = 'success') {
    console.log(`🔔 Toast: ${type} - ${msg}`);
    
    const colors = {
        'success': '#10b981',
        'error': '#ef4444',
        'warning': '#f59e0b',
        'info': '#3b82f6'
    };
    
    const icons = {
        'success': 'success',
        'error': 'error',
        'warning': 'warning',
        'info': 'info'
    };
    
    const titles = {
        'success': '✅ Succès',
        'error': '❌ Erreur',
        'warning': '⚠️ Attention',
        'info': 'ℹ️ Information'
    };
    
    // Utiliser SweetAlert2 pour un affichage centré professionnel
    Swal.fire({
        icon: icons[type] || 'info',
        title: titles[type] || 'Information',
        text: msg,
        confirmButtonColor: colors[type] || '#10b981',
        confirmButtonText: 'OK',
        timer: type === 'success' ? 2500 : 5000,
        timerProgressBar: true,
        toast: type === 'success' ? true : false,
        position: type === 'success' ? 'top-end' : 'center',
        showConfirmButton: type !== 'success',
        showClass: {
            popup: 'animate__animated animate__fadeInUp'
        },
        hideClass: {
            popup: 'animate__animated animate__fadeOutDown'
        },
        background: document.documentElement.getAttribute('data-theme') === 'dark' ? '#1A1D24' : '#ffffff',
        color: document.documentElement.getAttribute('data-theme') === 'dark' ? '#F3F4F6' : '#1e293b',
        iconColor: colors[type] || '#10b981'
    });
}

// =============================================
// FONCTION UTILITAIRE POUR LE TOKEN CSRF
// =============================================
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
           document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || 
           document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
}

console.log('✅ ajouter_cls_option.js chargé avec succès');