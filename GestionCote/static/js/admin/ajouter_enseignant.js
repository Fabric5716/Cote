// static/js/admin/ajouter_enseignant.js

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('enseignantForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // Récupération des champs
            const nom = document.getElementById('nom').value.trim();
            const prenom = document.getElementById('prenom').value.trim();
            const email = document.getElementById('email').value.trim();
            const specialite = document.getElementById('specialite').value.trim();
            const password = document.getElementById('password').value;
            const passwordConfirm = document.getElementById('password_confirm').value;

            // Validation
            if (!nom || !prenom || !email || !specialite || !password) {
                Swal.fire('Erreur', 'Veuillez remplir tous les champs obligatoires', 'error');
                return;
            }
            if (password !== passwordConfirm) {
                Swal.fire('Erreur', 'Les mots de passe ne correspondent pas', 'error');
                return;
            }
            if (password.length < 6) {
                Swal.fire('Erreur', 'Le mot de passe doit contenir au moins 6 caractères', 'error');
                return;
            }

            const submitBtn = form.querySelector('.btn-submit');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enregistrement...';

            const formData = new FormData(form);
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
                    Swal.fire('Succès', data.message, 'success');
                    form.reset();
                    setTimeout(() => {
                        window.location.href = '/dashboard-de/';
                    }, 1500);
                } else {
                    Swal.fire('Erreur', data.error, 'error');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-save"></i> Enregistrer l\'enseignant';
                }
            })
            .catch(error => {
                console.error(error);
                Swal.fire('Erreur', 'Erreur de connexion au serveur', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Enregistrer l\'enseignant';
            });
        });
    }
});