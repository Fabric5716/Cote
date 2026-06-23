/**
 * MAIN.JS - ADMIN PREMIUM ÉDITION
 * Gestion du thème, sidebar, dropdowns, date/time, animations (identique au modèle PHP)
 */
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        initSidebarPremium();
        initThemePremium();
        initDropdownsPremium();
        initDateTimePremium();
        initMicroInteractions();
    });

    function initSidebarPremium() {
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');
        const toggleBtn = document.querySelector('.sidebar-toggle');
        const hamburger = document.querySelector('.hamburger');

        if (!sidebar || !mainContent) return;

        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true' && window.innerWidth > 992) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        }

        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('expanded');
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
                triggerRipple(e, toggleBtn);
            });
        }

        if (hamburger) {
            hamburger.addEventListener('click', () => {
                sidebar.classList.toggle('active');
            });
        }

        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 992) sidebar.classList.remove('active');
            });
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth > 992) sidebar.classList.remove('active');
        });
    }

    function initThemePremium() {
        const themeToggle = document.getElementById('themeToggle');
        if (!themeToggle) return;

        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeIcon(themeToggle, savedTheme);

        themeToggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const newTheme = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(themeToggle, newTheme);
            document.body.style.transition = 'background 0.3s, color 0.3s';
            setTimeout(() => document.body.style.transition = '', 300);
        });
    }

    function updateThemeIcon(btn, theme) {
        const icon = btn.querySelector('i');
        if (icon) {
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    function initDropdownsPremium() {
        const triggers = document.querySelectorAll('.dropdown-trigger');
        triggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                const menu = trigger.closest('.user-dropdown')?.querySelector('.dropdown-menu');
                if (!menu) return;
                document.querySelectorAll('.dropdown-menu.show').forEach(m => {
                    if (m !== menu) m.classList.remove('show');
                });
                menu.classList.toggle('show');
            });
        });
        document.addEventListener('click', () => {
            document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
        });
    }

    function initDateTimePremium() {
        const dateTimeEl = document.getElementById('currentDateTime');
        if (!dateTimeEl) return;
        const update = () => {
            const now = new Date();
            const options = { weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' };
            let str = now.toLocaleDateString('fr-FR', options);
            str = str.charAt(0).toUpperCase() + str.slice(1);
            dateTimeEl.textContent = str;
        };
        update();
        setInterval(update, 60000);
    }

    function initMicroInteractions() {
        const clickables = document.querySelectorAll('.btn, .nav-link, .dropdown-trigger, .sidebar-toggle, .theme-toggle, .logout-btn');
        clickables.forEach(el => {
            el.addEventListener('click', (e) => triggerRipple(e, el));
        });

        const cards = document.querySelectorAll('.card, .stat-card, .cours-header');
        if (cards.length) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });
            cards.forEach(card => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'all 0.5s ease';
                observer.observe(card);
            });
        }
    }

    function triggerRipple(event, element) {
        const rect = element.getBoundingClientRect();
        const ripple = document.createElement('span');
        ripple.className = 'ripple-effect';
        ripple.style.left = `${event.clientX - rect.left}px`;
        ripple.style.top = `${event.clientY - rect.top}px`;
        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    }
})();