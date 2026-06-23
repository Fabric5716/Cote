/**
 * SAISIR COTES - Version corrigée (plus de NaN)
 */
(function() {
    'use strict';

    const classeSelect = document.getElementById('classeSelect');
    const coursSelect = document.getElementById('coursSelect');
    const chargerBtn = document.getElementById('chargerBtn');
    const reloadBtn = document.getElementById('reloadClassesBtn');
    const saveAllBtn = document.getElementById('saveAllBtn');
    const cotesContainer = document.getElementById('cotesContainer');
    const tableWrapper = document.getElementById('tableWrapper');
    const anneeActiveId = document.getElementById('annee_active_id').value;

    let pointsParPeriode = 40;
    let currentClasseId = null;
    let currentCoursId = null;

    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    if (!csrfToken) {
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        if (cookie) csrfToken = cookie.split('=')[1];
    }

    // --- Chargement des classes ---
    async function chargerClasses() {
        if (!anneeActiveId) {
            classeSelect.innerHTML = '<option value="">-- Année non active --</option>';
            return;
        }
        classeSelect.disabled = true;
        classeSelect.innerHTML = '<option value="">-- Chargement... --</option>';
        try {
            const resp = await fetch(`/api/enseignant/classes/?annee_id=${anneeActiveId}`);
            const data = await resp.json();
            if (!data.classes || data.classes.length === 0) {
                classeSelect.innerHTML = '<option value="">-- Aucune classe --</option>';
                return;
            }
            classeSelect.innerHTML = '<option value="">-- Sélectionnez une classe --</option>';
            data.classes.forEach(cl => {
                const opt = document.createElement('option');
                opt.value = cl.id;
                opt.textContent = cl.nom_classe;
                classeSelect.appendChild(opt);
            });
            classeSelect.disabled = false;
        } catch (err) {
            console.error(err);
            classeSelect.innerHTML = '<option value="">-- Erreur --</option>';
        }
    }

    // --- Chargement des cours ---
    async function chargerCours(classeId) {
        if (!classeId) {
            coursSelect.disabled = true;
            coursSelect.innerHTML = '<option value="">-- Sélectionnez une classe --</option>';
            chargerBtn.disabled = true;
            return;
        }
        coursSelect.disabled = true;
        coursSelect.innerHTML = '<option value="">-- Chargement... --</option>';
        chargerBtn.disabled = true;
        try {
            const resp = await fetch(`/api/enseignant/cours/?annee_id=${anneeActiveId}&classe_id=${classeId}`);
            const data = await resp.json();
            if (!data.cours || data.cours.length === 0) {
                coursSelect.innerHTML = '<option value="">-- Aucun cours --</option>';
                return;
            }
            coursSelect.innerHTML = '<option value="">-- Sélectionnez un cours --</option>';
            data.cours.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = `${c.nom_cours} (coeff ${c.coefficient}, ${c.points_par_periode} pts/période)`;
                opt.dataset.points = c.points_par_periode;
                coursSelect.appendChild(opt);
            });
            coursSelect.disabled = false;
        } catch (err) {
            console.error(err);
            coursSelect.innerHTML = '<option value="">-- Erreur --</option>';
        }
    }

    // --- Chargement des élèves ---
    async function chargerElevesCotes() {
        const classeId = classeSelect.value;
        const coursId = coursSelect.value;
        if (!classeId || !coursId) {
            showToast('Sélectionnez une classe et un cours', 'error');
            return;
        }
        currentClasseId = classeId;
        currentCoursId = coursId;
        const selected = coursSelect.options[coursSelect.selectedIndex];
        pointsParPeriode = parseInt(selected.dataset.points) || 40;

        showLoadingTable();
        try {
            const resp = await fetch(`/api/enseignant/eleves-cotes/?annee_id=${anneeActiveId}&classe_id=${classeId}&cours_id=${coursId}`);
            const data = await resp.json();
            if (!data.eleves || data.eleves.length === 0) {
                tableWrapper.innerHTML = '<div class="alert alert-info">Aucun élève.</div>';
                cotesContainer.style.display = 'block';
                return;
            }
            genererTableauCotes(data.eleves, pointsParPeriode);
            cotesContainer.style.display = 'block';
        } catch (err) {
            console.error(err);
            tableWrapper.innerHTML = '<div class="alert alert-danger">Erreur chargement</div>';
            cotesContainer.style.display = 'block';
        }
    }

    // --- Génération du tableau (corrigée) ---
    function genererTableauCotes(eleves, points) {
        const maxPeriode = points;
        const maxExamen = points * 2;
        let html = `<div class="table-responsive">
            <table class="data-table" id="cotesTable">
                <thead><tr>
                    <th>Élève</th><th>P1 (/${maxPeriode})</th><th>P2 (/${maxPeriode})</th>
                    <th>Examen S1 (/${maxExamen})</th><th>Total S1</th>
                    <th>P3 (/${maxPeriode})</th><th>P4 (/${maxPeriode})</th>
                    <th>Examen S2 (/${maxExamen})</th><th>Total S2</th>
                    <th>Total général</th><th>%</th>
                </tr></thead><tbody>`;

        for (const eleve of eleves) {
            const c = eleve.cote || {};
            const p1 = (c.p1 !== undefined && c.p1 !== null) ? c.p1 : '';
            const p2 = (c.p2 !== undefined && c.p2 !== null) ? c.p2 : '';
            const ex1 = (c.ex1 !== undefined && c.ex1 !== null) ? c.ex1 : '';
            const p3 = (c.p3 !== undefined && c.p3 !== null) ? c.p3 : '';
            const p4 = (c.p4 !== undefined && c.p4 !== null) ? c.p4 : '';
            const ex2 = (c.ex2 !== undefined && c.ex2 !== null) ? c.ex2 : '';

            // Calcul des totaux initiaux (pour l'affichage, pas pour les inputs)
            const num = (v) => (v !== '' && !isNaN(parseFloat(v))) ? parseFloat(v) : 0;
            const totalS1 = (p1 !== '' && p2 !== '' && ex1 !== '') ? (num(p1)+num(p2)+num(ex1)) : (c.total_s1 !== undefined ? c.total_s1 : '—');
            const totalS2 = (p3 !== '' && p4 !== '' && ex2 !== '') ? (num(p3)+num(p4)+num(ex2)) : (c.total_s2 !== undefined ? c.total_s2 : '—');
            const totalGeneral = (totalS1 !== '—' && totalS2 !== '—') ? (totalS1 + totalS2) : (c.total_general !== undefined ? c.total_general : '—');
            const pourcentage = c.pourcentage !== undefined ? c.pourcentage : (totalGeneral !== '—' ? ((totalGeneral / (points * 8) * 100).toFixed(1) + '%') : '—');

            html += `<tr data-eleve-id="${eleve.id}">
                <td><strong>${eleve.nom} ${eleve.prenom}</strong><br><small>${eleve.matricule}</small></td>
                <td><input type="number" class="cote-input" data-field="p1" value="${p1}" step="any" min="0" max="${maxPeriode}"></td>
                <td><input type="number" class="cote-input" data-field="p2" value="${p2}" step="any" min="0" max="${maxPeriode}"></td>
                <td><input type="number" class="cote-input" data-field="ex1" value="${ex1}" step="any" min="0" max="${maxExamen}"></td>
                <td class="total-cell" data-total="s1">${totalS1 !== '—' ? totalS1 : '—'}</td>
                <td><input type="number" class="cote-input" data-field="p3" value="${p3}" step="any" min="0" max="${maxPeriode}"></td>
                <td><input type="number" class="cote-input" data-field="p4" value="${p4}" step="any" min="0" max="${maxPeriode}"></td>
                <td><input type="number" class="cote-input" data-field="ex2" value="${ex2}" step="any" min="0" max="${maxExamen}"></td>
                <td class="total-cell" data-total="s2">${totalS2 !== '—' ? totalS2 : '—'}</td>
                <td class="total-cell" data-total="general">${totalGeneral !== '—' ? totalGeneral : '—'}</td>
                <td class="total-cell" data-pourcentage>${pourcentage}</td>
            </tr>`;
        }
        html += `</tbody></table></div>`;
        tableWrapper.innerHTML = html;

        // Attacher les événements pour recalcul à chaque saisie
        document.querySelectorAll('.cote-input').forEach(input => {
            input.addEventListener('input', function() {
                recalcTotalsForRow(this.closest('tr'));
            });
        });
    }

    // Recalcul corrigé (plus de NaN)
    function recalcTotalsForRow(row) {
        const getVal = (selector) => {
            const inp = row.querySelector(selector);
            if (!inp) return 0;
            let v = parseFloat(inp.value);
            return isNaN(v) ? 0 : v;
        };
        const p1 = getVal('[data-field="p1"]');
        const p2 = getVal('[data-field="p2"]');
        const ex1 = getVal('[data-field="ex1"]');
        const p3 = getVal('[data-field="p3"]');
        const p4 = getVal('[data-field="p4"]');
        const ex2 = getVal('[data-field="ex2"]');

        const totalS1 = p1 + p2 + ex1;
        const totalS2 = p3 + p4 + ex2;
        const totalGeneral = totalS1 + totalS2;
        const maxTotal = pointsParPeriode * 8;
        const pourcentage = maxTotal > 0 ? (totalGeneral / maxTotal * 100).toFixed(1) : 0;

        row.querySelector('[data-total="s1"]').textContent = totalS1;
        row.querySelector('[data-total="s2"]').textContent = totalS2;
        row.querySelector('[data-total="general"]').textContent = totalGeneral;
        row.querySelector('[data-pourcentage]').textContent = pourcentage + '%';
    }

    async function sauvegarderToutesCotes() {
        if (!currentClasseId || !currentCoursId) {
            showToast('Aucune sélection', 'error');
            return;
        }
        const rows = document.querySelectorAll('#cotesTable tbody tr');
        const cotes = {};
        for (const row of rows) {
            const eleveId = row.dataset.eleveId;
            cotes[eleveId] = {
                p1: row.querySelector('[data-field="p1"]')?.value || null,
                p2: row.querySelector('[data-field="p2"]')?.value || null,
                ex1: row.querySelector('[data-field="ex1"]')?.value || null,
                p3: row.querySelector('[data-field="p3"]')?.value || null,
                p4: row.querySelector('[data-field="p4"]')?.value || null,
                ex2: row.querySelector('[data-field="ex2"]')?.value || null
            };
        }
        const overlay = document.getElementById('savingOverlay');
        overlay.style.display = 'flex';
        try {
            const resp = await fetch('/api/enseignant/sauvegarder-cotes/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({
                    annee_id: anneeActiveId,
                    classe_id: currentClasseId,
                    cours_id: currentCoursId,
                    cotes: cotes
                })
            });
            const result = await resp.json();
            if (result.success) showToast('Enregistré', 'success');
            else showToast(result.error || 'Erreur', 'error');
        } catch (err) {
            showToast('Erreur réseau', 'error');
        } finally {
            overlay.style.display = 'none';
        }
    }

    function showToast(msg, type = 'success') {
        const existing = document.querySelectorAll('.toast-notification');
        existing.forEach(t => t.remove());
        const toast = document.createElement('div');
        toast.className = `toast-notification ${type}`;
        toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i><span>${msg}</span>`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    function showLoadingTable() {
        tableWrapper.innerHTML = '<div class="text-center p-5"><i class="fas fa-spinner fa-spin fa-2x"></i><p>Chargement...</p></div>';
        cotesContainer.style.display = 'block';
    }

    // Initialisation
    function init() {
        chargerClasses();
        classeSelect.addEventListener('change', () => {
            const val = classeSelect.value;
            if (val) chargerCours(val);
            else {
                coursSelect.disabled = true;
                coursSelect.innerHTML = '<option value="">-- Sélectionnez une classe --</option>';
                chargerBtn.disabled = true;
                cotesContainer.style.display = 'none';
            }
        });
        coursSelect.addEventListener('change', () => {
            chargerBtn.disabled = !coursSelect.value;
        });
        chargerBtn.addEventListener('click', chargerElevesCotes);
        reloadBtn.addEventListener('click', () => {
            chargerClasses();
            coursSelect.disabled = true;
            coursSelect.innerHTML = '<option value="">-- Sélectionnez une classe --</option>';
            chargerBtn.disabled = true;
            cotesContainer.style.display = 'none';
        });
        saveAllBtn.addEventListener('click', sauvegarderToutesCotes);
    }
    init();
})();