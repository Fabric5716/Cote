// static/js/admin/modifier_eleve.js

let currentStep = 1;
const totalSteps = 4;

document.addEventListener('DOMContentLoaded', function() {
    initParentSelector();
    initWizard();
    initFormSubmit();
    updateConfirmation(); // pré-remplit la confirmation avec les valeurs actuelles
});

// Gestion du choix parent existant / nouveau
function initParentSelector() {
    const parentChoice = document.getElementById('parent_choice');
    const newParentFields = document.getElementById('new_parent_fields');
    const nomParent = document.getElementById('nom_parent');
    const prenomParent = document.getElementById('prenom_parent');
    const telParent = document.getElementById('telephone_parent');
    const emailParent = document.getElementById('email_parent');
    const professionParent = document.getElementById('profession_parent');
    const adresseParent = document.getElementById('adresse_parent');
    const parentIdHidden = document.getElementById('parent_id');

    function updateParentFields() {
        const selected = parentChoice.value;
        if (selected === 'new') {
            newParentFields.style.display = 'block';
            nomParent.required = true;
            telParent.required = true;
            parentIdHidden.value = '';
        } else {
            newParentFields.style.display = 'none';
            nomParent.required = false;
            telParent.required = false;
            parentIdHidden.value = selected;
            const option = parentChoice.options[parentChoice.selectedIndex];
            nomParent.value = option.dataset.nom || '';
            prenomParent.value = option.dataset.prenom || '';
            telParent.value = option.dataset.tel || '';
            emailParent.value = option.dataset.email || '';
            adresseParent.value = option.dataset.adresse || '';
            professionParent.value = '';
        }
    }
    parentChoice.addEventListener('change', updateParentFields);
    updateParentFields();
}

// Navigation du wizard
function initWizard() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    function showStep(step) {
        document.querySelectorAll('.form-step').forEach(stepDiv => {
            stepDiv.classList.remove('active');
            if (parseInt(stepDiv.dataset.step) === step) stepDiv.classList.add('active');
        });
        document.querySelectorAll('.step').forEach(stepDiv => {
            stepDiv.classList.remove('active');
            if (parseInt(stepDiv.dataset.step) === step) stepDiv.classList.add('active');
        });
        prevBtn.style.display = step === 1 ? 'none' : 'block';
        nextBtn.textContent = step === totalSteps ? 'Confirmer' : 'Suivant';
        if (step === totalSteps) updateConfirmation();
    }

    function next() {
        if (validateStep(currentStep)) {
            if (currentStep < totalSteps) {
                currentStep++;
                showStep(currentStep);
            } else {
                document.getElementById('modifierEleveForm').dispatchEvent(new Event('submit'));
            }
        }
    }

    function prev() {
        if (currentStep > 1) {
            currentStep--;
            showStep(currentStep);
        }
    }

    prevBtn.addEventListener('click', prev);
    nextBtn.addEventListener('click', next);
    showStep(1);
}

// Validation par étape
function validateStep(step) {
    if (step === 1) {
        const nom = document.getElementById('nom').value.trim();
        const prenom = document.getElementById('prenom').value.trim();
        const sexe = document.getElementById('sexe').value;
        if (!nom || !prenom || !sexe) {
            Swal.fire('Erreur', 'Veuillez remplir le nom, prénom et sexe', 'error');
            return false;
        }
        return true;
    }
    if (step === 2) {
        const parentChoice = document.getElementById('parent_choice').value;
        if (parentChoice === 'new') {
            const nomParent = document.getElementById('nom_parent').value.trim();
            const telParent = document.getElementById('telephone_parent').value.trim();
            if (!nomParent || !telParent) {
                Swal.fire('Erreur', 'Veuillez saisir le nom et le téléphone du parent', 'error');
                return false;
            }
        } else if (!parentChoice) {
            Swal.fire('Erreur', 'Veuillez choisir un parent existant ou en ajouter un nouveau', 'error');
            return false;
        }
        return true;
    }
    if (step === 3) {
        const classeSelect = document.getElementById('classe_id');
        const classeValue = classeSelect ? classeSelect.value : '';
        const typeInsSelect = document.getElementById('type_inscription');
        const typeInsValue = typeInsSelect ? typeInsSelect.value : '';

        if (classeSelect && classeSelect.options.length <= 1) {
            Swal.fire('Erreur', 'Aucune classe disponible. Veuillez d\'abord créer des classes.', 'error');
            return false;
        }
        if (!classeValue) {
            Swal.fire('Erreur', 'Veuillez sélectionner une classe valide.', 'error');
            return false;
        }
        if (!typeInsValue) {
            Swal.fire('Erreur', 'Veuillez sélectionner un type d’inscription', 'error');
            return false;
        }
        return true;
    }
    return true;
}

// Mise à jour de l'affichage de confirmation
function updateConfirmation() {
    // Élève
    const nom = document.getElementById('nom').value;
    const postnom = document.getElementById('postnom').value;
    const prenom = document.getElementById('prenom').value;
    const sexe = document.getElementById('sexe').value === 'M' ? 'Masculin' : 'Féminin';
    const dateNaiss = document.getElementById('date_naissance').value || 'Non renseignée';
    const lieuNaiss = document.getElementById('lieu_naissance').value || 'Non renseigné';
    const adresse = document.getElementById('adresse').value || 'Non renseignée';
    document.getElementById('confirm_eleve').innerHTML = `
        <p><strong>Nom :</strong> ${nom} ${postnom ? postnom : ''} ${prenom}</p>
        <p><strong>Sexe :</strong> ${sexe}</p>
        <p><strong>Date naissance :</strong> ${dateNaiss}</p>
        <p><strong>Lieu naissance :</strong> ${lieuNaiss}</p>
        <p><strong>Adresse :</strong> ${adresse}</p>
    `;

    // Parent
    const parentChoice = document.getElementById('parent_choice');
    let parentHtml = '';
    if (parentChoice.value === 'new') {
        const nomP = document.getElementById('nom_parent').value;
        const prenomP = document.getElementById('prenom_parent').value;
        const telP = document.getElementById('telephone_parent').value;
        const emailP = document.getElementById('email_parent').value;
        const professionP = document.getElementById('profession_parent').value;
        const adresseP = document.getElementById('adresse_parent').value;
        parentHtml = `
            <p><strong>Nom :</strong> ${nomP} ${prenomP}</p>
            <p><strong>Téléphone :</strong> ${telP}</p>
            <p><strong>Email :</strong> ${emailP || 'Non renseigné'}</p>
            <p><strong>Profession :</strong> ${professionP || 'Non renseignée'}</p>
            <p><strong>Adresse :</strong> ${adresseP || 'Non renseignée'}</p>
        `;
    } else {
        const opt = parentChoice.options[parentChoice.selectedIndex];
        parentHtml = `
            <p><strong>Parent :</strong> ${opt.dataset.nom} ${opt.dataset.prenom}</p>
            <p><strong>Téléphone :</strong> ${opt.dataset.tel}</p>
            <p><strong>Email :</strong> ${opt.dataset.email || 'Non renseigné'}</p>
        `;
    }
    document.getElementById('confirm_parent').innerHTML = parentHtml;

    // Scolarité
    const classeSelect = document.getElementById('classe_id');
    const classeNom = classeSelect.options[classeSelect.selectedIndex]?.text || '';
    const typeIns = document.getElementById('type_inscription').value === 'NOUVEAU' ? 'Nouvel élève' : 'Réinscription';
    const ecole = document.getElementById('ecole_provenance').value || 'Non renseignée';
    const dateIns = document.getElementById('date_inscription').value;
    const matricule = document.getElementById('matricule').value;
    document.getElementById('confirm_scolaire').innerHTML = `
        <p><strong>Classe :</strong> ${classeNom}</p>
        <p><strong>Type inscription :</strong> ${typeIns}</p>
        <p><strong>École provenance :</strong> ${ecole}</p>
        <p><strong>Date inscription :</strong> ${dateIns}</p>
        <p><strong>Matricule :</strong> ${matricule}</p>
    `;
}

// Soumission du formulaire (AJAX)
function initFormSubmit() {
    const form = document.getElementById('modifierEleveForm');
    form.addEventListener('submit', function(e) {
        e.preventDefault();

        const formData = new FormData(form);
        const parentChoice = document.getElementById('parent_choice').value;

        if (parentChoice !== 'new') {
            formData.delete('nom_parent');
            formData.delete('prenom_parent');
            formData.delete('telephone_parent');
            formData.delete('email_parent');
            formData.delete('profession_parent');
            formData.delete('adresse_parent');
            formData.append('parent_id', parentChoice);
        } else {
            formData.delete('parent_id');
        }

        const submitBtn = form.querySelector('.btn-submit-final');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enregistrement...';
        }

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire('Succès', data.message, 'success').then(() => {
                    // Redirection vers la page de détail
                    const eleveId = document.querySelector('input[name="eleve_id"]').value;
                    window.location.href = `/gestion/eleves/detail/${eleveId}/`;
                });
            } else {
                Swal.fire('Erreur', data.error, 'error');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Enregistrer les modifications';
                }
            }
        })
        .catch(error => {
            console.error(error);
            Swal.fire('Erreur', 'Erreur de connexion au serveur', 'error');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Enregistrer les modifications';
            }
        });
    });
}