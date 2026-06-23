// static/js/admin/reinscription.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation
    initSearchInstant();
    initRedoublementCheckbox();
    initFormSubmit();
    initWizardSteps();
    autoSelectClass();
    initClassSelection();
    handleMessages();
    initDynamicFilters();
});

// Configuration des niveaux
const NIVEAUX_CONFIG = {
    'CO': {
        label: 'Cycle d\'Orientation',
        niveaux: ['7e', '8e'],
        suivant: {
            '7e': '8e',
            '8e': '1ère'
        }
    },
    'SECONDAIRE': {
        label: 'Secondaire',
        niveaux: ['1ère', '2ème', '3ème', '4ème'],
        suivant: {
            '1ère': '2ème',
            '2ème': '3ème',
            '3ème': '4ème',
            '4ème': null
        }
    }
};

// Fonction pour déterminer le cycle d'un niveau
function getCycleFromNiveau(niveau) {
    if (['7e', '8e'].includes(niveau)) return 'CO';
    if (['1ère', '2ème', '3ème', '4ème'].includes(niveau)) return 'SECONDAIRE';
    return null;
}

// Fonction pour obtenir le niveau suivant
function getProchainNiveau(niveauActuel) {
    const cycle = getCycleFromNiveau(niveauActuel);
    if (!cycle) return null;
    return NIVEAUX_CONFIG[cycle].suivant[niveauActuel] || null;
}

// =============================================
// GESTION DES FILTRES DYNAMIQUES (Cycle → Niveau → Classe)
// =============================================

function initDynamicFilters() {
    const cycleSelect = document.getElementById('cycle_select');
    const niveauSelect = document.getElementById('niveau_select');
    const classeSelect = document.getElementById('classe_id');
    
    if (!cycleSelect || !niveauSelect || !classeSelect) return;
    
    // Événement : changement de cycle
    cycleSelect.addEventListener('change', function() {
        const cycle = this.value;
        niveauSelect.innerHTML = '<option value="">-- Sélectionnez un niveau --</option>';
        classeSelect.innerHTML = '<option value="">-- Sélectionnez d\'abord un niveau --</option>';
        classeSelect.disabled = true;
        
        if (!cycle) {
            niveauSelect.disabled = true;
            niveauSelect.innerHTML = '<option value="">-- Sélectionnez d\'abord un cycle --</option>';
            return;
        }
        
        // Charger les niveaux pour ce cycle
        fetch(`/api/reinscription/niveaux/?cycle=${encodeURIComponent(cycle)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.niveaux && data.niveaux.length > 0) {
                    niveauSelect.disabled = false;
                    let options = '<option value="">-- Sélectionnez un niveau --</option>';
                    data.niveaux.forEach(niveau => {
                        // Utiliser window.prochainNiveau pour la sélection
                        const selected = (window.prochainNiveau && niveau === window.prochainNiveau) ? 'selected' : '';
                        options += `<option value="${niveau}" ${selected}>${niveau}</option>`;
                    });
                    niveauSelect.innerHTML = options;
                    
                    // Si un prochain niveau est défini, déclencher le chargement des classes
                    if (window.prochainNiveau && data.niveaux.includes(window.prochainNiveau)) {
                        niveauSelect.value = window.prochainNiveau;
                        niveauSelect.dispatchEvent(new Event('change'));
                    }
                } else {
                    niveauSelect.disabled = true;
                    niveauSelect.innerHTML = '<option value="">-- Aucun niveau disponible --</option>';
                    const helpText = document.getElementById('classe_help');
                    if (helpText) {
                        helpText.textContent = '⚠️ Aucun niveau disponible pour ce cycle. Veuillez créer des classes.';
                    }
                }
            })
            .catch(error => {
                console.error('Erreur chargement niveaux:', error);
                showMessage('Erreur de chargement des niveaux', 'error');
            });
    });
    
    // Événement : changement de niveau
    niveauSelect.addEventListener('change', function() {
        const niveau = this.value;
        classeSelect.innerHTML = '<option value="">-- Sélectionnez d\'abord un niveau --</option>';
        classeSelect.disabled = true;
        
        if (!niveau) {
            classeSelect.innerHTML = '<option value="">-- Sélectionnez d\'abord un niveau --</option>';
            const helpText = document.getElementById('classe_help');
            if (helpText) {
                helpText.textContent = 'Sélectionnez un niveau pour voir les classes disponibles';
            }
            return;
        }
        
        // Charger les classes pour ce niveau
        fetch(`/api/reinscription/classes/?niveau=${encodeURIComponent(niveau)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.classes && data.classes.length > 0) {
                    classeSelect.disabled = false;
                    let options = '<option value="">-- Sélectionnez une classe --</option>';
                    data.classes.forEach(classe => {
                        const optionText = classe.option ? 
                            `${classe.nom_classe} (${classe.option})` : 
                            classe.nom_classe;
                        const selected = (window.classeId && classe.id === window.classeId) ? 'selected' : '';
                        options += `<option value="${classe.id}" data-niveau="${classe.niveau}" data-cycle="${classe.est_cycle_orientation ? 'CO' : 'SECONDAIRE'}" ${selected}>${optionText}</option>`;
                    });
                    classeSelect.innerHTML = options;
                    const helpText = document.getElementById('classe_help');
                    if (helpText) {
                        helpText.textContent = `${data.classes.length} classe(s) disponible(s) pour le niveau ${niveau}`;
                    }
                    
                    // Auto-sélection de la première classe si une seule disponible
                    if (data.classes.length === 1) {
                        classeSelect.value = data.classes[0].id;
                        if (helpText) {
                            helpText.textContent = `✅ ${data.classes[0].nom_classe} sélectionnée automatiquement`;
                        }
                    }
                } else {
                    classeSelect.disabled = true;
                    classeSelect.innerHTML = `<option value="">-- Aucune classe pour le niveau ${niveau} --</option>`;
                    const helpText = document.getElementById('classe_help');
                    if (helpText) {
                        helpText.textContent = `⚠️ Aucune classe disponible pour le niveau ${niveau}. Veuillez créer une classe dans "Gestion des classes et options".`;
                    }
                }
            })
            .catch(error => {
                console.error('Erreur chargement classes:', error);
                showMessage('Erreur de chargement des classes', 'error');
            });
    });
    
    // Si un prochain niveau est défini, pré-sélectionner le cycle et le niveau
    // Utiliser window.prochainNiveau qui est défini dans le template
    if (window.prochainNiveau) {
        const cycle = getCycleFromNiveau(window.prochainNiveau);
        if (cycle) {
            cycleSelect.value = cycle;
            cycleSelect.dispatchEvent(new Event('change'));
        }
    }
}

// =============================================
// GESTION DES MESSAGES AVEC SWEETALERT2
// =============================================

function handleMessages() {
    const messagesContainer = document.querySelector('.messages');
    if (!messagesContainer) return;
    
    const messages = messagesContainer.querySelectorAll('.alert');
    if (messages.length === 0) return;
    
    messagesContainer.style.display = 'none';
    
    messages.forEach(function(alert) {
        const message = alert.textContent.trim();
        const isError = alert.classList.contains('alert-danger') || alert.classList.contains('error');
        const isSuccess = alert.classList.contains('alert-success');
        const isWarning = alert.classList.contains('alert-warning');
        const isInfo = alert.classList.contains('alert-info');
        
        let icon = 'info';
        if (isError) icon = 'error';
        else if (isSuccess) icon = 'success';
        else if (isWarning) icon = 'warning';
        
        Swal.fire({
            icon: icon,
            title: isError ? '❌ Erreur' : 
                   isSuccess ? '✅ Succès' : 
                   isWarning ? '⚠️ Attention' : 'ℹ️ Information',
            text: message,
            confirmButtonColor: isError ? '#ef4444' : 
                               isSuccess ? '#10b981' : 
                               '#3b82f6',
            confirmButtonText: 'OK',
            timer: isSuccess ? 3000 : 5000,
            timerProgressBar: true,
            toast: isSuccess ? true : false,
            position: isSuccess ? 'top-end' : 'center',
            showConfirmButton: !isSuccess,
        });
    });
}

// Fonction pour afficher un message personnalisé
function showMessage(message, type = 'info', title = null) {
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
    
    const colors = {
        'success': '#10b981',
        'error': '#ef4444',
        'warning': '#f59e0b',
        'info': '#3b82f6'
    };
    
    Swal.fire({
        icon: icons[type] || 'info',
        title: title || titles[type] || 'Information',
        text: message,
        confirmButtonColor: colors[type] || '#3b82f6',
        confirmButtonText: 'OK',
        timer: type === 'success' ? 3000 : 5000,
        timerProgressBar: true,
        toast: type === 'success' ? true : false,
        position: type === 'success' ? 'top-end' : 'center',
        showConfirmButton: type !== 'success',
    });
}

// =============================================
// GESTION DE LA RECHERCHE INSTANTANÉE
// =============================================

function initSearchInstant() {
    const searchInput = document.getElementById('matriculeSearch');
    const resultsDiv = document.getElementById('instantSearchResults');
    let searchTimeout = null;

    if (!searchInput || !resultsDiv) return;

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length < 3) {
            resultsDiv.style.display = 'none';
            return;
        }

        searchTimeout = setTimeout(() => {
            fetch('/api/reinscription/search-eleve/?q=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.data && data.data.length > 0) {
                        let html = '';
                        data.data.forEach(etudiant => {
                            let nomComplet = '';
                            if (etudiant.prenom) nomComplet += etudiant.prenom + ' ';
                            if (etudiant.postnom) nomComplet += etudiant.postnom + ' ';
                            if (etudiant.nom) nomComplet += etudiant.nom;
                            nomComplet = escapeHtml(nomComplet.trim());

                            const avatarColor = etudiant.sexe === 'M' ? 
                                'linear-gradient(135deg, #2E8B57, #4682B4)' : 
                                'linear-gradient(135deg, #FF69B4, #FF1493)';

                            html += `
                                <div class="result-item" onclick="window.location.href='?matricule=${encodeURIComponent(etudiant.matricule)}'">
                                    <div class="result-avatar" style="background: ${avatarColor};">
                                        <i class="fas fa-user-graduate"></i>
                                    </div>
                                    <div class="result-info">
                                        <span class="result-name">${nomComplet}</span>
                                        <div class="result-details">
                                            <span><i class="fas fa-id-card"></i> ${escapeHtml(etudiant.matricule)}</span>
                                        </div>
                                    </div>
                                    <i class="fas fa-chevron-right" style="color: var(--text-secondary, #6b7280);"></i>
                                </div>
                            `;
                        });
                        resultsDiv.innerHTML = html;
                        resultsDiv.style.display = 'block';
                    } else {
                        resultsDiv.innerHTML = `
                            <div class="result-item" style="justify-content: center; gap: 10px;">
                                <i class="fas fa-user-slash" style="color: var(--text-secondary, #6b7280);"></i>
                                <span>Aucun élève trouvé pour "${escapeHtml(query)}"</span>
                            </div>
                        `;
                        resultsDiv.style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Erreur recherche:', error);
                    showMessage('Erreur de connexion au serveur', 'error');
                    resultsDiv.innerHTML = `
                        <div class="result-item" style="justify-content: center; gap: 10px;">
                            <i class="fas fa-exclamation-triangle" style="color: #ef4444;"></i>
                            <span>Erreur de connexion au serveur</span>
                        </div>
                    `;
                    resultsDiv.style.display = 'block';
                });
        }, 500);
    });

    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-container')) {
            resultsDiv.style.display = 'none';
        }
    });
}

// =============================================
// GESTION DU REDOUBLEMENT
// =============================================

function initRedoublementCheckbox() {
    const estRedoublant = document.getElementById('est_redoublant');
    const classeSelect = document.getElementById('classe_id');
    const infoDiv = document.getElementById('promotionInfo');
    const infoText = document.getElementById('promotionInfoText');

    if (!estRedoublant || !classeSelect) return;

    estRedoublant.addEventListener('change', function() {
        const isRedoublant = this.checked;

        if (isRedoublant) {
            // Mode redoublement : sélectionner la classe actuelle
            const options = classeSelect.options;
            
            // Récupérer le nom de la classe actuelle depuis le champ "Classe actuelle"
            const classeActuelleInput = document.getElementById('classe_actuelle_input');
            let classeActuelleNom = '';
            if (classeActuelleInput) {
                classeActuelleNom = classeActuelleInput.value || 'cette classe';
            }
            
            // Si toujours pas trouvé, utiliser window.currentNiveau
            if (!classeActuelleNom && window.currentNiveau) {
                classeActuelleNom = window.currentNiveau;
            }
            
            // Sélectionner la classe actuelle dans la liste
            let found = false;
            for (let i = 0; i < options.length; i++) {
                const optionText = options[i].text;
                if (classeActuelleNom && optionText.includes(classeActuelleNom)) {
                    options[i].selected = true;
                    found = true;
                    break;
                }
            }
            
            // Si pas trouvée, prendre la première option avec le même niveau
            if (!found && window.currentNiveau) {
                for (let i = 0; i < options.length; i++) {
                    const optionNiveau = options[i].getAttribute('data-niveau');
                    if (optionNiveau === window.currentNiveau) {
                        options[i].selected = true;
                        found = true;
                        break;
                    }
                }
            }

            classeSelect.disabled = true;

            // Afficher l'info
            if (infoDiv && infoText) {
                infoDiv.style.display = 'block';
                infoText.innerHTML = `<strong>Mode redoublement activé :</strong> L'élève restera en <strong>${classeActuelleNom}</strong>.`;
                infoDiv.style.background = 'var(--warning-bg, #fff3e0)';
                infoDiv.style.borderLeft = '3px solid #f59e0b';
                infoDiv.style.color = 'var(--warning-text, #78350f)';
            }
        } else {
            // Mode normal : proposer la classe suivante
            classeSelect.disabled = false;

            // Sélectionner automatiquement la première classe du prochain niveau
            if (window.prochainNiveau) {
                const options = classeSelect.options;
                let found = false;
                for (let i = 0; i < options.length; i++) {
                    const optionNiveau = options[i].getAttribute('data-niveau');
                    if (optionNiveau === window.prochainNiveau) {
                        options[i].selected = true;
                        found = true;
                        break;
                    }
                }
            }

            if (infoDiv && infoText) {
                infoDiv.style.display = 'block';
                const prochainNiveauDisplay = window.prochainNiveau || 'suivant';
                infoText.innerHTML = `<strong>Progression normale :</strong> L'élève passera au niveau <strong>${prochainNiveauDisplay}</strong>.`;
                infoDiv.style.background = 'var(--success-bg, #e8f5e9)';
                infoDiv.style.borderLeft = '3px solid #4caf50';
                infoDiv.style.color = 'var(--success-text, #1f2937)';
            }
        }

        // Mettre à jour le champ caché
        const estRedoublantHidden = document.getElementById('est_redoublant_hidden');
        if (estRedoublantHidden) {
            estRedoublantHidden.value = isRedoublant ? '1' : '0';
        }
    });
}

// =============================================
// AUTO-SÉLECTION DE LA CLASSE
// =============================================

function autoSelectClass() {
    const classeSelect = document.getElementById('classe_id');
    if (!classeSelect) return;

    if (window.prochainNiveau && window.prochainNiveau !== '') {
        const options = classeSelect.options;
        for (let i = 0; i < options.length; i++) {
            const optionNiveau = options[i].getAttribute('data-niveau');
            if (optionNiveau === window.prochainNiveau) {
                options[i].selected = true;
                break;
            }
        }
    }
}

// =============================================
// GESTION DE LA SÉLECTION DE CLASSE
// =============================================

function initClassSelection() {
    const classeSelect = document.getElementById('classe_id');
    if (!classeSelect) return;

    classeSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const niveau = selectedOption.getAttribute('data-niveau');
        
        if (niveau === '4ème') {
            const estRedoublant = document.getElementById('est_redoublant');
            if (estRedoublant && !estRedoublant.checked) {
                Swal.fire({
                    title: '⚠️ Attention',
                    text: 'L\'élève passe en 4ème (Terminale). Après cette année, il ne pourra plus progresser.',
                    icon: 'warning',
                    confirmButtonColor: '#f59e0b',
                    confirmButtonText: 'Je comprends'
                });
            }
        }
        
        // Mettre à jour le texte d'aide
        const helpText = document.getElementById('classe_help');
        if (helpText && selectedOption.text) {
            helpText.textContent = `✅ Classe sélectionnée : ${selectedOption.text}`;
        }
    });
}

// =============================================
// GESTION DES ÉTAPES DU WIZARD
// =============================================

function initWizardSteps() {
    const eleveFound = document.querySelector('.student-card');
    if (eleveFound) {
        const steps = document.querySelectorAll('.step');
        const formSteps = document.querySelectorAll('.form-step');
        
        steps.forEach(step => {
            const stepNum = parseInt(step.dataset.step);
            if (stepNum === 1) {
                step.classList.add('completed');
            } else if (stepNum === 2) {
                step.classList.add('active');
            }
        });
        
        formSteps.forEach(step => {
            const stepNum = parseInt(step.dataset.step);
            if (stepNum === 1) {
                step.classList.remove('active');
            } else if (stepNum === 2) {
                step.classList.add('active');
            }
        });
    }
}

// =============================================
// SOUMISSION DU FORMULAIRE - CORRIGÉE
// =============================================

function initFormSubmit() {
    const form = document.getElementById('reinscriptionForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        const classeSelect = document.getElementById('classe_id');
        const estRedoublant = document.getElementById('est_redoublant');
        const niveauSelect = document.getElementById('niveau_select');

        if (!classeSelect.value) {
            e.preventDefault();
            showMessage('Veuillez sélectionner une classe pour la réinscription.', 'error');
            return false;
        }

        const selectedOption = classeSelect.options[classeSelect.selectedIndex];
        const niveau = selectedOption.getAttribute('data-niveau');
        
        // =============================================
        // CORRECTION : Utiliser prochainNiveau au lieu de window.prochainNiveau
        // =============================================
        const prochainNiveau = document.getElementById('prochain_niveau_input')?.value || window.prochainNiveau;
        
        console.log('Niveau sélectionné:', niveau);
        console.log('Prochain niveau attendu:', prochainNiveau);
        
        // Vérification supplémentaire : le niveau doit correspondre
        if (niveau !== prochainNiveau && !estRedoublant.checked) {
            e.preventDefault();
            showMessage(`⚠️ La classe sélectionnée (${selectedOption.text}) n'est pas au niveau attendu (${prochainNiveau || 'non défini'}).`, 'warning');
            return false;
        }
        
        if (niveau === '4ème' && !estRedoublant.checked) {
            e.preventDefault();
            Swal.fire({
                title: '⚠️ Attention',
                text: 'L\'élève passe en 4ème (Terminale).\n\nAprès cette année, il ne pourra plus progresser.\n\nSouhaitez-vous continuer ?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#f59e0b',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Oui, continuer',
                cancelButtonText: 'Annuler'
            }).then((result) => {
                if (result.isConfirmed) {
                    form.submit();
                }
            });
            return false;
        }

        if (estRedoublant.checked) {
            e.preventDefault();
            Swal.fire({
                title: '⚠️ Confirmation de redoublement',
                text: 'L\'élève restera dans la même classe.\n\nSouhaitez-vous continuer ?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#f59e0b',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Oui, confirmer',
                cancelButtonText: 'Annuler'
            }).then((result) => {
                if (result.isConfirmed) {
                    form.submit();
                }
            });
            return false;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Traitement en cours...';
        }
        return true;
    });
}

// =============================================
// FONCTION UTILITAIRE POUR ÉCHAPPER LE HTML
// =============================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}