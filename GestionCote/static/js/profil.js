// profil.js - Validation, aperçu photo, auto-disparition, détection de modification
document.addEventListener('DOMContentLoaded', function() {
    // Gestion de l'upload de la photo (clic sur l'avatar)
    const avatar = document.querySelector('.profile-avatar-lg');
    const fileInput = document.getElementById('profile_photo_input');
    const photoForm = document.getElementById('photoUploadForm');

    if (avatar && fileInput && photoForm) {
        avatar.style.cursor = 'pointer';
        avatar.addEventListener('click', function() {
            fileInput.click();
        });
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                photoForm.submit();
            }
        });
    }

    // Auto-disparition des alertes après 5 secondes
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => {
                if (alert.parentNode) alert.remove();
            }, 500);
        }, 5000);
    });

    // Validation téléphone (uniquement chiffres)
    const phoneInput = document.querySelector('input[name="telephone"]');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 12) value = value.slice(0, 12);
            e.target.value = value;
        });
    }

    // Validation email sur le champ du formulaire de modification
    const emailInput = document.querySelector('input[name="email"]');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            const email = this.value.trim();
            const emailPattern = /^[^\s@]+@([^\s@]+\.)+[^\s@]+$/;
            if (email && !emailPattern.test(email)) {
                showFieldError(this, 'Adresse email invalide');
            } else {
                clearFieldError(this);
            }
        });
    }

    // Détecter les modifications sur le formulaire de coordonnées
    const coordForm = document.querySelector('#edit-coords form');
    if (coordForm) {
        const phone = coordForm.querySelector('input[name="telephone"]');
        const email = coordForm.querySelector('input[name="email"]');
        const adresse = coordForm.querySelector('textarea[name="adresse"]');
        let initialValues = {
            telephone: phone ? phone.value : '',
            email: email ? email.value : '',
            adresse: adresse ? adresse.value : ''
        };

        coordForm.addEventListener('submit', function(e) {
            let hasError = false;
            const emailVal = email ? email.value.trim() : '';
            if (emailVal && !/^[^\s@]+@([^\s@]+\.)+[^\s@]+$/.test(emailVal)) {
                showFieldError(email, 'Email invalide');
                hasError = true;
            }
            if (hasError) {
                e.preventDefault();
                alert('Veuillez corriger les erreurs avant de soumettre.');
                return;
            }

            const currentPhone = phone ? phone.value : '';
            const currentEmail = email ? email.value : '';
            const currentAdresse = adresse ? adresse.value : '';
            const hasChanges = (currentPhone !== initialValues.telephone) ||
                               (currentEmail !== initialValues.email) ||
                               (currentAdresse !== initialValues.adresse);

            if (!hasChanges) {
                e.preventDefault();
                showTemporaryMessage('Aucune modification détectée. Veuillez modifier un champ avant d\'enregistrer.');
            }
        });
    }

    // Fonctions utilitaires
    function showFieldError(input, message) {
        clearFieldError(input);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.style.cssText = 'color: #ef4444; font-size: 0.75rem; margin-top: 0.25rem;';
        errorDiv.textContent = message;
        input.parentNode.appendChild(errorDiv);
        input.style.borderColor = '#ef4444';
    }

    function clearFieldError(input) {
        const parent = input.parentNode;
        const existingError = parent.querySelector('.field-error');
        if (existingError) existingError.remove();
        input.style.borderColor = '';
    }

    function showTemporaryMessage(message) {
        const existingMsg = document.querySelector('.temp-message');
        if (existingMsg) existingMsg.remove();

        const msgDiv = document.createElement('div');
        msgDiv.className = 'temp-message alert alert-warning';
        msgDiv.style.cssText = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; background: #fef3c7; color: #92400e; border-left-color: #f59e0b;';
        msgDiv.innerHTML = '<i class="fas fa-info-circle"></i><div class="alert-content">' + message + '</div>';
        document.body.appendChild(msgDiv);

        setTimeout(() => {
            msgDiv.style.transition = 'opacity 0.5s ease';
            msgDiv.style.opacity = '0';
            setTimeout(() => msgDiv.remove(), 500);
        }, 3000);
    }
});

function scrollToEditCoords() {
    document.getElementById('edit-coords').scrollIntoView({ behavior: 'smooth' });
}