// static/js/admin/detail_eleve.js
console.log("Fiche élève – animations activées");

document.addEventListener('DOMContentLoaded', function() {
    // Animation d'entrée de la carte principale
    const profileCard = document.querySelector('.student-profile-card');
    if (profileCard) {
        profileCard.style.opacity = '0';
        profileCard.style.transform = 'translateY(20px)';
        setTimeout(() => {
            profileCard.style.transition = 'all 0.5s cubic-bezier(0.2, 0.9, 0.4, 1.1)';
            profileCard.style.opacity = '1';
            profileCard.style.transform = 'translateY(0)';
        }, 100);
    }

    // Effet de survol sur la photo
    const studentPhoto = document.querySelector('.student-photo');
    if (studentPhoto) {
        studentPhoto.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.02)';
            this.style.transition = 'transform 0.25s ease';
            this.style.boxShadow = '0 12px 24px rgba(0,0,0,0.15)';
        });
        studentPhoto.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = '0 8px 20px rgba(0,0,0,0.1)';
        });
    }

    // Mise en évidence des sections au survol
    const sections = document.querySelectorAll('.info-section');
    sections.forEach(section => {
        section.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#fcfdff';
            this.style.transition = 'background 0.2s';
            this.style.borderRadius = '16px';
            this.style.padding = '0 8px';
            this.style.margin = '0 -8px';
        });
        section.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
            this.style.padding = '';
            this.style.margin = '';
        });
    });

    // Animation des badges
    const badges = document.querySelectorAll('.active-badge, .cycle-badge');
    badges.forEach(badge => {
        badge.addEventListener('mouseenter', () => badge.style.opacity = '0.9');
        badge.addEventListener('mouseleave', () => badge.style.opacity = '1');
    });
});