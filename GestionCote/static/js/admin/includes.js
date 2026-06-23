// static/js/admin/includes.js

// ========== MODAL FUNCTIONS ==========
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
    }
}

// Fermer modal en cliquant à l'extérieur
window.onclick = function(event) {
    if (event.target.classList && event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// ========== MENU ACTIVE STATE ==========
function setActiveMenuItem() {
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.menu-item');
    
    menuItems.forEach(item => {
        const link = item.getAttribute('onclick');
        if (link && currentPath.includes(link.replace("openModal('", "").replace("')", ""))) {
            item.classList.add('active');
        } else if (currentPath === '/dashboard-de/' && item.querySelector('span')?.innerText === 'Tableau de bord') {
            item.classList.add('active');
        }
    });
}

// ========== COUNTER ANIMATION ==========
function animateCounter(element, target) {
    let current = 0;
    const increment = target / 50;
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 20);
}

// Démarrer les animations des compteurs
function initCounters() {
    document.querySelectorAll('.animate-counter').forEach(counter => {
        const target = parseInt(counter.dataset.target);
        if (!isNaN(target)) {
            animateCounter(counter, target);
        }
    });
}

// ========== NOTIFICATIONS ==========
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `fixed top-20 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    }`;
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ========== FORM SUBMISSIONS ==========
function submitForm(formId, url, modalId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            const data = await response.json();
            
            if (data.success) {
                showNotification(data.message || 'Opération réussie !', 'success');
                closeModal(modalId);
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification(data.error || 'Une erreur est survenue', 'error');
            }
        } catch (error) {
            showNotification('Erreur de connexion', 'error');
        }
    });
}

// ========== EXPORT FUNCTIONS ==========
function exportPDF() {
    window.location.href = '/admin/archives/export-pdf/';
    showNotification('Export PDF en cours...', 'success');
}

function exportExcel() {
    window.location.href = '/admin/archives/export-excel/';
    showNotification('Export Excel en cours...', 'success');
}

function genererPalmares() {
    if (confirm('Voulez-vous générer le palmarès de l\'année ?')) {
        fetch('/admin/palmares/generer/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Palmarès généré avec succès !', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification(data.error || 'Erreur lors de la génération', 'error');
            }
        });
    }
}

// ========== CHARTS INITIALIZATION ==========
function initCharts(chartData) {
    // Graphique des inscriptions
    const ctx1 = document.getElementById('inscriptionChart')?.getContext('2d');
    if (ctx1 && typeof Chart !== 'undefined') {
        new Chart(ctx1, {
            type: 'line',
            data: {
                labels: chartData?.years || ['2019', '2020', '2021', '2022', '2023', '2024'],
                datasets: [{
                    label: 'Nombre d\'inscriptions',
                    data: chartData?.inscriptions || [120, 150, 180, 220, 280, 350],
                    borderColor: '#1e3c72',
                    backgroundColor: 'rgba(30,60,114,0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
    
    // Graphique des filières
    const ctx2 = document.getElementById('filiereChart')?.getContext('2d');
    if (ctx2 && typeof Chart !== 'undefined') {
        new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: chartData?.filiereLabels || ['Pédagogie', 'Construction', 'Social', 'Commerciale'],
                datasets: [{
                    data: chartData?.filiereData || [40, 25, 20, 15],
                    backgroundColor: ['#1e3c72', '#2a5298', '#3b6cb0', '#4c86c8'],
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
}

// ========== LOADING DATA - CORRIGÉ ==========
async function loadDashboardData() {
    console.log('🔄 Chargement des données du tableau de bord...');
    
    try {
        // Récupérer le token CSRF
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                          document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
        
        // URL correcte pour les statistiques (avec le préfixe /api/)
        const url = '/api/stats/data/';
        console.log(`📡 Appel de l'API: ${url}`);
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin' // Important pour envoyer les cookies de session
        });
        
        console.log(`📡 Statut de la réponse: ${response.status}`);
        
        // Vérifier si la réponse est OK
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                console.warn('⚠️ Session expirée ou non authentifié');
                // Ne pas rediriger automatiquement, laisser l'utilisateur voir la page
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Vérifier le type de contenu
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // Si ce n'est pas du JSON, c'est probablement une erreur HTML
            const text = await response.text();
            console.error('❌ Réponse non JSON reçue:', text.substring(0, 200));
            throw new Error('La réponse du serveur n\'est pas du JSON. Vérifiez votre authentification.');
        }
        
        const data = await response.json();
        console.log('✅ Données chargées avec succès:', data);
        
        // Mettre à jour les compteurs
        document.querySelectorAll('.stat-value').forEach(el => {
            const key = el.id;
            if (data[key] !== undefined && data[key] !== null) {
                const value = parseInt(data[key]) || 0;
                el.dataset.target = value;
                animateCounter(el, value);
            }
        });
        
        return data;
        
    } catch (error) {
        console.error('❌ Erreur de chargement des données:', error);
        // Afficher un message discret dans la console
        console.log('💡 Vérifiez que vous êtes connecté et que l\'URL /api/stats/data/ est accessible.');
        return null;
    }
}

// ========== INITIALIZATION - CORRIGÉ ==========
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM chargé - Initialisation du dashboard');
    
    setActiveMenuItem();
    initCounters();
    
    // Charger les données avec un léger délai pour s'assurer que la session est bien établie
    setTimeout(async () => {
        const data = await loadDashboardData();
        if (data) {
            initCharts(data);
        } else {
            console.log('ℹ️ Les données du dashboard ne sont pas disponibles');
        }
    }, 500);
    
    // Initialiser les formulaires
    submitForm('enseignantForm', '/admin/enseignants/ajouter/', 'modalEnseignant');
    submitForm('eleveForm', '/admin/eleves/ajouter/', 'modalEleve');
    submitForm('anneeForm', '/admin/annee/definir/', 'modalAnnee');
});

// ========== TOGGLE PASSWORD ==========
function togglePassword(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    if (input && icon) {
        const type = input.type === 'password' ? 'text' : 'password';
        input.type = type;
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');
    }
}

// ========== FONCTION UTILITAIRE POUR LE TOKEN CSRF ==========
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
           document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || 
           document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
}

console.log('✅ includes.js chargé avec succès');