# Cote/views.py

import random
import string
import json
import re
import os
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Avg, Count, Q

from .models import (
    Utilisateur, Personne, Personnel, AnneeScolaire, Eleve, Classe, Cours,
    Inscription, Note, Palmares, OptionEtude, AttributionCours, TitulaireClasse,
    Periode, Semestre, Bulletin, Archivage, Cote
)
from .forms import CoteForm, SelectionForm


# =====================================================
# 1. VUES PUBLIQUES (index, login, logout, register_admin)
# =====================================================

def index(request):
    return render(request, 'index.html')


def login_view(request):
    admin_exists = Utilisateur.objects.filter(est_principal=True).exists()
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = Utilisateur.objects.get(email=email, est_actif=True)
            if user.check_password(password):
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['user_role'] = user.role
                request.session['user_nom'] = f"{user.id_personne.nom} {user.id_personne.prenom}"
                request.session['user_prenom'] = user.id_personne.prenom
                request.session['is_principal'] = user.est_principal
                user.dernier_connexion = timezone.now()
                user.save()
                messages.success(request, f'Bienvenue {user.id_personne.prenom} !')
                if user.role == 'DE' or user.est_principal:
                    return redirect('dashboard_de')
                elif user.role == 'ENSEIGNANT':
                    return redirect('dashboard_enseignant')
                elif user.role == 'TITULAIRE':
                    return redirect('dashboard_titulaire')
                else:
                    return redirect('dashboard')
            else:
                messages.error(request, 'Mot de passe incorrect')
        except Utilisateur.DoesNotExist:
            messages.error(request, 'Email non trouvé ou compte inactif')
    context = {'admin_exists': admin_exists, 'page_title': 'Connexion - CS KABA'}
    return render(request, 'Cote/login.html', context)


def logout_view(request):
    request.session.flush()
    messages.success(request, 'Vous avez été déconnecté avec succès')
    return redirect('index')


def register_admin(request):
    if Utilisateur.objects.filter(est_principal=True).exists():
        messages.warning(request, 'Un administrateur principal existe déjà')
        return redirect('login')
    if request.method == 'POST':
        nom = request.POST.get('nom')
        postnom = request.POST.get('postnom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        if password != password_confirm:
            messages.error(request, 'Les mots de passe ne correspondent pas')
            return redirect('register_admin')
        if len(password) < 6:
            messages.error(request, 'Le mot de passe doit contenir au moins 6 caractères')
            return redirect('register_admin')
        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé')
            return redirect('register_admin')
        try:
            personne = Personne.objects.create(
                nom=nom, postnom=postnom or '', prenom=prenom,
                email=email, telephone=telephone or ''
            )
            utilisateur = Utilisateur(
                id_personne=personne, email=email, role='DE',
                est_actif=True, est_principal=True
            )
            utilisateur.set_password(password)
            utilisateur.save()
            Personnel.objects.create(id_utilisateur=utilisateur, date_embauche=datetime.now().date(), est_titulaire=True)
            messages.success(request, 'Administrateur créé avec succès ! Veuillez vous connecter.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
    return render(request, 'Cote/register_admin.html', {'page_title': 'Création du Directeur des Études'})


# =====================================================
# 2. TABLEAUX DE BORD
# =====================================================

def dashboard(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return redirect('dashboard_de')


def dashboard_de(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')

    annee_active = AnneeScolaire.objects.filter(est_active=True).first()

    total_eleves = Inscription.objects.filter(id_annee=annee_active, est_active=True).count() if annee_active else 0
    total_enseignants = Personnel.objects.count()
    total_classes = Classe.objects.filter(inscription__id_annee=annee_active, inscription__est_active=True).distinct().count() if annee_active else 0

    top_eleves_data = []
    if annee_active:
        inscriptions = Inscription.objects.filter(id_annee=annee_active, est_active=True).select_related('id_eleve__id_personne', 'id_classe')
        eleves_avec_moyennes = []
        for inscription in inscriptions:
            eleve = inscription.id_eleve
            moyenne = Note.objects.filter(id_eleve=eleve, id_annee=annee_active).aggregate(Avg('note'))['note__avg']
            if moyenne:
                mention = 'Excellent' if moyenne >= 16 else 'Très Bien' if moyenne >= 14 else 'Bien' if moyenne >= 12 else 'Assez Bien' if moyenne >= 10 else 'Passable'
                eleves_avec_moyennes.append({
                    'matricule': eleve.matricule,
                    'nom': eleve.id_personne.nom,
                    'prenom': eleve.id_personne.prenom,
                    'classe': inscription.id_classe.nom_classe,
                    'moyenne': round(moyenne, 2),
                    'mention': mention
                })
        top_eleves_data = sorted(eleves_avec_moyennes, key=lambda x: x['moyenne'], reverse=True)[:10]

    taux_reussite = 0
    if annee_active:
        inscriptions = Inscription.objects.filter(id_annee=annee_active, est_active=True)
        total_eleves_inscrits = inscriptions.count()
        if total_eleves_inscrits > 0:
            eleves_reussis = 0
            for inscription in inscriptions:
                moyenne = Note.objects.filter(id_eleve=inscription.id_eleve, id_annee=annee_active).aggregate(Avg('note'))['note__avg']
                if moyenne and moyenne >= 10:
                    eleves_reussis += 1
            taux_reussite = int((eleves_reussis / total_eleves_inscrits) * 100) if total_eleves_inscrits > 0 else 0

    annees_scolaires = AnneeScolaire.objects.all().order_by('date_debut')
    evo_labels = []
    evo_data = []
    for annee in annees_scolaires:
        evo_labels.append(annee.annee_scolaire)
        evo_data.append(Inscription.objects.filter(id_annee=annee).count())
    if not evo_labels:
        evo_labels = ['Aucune donnée']
        evo_data = [0]

    repartition_labels = []
    repartition_data = []
    repartition_colors = ['#1e3c72', '#2a5298', '#3b6cb0', '#4c86c8', '#5c9fd9', '#6cb8ea', '#7dd1fb', '#8eeaff']
    if annee_active:
        classes_avec_inscrits = Classe.objects.filter(inscription__id_annee=annee_active, inscription__est_active=True).distinct()
        for classe in classes_avec_inscrits:
            nb_eleves = Inscription.objects.filter(id_classe=classe, id_annee=annee_active, est_active=True).count()
            if nb_eleves > 0:
                repartition_labels.append(classe.nom_classe)
                repartition_data.append(nb_eleves)
    if not repartition_labels:
        repartition_labels = ['Aucune inscription']
        repartition_data = [1]
        repartition_colors = ['#cbd5e1']

    annee_min = annees_scolaires.first().annee_scolaire.split('-')[0] if annees_scolaires else '2020'
    annee_max = annees_scolaires.last().annee_scolaire.split('-')[1] if annees_scolaires else '2024'

    context = {
        'user_nom': request.session.get('user_nom'),
        'total_eleves': total_eleves,
        'total_enseignants': total_enseignants,
        'total_classes': total_classes,
        'taux_reussite': taux_reussite,
        'top_eleves': top_eleves_data,
        'annee_active': annee_active,
        'evo_labels': json.dumps(evo_labels),
        'evo_data': json.dumps(evo_data),
        'annee_min': annee_min,
        'annee_max': annee_max,
        'repartition_labels': json.dumps(repartition_labels),
        'repartition_data': json.dumps(repartition_data),
        'repartition_colors': json.dumps(repartition_colors[:len(repartition_labels)]),
        'page_title': 'Dashboard Administrateur - CS KABA'
    }
    return render(request, 'Cote/admin/dashboard_de.html', context)


def dashboard_enseignant_old(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'ENSEIGNANT':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    context = {'user_nom': request.session.get('user_nom'), 'user_role': request.session.get('user_role'), 'page_title': 'Dashboard Enseignant - CS KABA'}
    return render(request, 'Cote/enseignant/dashboard_ense.html', context)


def dashboard_titulaire(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'TITULAIRE':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    context = {'user_nom': request.session.get('user_nom'), 'user_role': request.session.get('user_role'), 'page_title': 'Dashboard Titulaire - CS KABA'}
    return render(request, 'Cote/titulaire/dashboard_titulaire.html', context)


# =====================================================
# 3. GESTION DES ANNÉES SCOLAIRES (page + API)
# =====================================================

def annee_scolaire_page(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    context = {
        'user_nom': request.session.get('user_nom'),
        'annee_active': AnneeScolaire.objects.filter(est_active=True).first(),
        'annees': AnneeScolaire.objects.all().order_by('-id'),
        'page_title': 'Année scolaire - CS KABA'
    }
    return render(request, 'Cote/admin/annee_scolaire.html', context)


def validate_year_format(year_str):
    pattern = r'^\d{4}-\d{4}$'
    if not re.match(pattern, year_str):
        return False
    years = year_str.split('-')
    start_year = int(years[0])
    end_year = int(years[1])
    return end_year == start_year + 1


@csrf_exempt
def ajouter_annee(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    if request.content_type == 'application/json':
        data = json.loads(request.body)
        annee_scolaire = data.get('annee_scolaire', '').strip()
        date_debut_str = data.get('date_debut', '').strip()
        date_fin_str = data.get('date_fin', '').strip()
        est_active = data.get('est_active', False)
    else:
        annee_scolaire = request.POST.get('annee_scolaire', '').strip()
        date_debut_str = request.POST.get('date_debut', '').strip()
        date_fin_str = request.POST.get('date_fin', '').strip()
        est_active = request.POST.get('est_active') == 'true'

    if not annee_scolaire:
        return JsonResponse({'success': False, 'error': 'L\'année scolaire est requise'}, status=400)
    if not validate_year_format(annee_scolaire):
        return JsonResponse({'success': False, 'error': 'Format invalide. Utilisez AAAA-AAAA (ex: 2026-2027)'}, status=400)

    def parse_flexible_date(date_str):
        date_str = date_str.strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        if re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
            return datetime.strptime(date_str, '%d-%m-%Y').date()
        return None

    date_debut = parse_flexible_date(date_debut_str)
    date_fin = parse_flexible_date(date_fin_str)
    if not date_debut or not date_fin:
        return JsonResponse({'success': False, 'error': 'Dates invalides. Utilisez JJ/MM/AAAA ou AAAA-MM-JJ.'}, status=400)
    if date_debut >= date_fin:
        return JsonResponse({'success': False, 'error': 'La date de fin doit être postérieure à la date de début.'}, status=400)
    if AnneeScolaire.objects.filter(annee_scolaire=annee_scolaire).exists():
        return JsonResponse({'success': False, 'error': 'Cette année scolaire existe déjà.'}, status=400)
    if est_active:
        AnneeScolaire.objects.filter(est_active=True).update(est_active=False)
    try:
        annee = AnneeScolaire.objects.create(annee_scolaire=annee_scolaire, date_debut=date_debut, date_fin=date_fin, est_active=est_active)
        return JsonResponse({'success': True, 'message': f'Année scolaire {annee_scolaire} ajoutée avec succès'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erreur interne : {str(e)}'}, status=500)


def get_annee(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    try:
        annee = AnneeScolaire.objects.get(id=id)
        return JsonResponse({'success': True, 'annee': {
            'id': annee.id, 'annee_scolaire': annee.annee_scolaire,
            'date_debut': annee.date_debut.strftime('%Y-%m-%d'),
            'date_fin': annee.date_fin.strftime('%Y-%m-%d'),
            'est_active': annee.est_active
        }})
    except AnneeScolaire.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Année non trouvée'})


@csrf_exempt
def activer_annee(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'POST':
        try:
            AnneeScolaire.objects.filter(est_active=True).update(est_active=False)
            annee = AnneeScolaire.objects.get(id=id)
            annee.est_active = True
            annee.save()
            return JsonResponse({'success': True, 'message': f'Année scolaire {annee.annee_scolaire} activée avec succès'})
        except AnneeScolaire.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Année non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@csrf_exempt
def desactiver_annee(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'POST':
        try:
            annee = AnneeScolaire.objects.get(id=id)
            annee.est_active = False
            annee.save()
            return JsonResponse({'success': True, 'message': f'Année scolaire {annee.annee_scolaire} désactivée avec succès'})
        except AnneeScolaire.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Année non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@csrf_exempt
def supprimer_annee(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'DELETE':
        try:
            annee = AnneeScolaire.objects.get(id=id)
            if annee.inscription_set.exists():
                return JsonResponse({'success': False, 'error': 'Cette année scolaire contient des inscriptions. Supprimez-les d\'abord.'})
            nom = annee.annee_scolaire
            annee.delete()
            return JsonResponse({'success': True, 'message': f'Année scolaire {nom} supprimée avec succès'})
        except AnneeScolaire.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Année non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


def get_annee_stats(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    try:
        annee = AnneeScolaire.objects.get(id=id)
        inscriptions_count = annee.inscription_set.count()
        notes_count = annee.note_set.count()
        classes_count = annee.inscription_set.values('id_classe').distinct().count()
        taux_reussite = 0
        eleves_avec_moyenne = 0
        eleves_reussis = 0
        for inscription in annee.inscription_set.all():
            moyenne = inscription.id_eleve.note_set.filter(id_annee=annee).aggregate(Avg('note'))['note__avg']
            if moyenne:
                eleves_avec_moyenne += 1
                if moyenne >= 10:
                    eleves_reussis += 1
        if eleves_avec_moyenne > 0:
            taux_reussite = int((eleves_reussis / eleves_avec_moyenne) * 100)
        enseignants_count = Personnel.objects.filter(titulaireclasse__id_annee=annee).distinct().count()
        return JsonResponse({
            'success': True,
            'annee_scolaire': annee.annee_scolaire,
            'date_debut': annee.date_debut.strftime('%d/%m/%Y'),
            'date_fin': annee.date_fin.strftime('%d/%m/%Y'),
            'est_active': annee.est_active,
            'inscriptions': inscriptions_count,
            'notes': notes_count,
            'classes': classes_count,
            'taux_reussite': taux_reussite,
            'enseignants': enseignants_count
        })
    except AnneeScolaire.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Année non trouvée'})


def print_annee_report(request, id):
    if not request.session.get('user_id'):
        return redirect('login')
    try:
        annee = AnneeScolaire.objects.get(id=id)
        inscriptions = annee.inscription_set.select_related('id_eleve__id_personne', 'id_classe').all()
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Rapport Année Scolaire {annee.annee_scolaire}</title><meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #1e3c72; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #1e3c72; color: white; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 12px; color: #666; }}
        </style>
        </head>
        <body>
            <div class="header">
                <h1>CS KABA - Complexe Scolaire d'Excellence</h1>
                <h2>Rapport Année Scolaire {annee.annee_scolaire}</h2>
                <p>Période: du {annee.date_debut.strftime('%d/%m/%Y')} au {annee.date_fin.strftime('%d/%m/%Y')}</p>
                <p>Statut: {"Active" if annee.est_active else "Inactive"}</p>
            </div>
            <h3>Liste des inscriptions ({inscriptions.count()} élèves)</h3>
            <table>
                <thead>
                    <tr><th>Matricule</th><th>Nom complet</th><th>Classe</th><th>Date inscription</th></tr>
                </thead>
                <tbody>
        """
        for ins in inscriptions:
            html += f"<tr><td>{ins.id_eleve.matricule}</td><td>{ins.id_eleve.id_personne.nom} {ins.id_eleve.id_personne.prenom}</td><td>{ins.id_classe.nom_classe}</td><td>{ins.date_inscription.strftime('%d/%m/%Y')}</td></tr>"
        html += f"""
                </tbody>
            </table>
            <div class="footer"><p>Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p><p>CS KABA - Complexe Scolaire d'Excellence</p></div>
        </body></html>
        """
        return HttpResponse(html, content_type='text/html')
    except AnneeScolaire.DoesNotExist:
        return redirect('annee_scolaire_page')


# =====================================================
# 4. GESTION DES CLASSES ET OPTIONS (page + API)
# =====================================================

def gestion_cls_option_page(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    context = {
        'user_nom': request.session.get('user_nom'),
        'classes': Classe.objects.all().order_by('nom_classe'),
        'options': OptionEtude.objects.all().order_by('nom_option'),
        'page_title': 'Gestion des classes et options - CS KABA'
    }
    return render(request, 'Cote/admin/ajouter_cls_option.html', context)


@csrf_exempt
def ajouter_classe(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('dashboard_de')

    if request.method == 'POST':
        try:
            classe_id = request.POST.get('classe_id')
            nom_classe = request.POST.get('nom_classe', '').strip()
            cycle = request.POST.get('cycle', '')
            annee = request.POST.get('annee', '').strip()
            division = request.POST.get('division', '').strip()
            id_option = request.POST.get('id_option')
            capacite_max = request.POST.get('capacite_max', 30)
            actif = request.POST.get('actif') == 'on'

            est_cycle_orientation = (cycle == 'CO')

            # Génération du nom si non fourni
            if not nom_classe and annee and division:
                if est_cycle_orientation:
                    nom_classe = f"{annee}e{division}"
                else:
                    suffix = {1: 'ère', 2: 'ème', 3: 'ème', 4: 'ème'}
                    annee_int = int(annee)
                    nom_classe = f"{annee_int}{suffix.get(annee_int, 'ème')}{division}"

            if not nom_classe:
                messages.error(request, 'Nom de classe manquant')
                return redirect('gestion_cls_option_page')

            if classe_id:
                # Modification
                try:
                    classe = Classe.objects.get(id=classe_id)
                except Classe.DoesNotExist:
                    messages.error(request, 'Classe non trouvée')
                    return redirect('gestion_cls_option_page')

                # Vérification d'unicité pour la modification
                if not est_cycle_orientation and id_option:
                    if Classe.objects.filter(nom_classe=nom_classe, id_option_id=id_option).exclude(id=classe_id).exists():
                        messages.error(request, f'Une classe "{nom_classe}" avec cette option existe déjà')
                        return redirect('gestion_cls_option_page')
                else:
                    if Classe.objects.filter(nom_classe=nom_classe).exclude(id=classe_id).exists():
                        messages.error(request, f'Une classe "{nom_classe}" existe déjà')
                        return redirect('gestion_cls_option_page')

                classe.nom_classe = nom_classe
                classe.est_cycle_orientation = est_cycle_orientation
                classe.capacite_max = capacite_max
                classe.actif = actif

                if not est_cycle_orientation and id_option:
                    try:
                        classe.id_option = OptionEtude.objects.get(id=id_option)
                    except OptionEtude.DoesNotExist:
                        messages.error(request, 'Option non trouvée')
                        return redirect('gestion_cls_option_page')
                else:
                    classe.id_option = None

                classe.save()
                messages.success(request, f'Classe {nom_classe} modifiée avec succès')
            else:
                # Création - Vérification corrigée
                if not est_cycle_orientation and id_option:
                    if Classe.objects.filter(nom_classe=nom_classe, id_option_id=id_option).exists():
                        messages.error(request, f'Une classe "{nom_classe}" avec cette option existe déjà')
                        return redirect('gestion_cls_option_page')
                else:
                    if Classe.objects.filter(nom_classe=nom_classe).exists():
                        messages.error(request, f'Une classe "{nom_classe}" existe déjà')
                        return redirect('gestion_cls_option_page')

                classe = Classe.objects.create(
                    nom_classe=nom_classe,
                    est_cycle_orientation=est_cycle_orientation,
                    capacite_max=capacite_max,
                    actif=actif
                )

                if not est_cycle_orientation and id_option:
                    try:
                        classe.id_option = OptionEtude.objects.get(id=id_option)
                        classe.save()
                    except OptionEtude.DoesNotExist:
                        pass

                messages.success(request, f'Classe {nom_classe} ajoutée avec succès')

        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

        return redirect('gestion_cls_option_page')

    return redirect('gestion_cls_option_page')


def get_classe(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    try:
        classe = Classe.objects.get(id=id)
        return JsonResponse({'success': True, 'classe': {
            'id': classe.id, 'nom_classe': classe.nom_classe, 'niveau': classe.niveau,
            'id_option': classe.id_option.id if classe.id_option else None,
            'capacite_max': classe.capacite_max, 'est_cycle_orientation': classe.est_cycle_orientation,
            'actif': classe.actif
        }})
    except Classe.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Classe non trouvée'})


@csrf_exempt
def supprimer_classe(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'DELETE':
        try:
            classe = Classe.objects.get(id=id)
            if classe.inscription_set.exists():
                return JsonResponse({'success': False, 'error': f'Cette classe contient {classe.inscription_set.count()} élève(s). Supprimez d\'abord les inscriptions.'})
            nom = classe.nom_classe
            classe.delete()
            return JsonResponse({'success': True, 'message': f'Classe {nom} supprimée avec succès'})
        except Classe.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Classe non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@csrf_exempt
def toggle_classe(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            classe = Classe.objects.get(id=id)
            classe.actif = data.get('actif', False)
            classe.save()
            return JsonResponse({'success': True, 'message': f'Classe {"activée" if classe.actif else "désactivée"} avec succès'})
        except Classe.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Classe non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@csrf_exempt
def ajouter_option(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'POST':
        try:
            option_id = request.POST.get('option_id')
            nom_option = request.POST.get('nom_option')
            code_option = request.POST.get('code_option')
            actif = request.POST.get('actif') == 'on'
            if option_id:
                option = OptionEtude.objects.get(id=option_id)
                if OptionEtude.objects.filter(code_option=code_option).exclude(id=option_id).exists():
                    return JsonResponse({'success': False, 'error': 'Ce code option est déjà utilisé'})
                option.nom_option = nom_option
                option.code_option = code_option
                option.actif = actif
                option.save()
                return JsonResponse({'success': True, 'message': f'Option {nom_option} modifiée avec succès'})
            else:
                if OptionEtude.objects.filter(code_option=code_option).exists():
                    return JsonResponse({'success': False, 'error': 'Ce code option existe déjà'})
                option = OptionEtude.objects.create(nom_option=nom_option, code_option=code_option, actif=actif)
                return JsonResponse({'success': True, 'message': f'Option {nom_option} ajoutée avec succès'})
        except OptionEtude.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Option non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


def get_option(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    try:
        option = OptionEtude.objects.get(id=id)
        return JsonResponse({'success': True, 'option': {
            'id': option.id, 'nom_option': option.nom_option, 'code_option': option.code_option, 'actif': option.actif
        }})
    except OptionEtude.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Option non trouvée'})


@csrf_exempt
def supprimer_option(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'DELETE':
        try:
            option = OptionEtude.objects.get(id=id)
            if option.classe_set.exists():
                return JsonResponse({'success': False, 'error': 'Cette option est utilisée par des classes. Supprimez d\'abord les classes associées.'})
            nom = option.nom_option
            option.delete()
            return JsonResponse({'success': True, 'message': f'Option {nom} supprimée avec succès'})
        except OptionEtude.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Option non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@csrf_exempt
def toggle_option(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            option = OptionEtude.objects.get(id=id)
            option.actif = data.get('actif', False)
            option.save()
            return JsonResponse({'success': True, 'message': f'Option {"activée" if option.actif else "désactivée"} avec succès'})
        except OptionEtude.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Option non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


# =====================================================
# 5. GESTION DES ENSEIGNANTS
# =====================================================

def ajouter_enseignant_page(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    context = {
        'user_nom': request.session.get('user_nom'),
        'classes': Classe.objects.filter(actif=True),
        'page_title': 'Ajouter un enseignant - CS KABA'
    }
    return render(request, 'Cote/admin/ajouter_enseignant.html', context)


@csrf_exempt
def ajouter_enseignant(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'POST':
        try:
            nom = request.POST.get('nom')
            postnom = request.POST.get('postnom', '')
            prenom = request.POST.get('prenom')
            sexe = request.POST.get('sexe')
            date_naissance = request.POST.get('date_naissance')
            lieu_naissance = request.POST.get('lieu_naissance', '')
            email = request.POST.get('email')
            telephone = request.POST.get('telephone', '')
            adresse = request.POST.get('adresse', '')
            specialite = request.POST.get('specialite')
            date_embauche = request.POST.get('date_embauche')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            if password != password_confirm:
                return JsonResponse({'success': False, 'error': 'Les mots de passe ne correspondent pas'})
            if len(password) < 6:
                return JsonResponse({'success': False, 'error': 'Le mot de passe doit contenir au moins 6 caractères'})
            if Utilisateur.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Cet email est déjà utilisé'})
            personne = Personne.objects.create(
                nom=nom, postnom=postnom, prenom=prenom, sexe=sexe,
                date_naissance=date_naissance or None, lieu_naissance=lieu_naissance,
                email=email, telephone=telephone, adresse=adresse
            )
            utilisateur = Utilisateur(id_personne=personne, email=email, role='ENSEIGNANT', est_actif=True)
            utilisateur.set_password(password)
            utilisateur.save()
            Personnel.objects.create(id_utilisateur=utilisateur, specialite=specialite, date_embauche=date_embauche or datetime.now().date())
            return JsonResponse({'success': True, 'message': f'Enseignant {nom} {prenom} ajouté avec succès'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


# =====================================================
# 6. GESTION DES ÉLÈVES (page + API)
# =====================================================

def ajouter_eleve_page(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    classes = Classe.objects.filter(actif=True)
    options = OptionEtude.objects.filter(actif=True)
    annees = AnneeScolaire.objects.all().order_by('-id')
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    parents = Personne.objects.filter(telephone__isnull=False).exclude(telephone='').exclude(telephone__exact='')
    context = {
        'user_nom': request.session.get('user_nom'),
        'classes': classes,
        'options': options,
        'parents': parents,
        'annees': annees,
        'annee_active': annee_active,
        'page_title': 'Ajouter un élève - CS KABA'
    }
    return render(request, 'Cote/admin/ajouter_eleve.html', context)


@csrf_exempt
def ajouter_eleve(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

    if request.method == 'POST':
        try:
            nom = request.POST.get('nom')
            postnom = request.POST.get('postnom', '')
            prenom = request.POST.get('prenom')
            sexe = request.POST.get('sexe')
            date_naissance = request.POST.get('date_naissance')
            lieu_naissance = request.POST.get('lieu_naissance', '')
            adresse = request.POST.get('adresse', '')
            photo = request.FILES.get('photo')
            classe_id = request.POST.get('classe_id')
            annee_scolaire_id = request.POST.get('annee_scolaire')
            type_inscription = request.POST.get('type_inscription', 'NOUVEAU')
            ecole_provenance = request.POST.get('ecole_provenance', '')
            date_inscription_str = request.POST.get('date_inscription')
            parent_id = request.POST.get('parent_id')
            nom_parent = request.POST.get('nom_parent', '')
            prenom_parent = request.POST.get('prenom_parent', '')
            telephone_parent = request.POST.get('telephone_parent', '')
            email_parent = request.POST.get('email_parent', '')
            profession_parent = request.POST.get('profession_parent', '')
            adresse_parent = request.POST.get('adresse_parent', '')

            if not nom or not prenom or not sexe:
                return JsonResponse({'success': False, 'error': 'Nom, prénom et sexe sont requis'})
            if not classe_id:
                return JsonResponse({'success': False, 'error': 'Veuillez sélectionner une classe'})
            if not annee_scolaire_id:
                return JsonResponse({'success': False, 'error': 'Année scolaire non spécifiée'})

            try:
                classe = Classe.objects.get(id=classe_id, actif=True)
            except Classe.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Classe invalide ou inactive'})
            try:
                annee_scolaire_obj = AnneeScolaire.objects.get(id=annee_scolaire_id)
            except AnneeScolaire.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Année scolaire invalide'})

            parent_personne = None
            if parent_id:
                try:
                    parent_personne = Personne.objects.get(id=parent_id)
                    if telephone_parent:
                        parent_personne.telephone = telephone_parent
                    if email_parent:
                        parent_personne.email = email_parent
                    if adresse_parent:
                        parent_personne.adresse = adresse_parent
                    parent_personne.save()
                except Personne.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Parent introuvable'})
            elif nom_parent and telephone_parent:
                parent_existant = Personne.objects.filter(telephone=telephone_parent).first()
                if parent_existant:
                    return JsonResponse({'success': False, 'error': f'Un parent avec le téléphone {telephone_parent} existe déjà (ID {parent_existant.id}). Veuillez le sélectionner dans la liste.'})
                parent_existant_nom = Personne.objects.filter(nom__iexact=nom_parent, prenom__iexact=prenom_parent).first()
                if parent_existant_nom:
                    return JsonResponse({'success': False, 'error': f'Un parent avec le nom "{nom_parent} {prenom_parent}" existe déjà. Veuillez le sélectionner dans la liste.'})
                parent_personne = Personne.objects.create(
                    nom=nom_parent, prenom=prenom_parent, telephone=telephone_parent,
                    email=email_parent, adresse=adresse_parent
                )
            else:
                return JsonResponse({'success': False, 'error': 'Veuillez sélectionner un parent existant ou saisir nom et téléphone du nouveau parent'})

            if date_inscription_str:
                date_inscription = datetime.strptime(date_inscription_str, '%Y-%m-%d').date()
            else:
                date_inscription = datetime.now().date()

            annee_mat = date_inscription.year
            jour = date_inscription.strftime('%d')
            mois = date_inscription.strftime('%m')
            compteur = Inscription.objects.filter(date_inscription=date_inscription, id_annee=annee_scolaire_obj).count() + 1
            compteur_str = str(compteur).zfill(3)
            matricule = f"KABA{annee_mat}{jour}{mois}{compteur_str}"
            while Eleve.objects.filter(matricule=matricule).exists():
                compteur += 1
                compteur_str = str(compteur).zfill(3)
                matricule = f"KABA{annee_mat}{jour}{mois}{compteur_str}"

            personne = Personne.objects.create(
                nom=nom, postnom=postnom, prenom=prenom, sexe=sexe,
                date_naissance=date_naissance or None, lieu_naissance=lieu_naissance,
                adresse=adresse
            )
            eleve = Eleve.objects.create(
                id_personne=personne, matricule=matricule,
                telephone_parent=telephone_parent or (parent_personne.telephone if parent_personne else ''),
                email_parent=email_parent or (parent_personne.email if parent_personne else ''),
                est_actif=True
            )
            if photo:
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                import os
                ext = os.path.splitext(photo.name)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                    eleve.delete()
                    personne.delete()
                    return JsonResponse({'success': False, 'error': 'Format de photo non supporté (JPG, PNG, GIF)'})
                nouveau_nom = f"{matricule}{ext}"
                chemin = default_storage.save(f'photos/eleves/{nouveau_nom}', ContentFile(photo.read()))
                eleve.photo = chemin
                eleve.save()
            Inscription.objects.create(
                id_eleve=eleve, id_classe=classe, id_annee=annee_scolaire_obj,
                type_inscription=type_inscription, date_inscription=date_inscription, est_active=True
            )
            return JsonResponse({'success': True, 'message': f'Élève {nom} {prenom} inscrit avec succès en {classe.nom_classe}. Matricule: {matricule}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


# =====================================================
# 6.1 LISTE DES ÉLÈVES (avec filtres)
# =====================================================

def liste_eleves(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    
    cycle = request.GET.get('cycle', '')
    classe_id = request.GET.get('classe', '')
    option_id = request.GET.get('option', '')
    
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    if annee_active:
        inscriptions = Inscription.objects.filter(id_annee=annee_active, est_active=True).select_related(
            'id_eleve__id_personne', 'id_classe', 'id_classe__id_option'
        )
    else:
        inscriptions = Inscription.objects.none()
    
    if cycle == 'CO':
        inscriptions = inscriptions.filter(id_classe__est_cycle_orientation=True)
    elif cycle == 'SECONDAIRE':
        inscriptions = inscriptions.filter(id_classe__est_cycle_orientation=False)
    if classe_id:
        inscriptions = inscriptions.filter(id_classe_id=classe_id)
    if option_id:
        inscriptions = inscriptions.filter(id_classe__id_option_id=option_id)
    
    eleves_list = []
    for ins in inscriptions:
        eleve = ins.id_eleve
        eleves_list.append({
            'id': eleve.id, 'matricule': eleve.matricule, 'nom': eleve.id_personne.nom,
            'postnom': eleve.id_personne.postnom or '', 'prenom': eleve.id_personne.prenom,
            'sexe': eleve.id_personne.sexe, 'classe_nom': ins.id_classe.nom_classe,
            'classe_id': ins.id_classe.id, 'option_nom': ins.id_classe.id_option.nom_option if ins.id_classe.id_option else None,
            'est_cycle_orientation': ins.id_classe.est_cycle_orientation,
            'photo': eleve.photo.url if eleve.photo else None,
        })
    
    cycles = [{'value': 'CO', 'label': 'Cycle d\'Orientation'}, {'value': 'SECONDAIRE', 'label': 'Secondaire'}]
    classes = Classe.objects.filter(actif=True).order_by('est_cycle_orientation', 'nom_classe')
    options = OptionEtude.objects.filter(actif=True).order_by('nom_option')
    
    context = {
        'user_nom': request.session.get('user_nom'), 'eleves': eleves_list, 'cycles': cycles,
        'classes': classes, 'options': options, 'cycle_selected': cycle,
        'classe_selected': int(classe_id) if classe_id else None,
        'option_selected': int(option_id) if option_id else None, 'annee_active': annee_active,
        'page_title': 'Liste des élèves - CS KABA'
    }
    return render(request, 'Cote/admin/liste_eleves.html', context)


# =====================================================
# 6.2 DÉTAIL D'UN ÉLÈVE
# =====================================================

def detail_eleve(request, eleve_id):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    
    try:
        eleve = Eleve.objects.select_related('id_personne').get(id=eleve_id, est_actif=True)
    except Eleve.DoesNotExist:
        messages.error(request, 'Élève introuvable')
        return redirect('liste_eleves')
    
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    inscription_actuelle = None
    if annee_active:
        try:
            inscription_actuelle = Inscription.objects.select_related('id_classe').get(
                id_eleve=eleve, id_annee=annee_active, est_active=True
            )
        except Inscription.DoesNotExist:
            pass
    inscriptions_passees = Inscription.objects.filter(id_eleve=eleve).exclude(id_annee=annee_active).select_related('id_annee', 'id_classe').order_by('-date_inscription')
    
    context = {
        'user_nom': request.session.get('user_nom'), 'eleve': eleve, 'personne': eleve.id_personne,
        'photo_url': eleve.photo.url if eleve.photo else None, 'inscription_actuelle': inscription_actuelle,
        'inscriptions_passees': inscriptions_passees, 'annee_active': annee_active,
        'page_title': f'Détail de {eleve.id_personne.nom} {eleve.id_personne.prenom} - CS KABA'
    }
    return render(request, 'Cote/admin/detail_eleve.html', context)


# =====================================================
# 6.3 MODIFICATION D'UN ÉLÈVE (page + API)
# =====================================================

def modifier_eleve_page(request, eleve_id):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    
    try:
        eleve = Eleve.objects.select_related('id_personne').get(id=eleve_id, est_actif=True)
    except Eleve.DoesNotExist:
        messages.error(request, 'Élève introuvable')
        return redirect('liste_eleves')
    
    classes = Classe.objects.filter(actif=True).order_by('nom_classe')
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    inscription_actuelle = None
    if annee_active:
        try:
            inscription_actuelle = Inscription.objects.get(id_eleve=eleve, id_annee=annee_active, est_active=True)
        except Inscription.DoesNotExist:
            pass
    parents = Personne.objects.filter(telephone__isnull=False).exclude(telephone='').exclude(telephone__exact='')
    parent_personne = None
    if eleve.telephone_parent:
        parent_personne = parents.filter(telephone=eleve.telephone_parent).first()
    
    context = {
        'user_nom': request.session.get('user_nom'), 'eleve': eleve, 'personne': eleve.id_personne,
        'classes': classes, 'annee_active': annee_active, 'inscription_actuelle': inscription_actuelle,
        'parents': parents, 'parent_personne': parent_personne,
        'parent_nom': parent_personne.nom if parent_personne else '',
        'parent_prenom': parent_personne.prenom if parent_personne else '',
        'parent_telephone': parent_personne.telephone if parent_personne else eleve.telephone_parent or '',
        'parent_email': parent_personne.email if parent_personne else eleve.email_parent or '',
        'parent_profession': '', 'parent_adresse': parent_personne.adresse if parent_personne else '',
        'page_title': f'Modifier {eleve.id_personne.nom} {eleve.id_personne.prenom} - CS KABA'
    }
    return render(request, 'Cote/admin/modifier_eleve.html', context)


@csrf_exempt
def modifier_eleve(request, eleve_id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        eleve = Eleve.objects.select_related('id_personne').get(id=eleve_id, est_actif=True)
    except Eleve.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Élève introuvable'})
    
    try:
        nom = request.POST.get('nom')
        postnom = request.POST.get('postnom', '')
        prenom = request.POST.get('prenom')
        sexe = request.POST.get('sexe')
        date_naissance = request.POST.get('date_naissance')
        lieu_naissance = request.POST.get('lieu_naissance', '')
        adresse = request.POST.get('adresse', '')
        telephone_parent = request.POST.get('telephone_parent', '')
        email_parent = request.POST.get('email_parent', '')
        photo = request.FILES.get('photo')
        classe_id = request.POST.get('classe_id')
        type_inscription = request.POST.get('type_inscription', 'NOUVEAU')
        parent_id = request.POST.get('parent_id')
        nom_parent = request.POST.get('nom_parent', '')
        prenom_parent = request.POST.get('prenom_parent', '')
        adresse_parent = request.POST.get('adresse_parent', '')
        
        personne = eleve.id_personne
        personne.nom = nom
        personne.postnom = postnom
        personne.prenom = prenom
        personne.sexe = sexe
        personne.date_naissance = date_naissance or None
        personne.lieu_naissance = lieu_naissance
        personne.adresse = adresse
        personne.save()
        
        if parent_id:
            try:
                parent_personne = Personne.objects.get(id=parent_id)
                if telephone_parent:
                    parent_personne.telephone = telephone_parent
                if email_parent:
                    parent_personne.email = email_parent
                if adresse_parent:
                    parent_personne.adresse = adresse_parent
                parent_personne.save()
                eleve.telephone_parent = parent_personne.telephone
                eleve.email_parent = parent_personne.email
            except Personne.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Parent introuvable'})
        elif nom_parent and telephone_parent:
            parent_existant = Personne.objects.filter(telephone=telephone_parent).first()
            if parent_existant:
                return JsonResponse({'success': False, 'error': f'Un parent avec le téléphone {telephone_parent} existe déjà. Veuillez le sélectionner dans la liste.'})
            parent_personne = Personne.objects.create(
                nom=nom_parent, prenom=prenom_parent, telephone=telephone_parent,
                email=email_parent, adresse=adresse_parent
            )
            eleve.telephone_parent = telephone_parent
            eleve.email_parent = email_parent
        
        if photo:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            import os
            ext = os.path.splitext(photo.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                return JsonResponse({'success': False, 'error': 'Format de photo non supporté (JPG, PNG, GIF)'})
            nouveau_nom = f"{eleve.matricule}{ext}"
            chemin = default_storage.save(f'photos/eleves/{nouveau_nom}', ContentFile(photo.read()))
            if eleve.photo:
                default_storage.delete(eleve.photo.name)
            eleve.photo = chemin
        eleve.save()
        
        annee_active = AnneeScolaire.objects.filter(est_active=True).first()
        if annee_active and classe_id:
            Inscription.objects.update_or_create(
                id_eleve=eleve, id_annee=annee_active,
                defaults={'id_classe_id': classe_id, 'type_inscription': type_inscription, 'est_active': True}
            )
        return JsonResponse({'success': True, 'message': 'Élève modifié avec succès'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =====================================================
# 6.4 REÇU D'INSCRIPTION (HTML imprimable)
# =====================================================

def generer_recu_inscription(request, eleve_id):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('dashboard_de')
    
    try:
        eleve = Eleve.objects.select_related('id_personne').get(id=eleve_id, est_actif=True)
    except Eleve.DoesNotExist:
        messages.error(request, 'Élève introuvable')
        return redirect('liste_eleves')
    
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    if not annee_active:
        messages.error(request, 'Aucune année scolaire active')
        return redirect('liste_eleves')
    try:
        inscription = Inscription.objects.select_related('id_classe').get(id_eleve=eleve, id_annee=annee_active, est_active=True)
    except Inscription.DoesNotExist:
        messages.error(request, 'Cet élève n\'est pas inscrit pour l\'année en cours')
        return redirect('liste_eleves')
    
    inscriptions_anterieures = Inscription.objects.filter(id_eleve=eleve).exclude(id_annee=annee_active).count()
    est_reinscription = inscriptions_anterieures > 0
    montant = 5 if est_reinscription else 10
    titre_recu = "REÇU DE PAIEMENT FRAIS RÉINSCRIPTION" if est_reinscription else "REÇU DE PAIEMENT FRAIS INSCRIPTION"
    numero_recu = f"REC-{annee_active.annee_scolaire.replace('-', '')}-{eleve.matricule}"
    date_inscription = inscription.date_inscription.strftime("%d/%m/%Y")
    
    def montant_en_lettres(m):
        return "CINQ" if m == 5 else "DIX" if m == 10 else str(m)
    montant_lettres = montant_en_lettres(montant) + " DOLLARS AMÉRICAINS"
    
    context = {
        'user_nom': request.session.get('user_nom'), 'eleve': eleve, 'personne': eleve.id_personne,
        'classe_nom': inscription.id_classe.nom_classe, 'annee_scolaire': annee_active.annee_scolaire,
        'numero_recu': numero_recu, 'montant': montant, 'montant_lettres': montant_lettres,
        'titre_recu': titre_recu, 'date_inscription': date_inscription, 'est_reinscription': est_reinscription,
        'photo_url': eleve.photo.url if eleve.photo else None,
    }
    return render(request, 'Cote/admin/recu_inscription.html', context)


# =====================================================
# 7. STATISTIQUES, PALMARÈS, EXPORTS
# =====================================================

def stats_data(request):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Non authentifié'}, status=401)

    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    if annee_active:
        total_eleves = Inscription.objects.filter(id_annee=annee_active, est_active=True).count()
        total_enseignants = Personnel.objects.filter(
            Q(attributioncours__id_annee=annee_active) |
            Q(titulaireclasse__id_annee=annee_active)
        ).distinct().count()
        total_classes = Classe.objects.filter(inscription__id_annee=annee_active, inscription__est_active=True).distinct().count()
        inscriptions = Inscription.objects.filter(id_annee=annee_active, est_active=True)
        total_eleves_inscrits = inscriptions.count()
        eleves_reussis = 0
        for inscription in inscriptions:
            moyenne = Note.objects.filter(id_eleve=inscription.id_eleve, id_annee=annee_active).aggregate(Avg('note'))['note__avg']
            if moyenne and moyenne >= 10:
                eleves_reussis += 1
        taux_reussite = int((eleves_reussis / total_eleves_inscrits) * 100) if total_eleves_inscrits > 0 else 0
    else:
        total_eleves = 0
        total_enseignants = 0
        total_classes = 0
        taux_reussite = 0

    data = {
        'total_eleves': total_eleves,
        'total_enseignants': total_enseignants,
        'total_classes': total_classes,
        'taux_reussite': taux_reussite if taux_reussite > 0 else 0,
    }
    return JsonResponse(data)


@csrf_exempt
def generer_palmares(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'POST':
        try:
            annee_active = AnneeScolaire.objects.filter(est_active=True).first()
            if not annee_active:
                return JsonResponse({'success': False, 'error': 'Aucune année scolaire active'})
            Palmares.objects.filter(id_annee=annee_active).delete()
            for classe in Classe.objects.filter(actif=True):
                inscriptions = Inscription.objects.filter(id_classe=classe, id_annee=annee_active, est_active=True).select_related('id_eleve')
                eleves_avec_moyennes = []
                for inscription in inscriptions:
                    moyenne = Note.objects.filter(id_eleve=inscription.id_eleve, id_annee=annee_active).aggregate(Avg('note'))['note__avg']
                    if moyenne:
                        mention = 'EXCELLENT' if moyenne >= 16 else 'TRES BIEN' if moyenne >= 14 else 'BIEN' if moyenne >= 12 else 'ASSEZ BIEN' if moyenne >= 10 else 'PASSABLE'
                        eleves_avec_moyennes.append({'eleve': inscription.id_eleve, 'moyenne': moyenne, 'mention': mention})
                eleves_avec_moyennes.sort(key=lambda x: x['moyenne'], reverse=True)
                for rang, item in enumerate(eleves_avec_moyennes, 1):
                    Palmares.objects.create(id_annee=annee_active, id_classe=classe, id_eleve=item['eleve'], rang=rang, mention=item['mention'])
            return JsonResponse({'success': True, 'message': 'Palmarès généré avec succès'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


def export_pdf(request):
    if not request.session.get('user_id'):
        return redirect('login')
    messages.info(request, 'Fonctionnalité d\'export PDF en développement')
    return redirect('dashboard_de')


def export_excel(request):
    if not request.session.get('user_id'):
        return redirect('login')
    messages.info(request, 'Fonctionnalité d\'export Excel en développement')
    return redirect('dashboard_de')


@csrf_exempt
def definir_annee(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'POST':
        try:
            annee_scolaire = request.POST.get('annee_scolaire')
            date_debut = request.POST.get('date_debut')
            date_fin = request.POST.get('date_fin')
            AnneeScolaire.objects.filter(est_active=True).update(est_active=False)
            AnneeScolaire.objects.create(annee_scolaire=annee_scolaire, date_debut=date_debut, date_fin=date_fin, est_active=True)
            return JsonResponse({'success': True, 'message': f'Année scolaire {annee_scolaire} définie avec succès'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


# =====================================================
# 8. GESTION DES COURS, ATTRIBUTIONS ET TITULAIRES
# =====================================================

def cours_de_page(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    
    cours_list = Cours.objects.all().select_related('id_option').order_by('nom_cours')
    cycles = [{'value': 'CO', 'label': 'Cycle d\'Orientation (7e-8e)'}, {'value': 'SECONDAIRE', 'label': 'Secondaire'}]
    options = OptionEtude.objects.filter(actif=True).order_by('nom_option')
    classes = Classe.objects.filter(actif=True).order_by('nom_classe')
    enseignants = Personnel.objects.filter(id_utilisateur__role='ENSEIGNANT', id_utilisateur__est_actif=True).select_related('id_utilisateur__id_personne')
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    titulaires = TitulaireClasse.objects.filter(id_annee=annee_active).select_related('id_personnel__id_utilisateur__id_personne', 'id_classe') if annee_active else []
    
    context = {
        'user_nom': request.session.get('user_nom'), 'cours_list': cours_list, 'cycles': cycles,
        'options': options, 'classes': classes, 'enseignants': enseignants, 'annee_active': annee_active,
        'titulaires': titulaires,
        'classes_json': json.dumps([{'id': c.id, 'nom_classe': c.nom_classe, 'est_cycle_orientation': c.est_cycle_orientation} for c in classes]),
        'page_title': 'Gestion des cours - CS KABA'
    }
    return render(request, 'Cote/admin/cours_de.html', context)


@csrf_exempt
def ajouter_cours(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        nom_cours = request.POST.get('nom_cours')
        code_cours = request.POST.get('code_cours')
        coefficient = request.POST.get('coefficient', 1)
        points_par_periode = request.POST.get('points_par_periode', 40)
        description = request.POST.get('description', '')
        cycle = request.POST.get('cycle')
        option_id = request.POST.get('option_id')
        
        if not nom_cours or not code_cours:
            return JsonResponse({'success': False, 'error': 'Nom et code du cours requis'})
        if Cours.objects.filter(code_cours=code_cours).exists():
            return JsonResponse({'success': False, 'error': 'Ce code de cours existe déjà'})
        
        cours = Cours.objects.create(
            nom_cours=nom_cours, code_cours=code_cours, coefficient=coefficient,
            points_par_periode=points_par_periode, description=description,
            id_option_id=option_id if option_id and cycle == 'SECONDAIRE' else None,
            created_by_id=request.session.get('user_id')
        )
        return JsonResponse({'success': True, 'message': 'Cours ajouté avec succès', 'cours_id': cours.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_cours(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    try:
        cours = Cours.objects.get(id=id)
        return JsonResponse({'success': True, 'cours': {
            'id': cours.id, 'nom_cours': cours.nom_cours, 'code_cours': cours.code_cours,
            'coefficient': cours.coefficient, 'points_par_periode': cours.points_par_periode,
            'description': cours.description,
            'id_option': cours.id_option.id if cours.id_option else None
        }})
    except Cours.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cours introuvable'})


@csrf_exempt
def modifier_cours(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        cours = Cours.objects.get(id=id)
        cours.nom_cours = request.POST.get('nom_cours')
        cours.code_cours = request.POST.get('code_cours')
        cours.coefficient = request.POST.get('coefficient', 1)
        cours.points_par_periode = request.POST.get('points_par_periode', 40)
        cours.description = request.POST.get('description', '')
        cycle = request.POST.get('cycle')
        option_id = request.POST.get('option_id')
        cours.id_option_id = option_id if option_id and cycle == 'SECONDAIRE' else None
        cours.save()
        return JsonResponse({'success': True, 'message': 'Cours modifié avec succès'})
    except Cours.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cours introuvable'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def supprimer_cours(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        cours = Cours.objects.get(id=id)
        if AttributionCours.objects.filter(id_cours=cours).exists():
            return JsonResponse({'success': False, 'error': 'Ce cours est déjà attribué à des classes. Supprimez d\'abord les attributions.'})
        nom = cours.nom_cours
        cours.delete()
        return JsonResponse({'success': True, 'message': f'Cours {nom} supprimé'})
    except Cours.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cours introuvable'})


@csrf_exempt
def get_cours_par_option(request):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    
    cycle = request.GET.get('cycle')
    option_id = request.GET.get('option_id')
    
    if cycle == 'CO':
        cours = Cours.objects.filter(id_option__isnull=True)
    elif cycle == 'SECONDAIRE' and option_id:
        cours = Cours.objects.filter(Q(id_option_id=option_id) | Q(id_option__isnull=True))
    else:
        cours = Cours.objects.none()
    data = [{'id': c.id, 'nom': c.nom_cours, 'code': c.code_cours, 'coefficient': c.coefficient, 'points_par_periode': c.points_par_periode} for c in cours]
    return JsonResponse({'success': True, 'cours': data})


@csrf_exempt
def attribuer_cours(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        cours_id = request.POST.get('cours_id')
        personnel_id = request.POST.get('personnel_id')
        classe_id = request.POST.get('classe_id')
        annee_id = request.POST.get('annee_id')
        
        if not all([cours_id, personnel_id, classe_id, annee_id]):
            return JsonResponse({'success': False, 'error': 'Tous les champs sont requis'})
        if AttributionCours.objects.filter(id_cours_id=cours_id, id_classe_id=classe_id, id_annee_id=annee_id).exists():
            return JsonResponse({'success': False, 'error': 'Ce cours est déjà attribué à cette classe'})
        AttributionCours.objects.create(
            id_personnel_id=personnel_id, id_cours_id=cours_id,
            id_classe_id=classe_id, id_annee_id=annee_id, est_active=True
        )
        return JsonResponse({'success': True, 'message': 'Cours attribué avec succès'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_attributions_classe(request):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    classe_id = request.GET.get('classe_id')
    annee_id = request.GET.get('annee_id')
    if not classe_id or not annee_id:
        return JsonResponse({'error': 'Paramètres manquants'}, status=400)
    attributions = AttributionCours.objects.filter(
        id_classe_id=classe_id, id_annee_id=annee_id, est_active=True
    ).select_related('id_cours', 'id_personnel__id_utilisateur__id_personne')
    data = [{'id': a.id, 'cours_nom': a.id_cours.nom_cours, 'cours_code': a.id_cours.code_cours,
             'enseignant': f"{a.id_personnel.id_utilisateur.id_personne.nom} {a.id_personnel.id_utilisateur.id_personne.prenom}"}
            for a in attributions]
    return JsonResponse({'success': True, 'attributions': data})


@csrf_exempt
def supprimer_attribution(request, attribution_id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    try:
        attribution = AttributionCours.objects.get(id=attribution_id)
        attribution.delete()
        return JsonResponse({'success': True, 'message': 'Attribution supprimée'})
    except AttributionCours.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Attribution introuvable'})


# ----- Gestion des titulaires (corrigée avec contraintes) -----

@csrf_exempt
def definir_titulaire(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        classe_id = request.POST.get('classe_id')
        personnel_id = request.POST.get('personnel_id')
        annee_id = request.POST.get('annee_id')
        
        if not classe_id or not annee_id:
            return JsonResponse({'success': False, 'error': 'Classe et année requises'})
        
        if not personnel_id:
            TitulaireClasse.objects.filter(id_classe_id=classe_id, id_annee_id=annee_id).delete()
            return JsonResponse({'success': True, 'message': 'Titulaire supprimé'})
        
        autre_titulaire = TitulaireClasse.objects.filter(id_personnel_id=personnel_id, id_annee_id=annee_id).exclude(id_classe_id=classe_id).first()
        if autre_titulaire:
            return JsonResponse({'success': False, 'error': f'Cet enseignant est déjà titulaire de la classe "{autre_titulaire.id_classe.nom_classe}" pour cette année.'})
        
        titulaire, created = TitulaireClasse.objects.update_or_create(
            id_classe_id=classe_id, id_annee_id=annee_id,
            defaults={'id_personnel_id': personnel_id, 'est_actif': True}
        )
        return JsonResponse({'success': True, 'message': 'Titulaire désigné avec succès' if created else 'Titulaire mis à jour avec succès'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_titulaire(request):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    classe_id = request.GET.get('classe_id')
    annee_id = request.GET.get('annee_id')
    if not classe_id or not annee_id:
        return JsonResponse({'error': 'Paramètres manquants'}, status=400)
    titulaire = TitulaireClasse.objects.filter(id_classe_id=classe_id, id_annee_id=annee_id).select_related('id_personnel__id_utilisateur__id_personne').first()
    if titulaire:
        data = {'id': titulaire.id, 'personnel_id': titulaire.id_personnel_id,
                'nom': f"{titulaire.id_personnel.id_utilisateur.id_personne.nom} {titulaire.id_personnel.id_utilisateur.id_personne.prenom}"}
    else:
        data = None
    return JsonResponse({'success': True, 'titulaire': data})


@csrf_exempt
def supprimer_titulaire_par_id(request, titulaire_id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    try:
        titulaire = TitulaireClasse.objects.get(id=titulaire_id)
        titulaire.delete()
        return JsonResponse({'success': True, 'message': 'Titulaire supprimé avec succès'})
    except TitulaireClasse.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Titulaire introuvable'})


def get_titulaires_liste(request):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    annee_id = request.GET.get('annee_id')
    if not annee_id:
        return JsonResponse({'error': 'Année non spécifiée'}, status=400)
    titulaires = TitulaireClasse.objects.filter(id_annee_id=annee_id).select_related(
        'id_personnel__id_utilisateur__id_personne', 'id_classe', 'id_annee'
    )
    data = [{
        'id': t.id,
        'enseignant_nom': f"{t.id_personnel.id_utilisateur.id_personne.nom} {t.id_personnel.id_utilisateur.id_personne.prenom}",
        'classe_nom': t.id_classe.nom_classe,
        'annee_scolaire': t.id_annee.annee_scolaire,
    } for t in titulaires]
    return JsonResponse({'success': True, 'titulaires': data})


@csrf_exempt
def filtrer_classes_par_cycle(request):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    cycle = request.GET.get('cycle')
    if cycle == 'CO':
        classes = Classe.objects.filter(est_cycle_orientation=True, actif=True).order_by('nom_classe')
    elif cycle == 'SECONDAIRE':
        classes = Classe.objects.filter(est_cycle_orientation=False, actif=True).order_by('nom_classe')
    else:
        classes = Classe.objects.none()
    data = [{'id': c.id, 'nom_classe': c.nom_classe} for c in classes]
    return JsonResponse({'success': True, 'classes': data})


# =====================================================
# ESPACE ENSEIGNANT
# =====================================================

def dashboard_enseignant(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'ENSEIGNANT':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')
    context = {
        'user_nom': request.session.get('user_nom'),
        'user_role': request.session.get('user_role'),
        'page_title': 'Dashboard Enseignant - CS KABA'
    }
    return render(request, 'Cote/enseignant/dashboard_enseignant.html', context)


@csrf_exempt
def get_enseignant_data(request):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    
    user_id = request.session.get('user_id')
    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
    except Personnel.DoesNotExist:
        return JsonResponse({'error': 'Personnel non trouvé pour cet utilisateur'}, status=404)
    
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    if not annee_active:
        return JsonResponse({'error': 'Aucune année scolaire active'}, status=400)
    
    attributions = AttributionCours.objects.filter(
        id_personnel=personnel,
        id_annee=annee_active,
        est_active=True
    ).select_related('id_cours', 'id_classe', 'id_classe__id_option')
    
    cours_data = []
    classes_set = set()
    total_eleves = 0
    
    for attr in attributions:
        effectif = Inscription.objects.filter(
            id_classe=attr.id_classe,
            id_annee=annee_active,
            est_active=True
        ).count()
        total_eleves += effectif
        
        option_nom = attr.id_classe.id_option.nom_option if attr.id_classe.id_option else "Sans option"
        
        cours_data.append({
            'cours_nom': attr.id_cours.nom_cours,
            'cours_code': attr.id_cours.code_cours,
            'coefficient': attr.id_cours.coefficient,
            'points_par_periode': attr.id_cours.points_par_periode,
            'classe_nom': attr.id_classe.nom_classe,
            'classe_id': attr.id_classe.id,
            'option_nom': option_nom,
            'effectif': effectif
        })
        classes_set.add(attr.id_classe.nom_classe)
    
    titulaire = TitulaireClasse.objects.filter(
        id_personnel=personnel,
        id_annee=annee_active,
        est_actif=True
    ).select_related('id_classe').first()
    
    return JsonResponse({
        'success': True,
        'total_cours': len(cours_data),
        'total_classes': len(classes_set),
        'total_eleves': total_eleves,
        'cours': cours_data,
        'classes_enseignees': list(classes_set),
        'titulaire': {
            'est_titulaire': bool(titulaire),
            'classe_nom': titulaire.id_classe.nom_classe if titulaire else None
        }
    })


def mes_cours(request):
    """Affiche la liste des cours assignés à l'enseignant connecté pour l'année active."""
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'ENSEIGNANT':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')

    user_id = request.session.get('user_id')
    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
    except Personnel.DoesNotExist:
        messages.error(request, 'Profil enseignant introuvable')
        return redirect('dashboard_enseignant')

    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    if not annee_active:
        messages.warning(request, 'Aucune année scolaire active')
        annee_active = None

    cours_list = []
    if annee_active:
        attributions = AttributionCours.objects.filter(
            id_personnel=personnel,
            id_annee=annee_active,
            est_active=True
        ).select_related('id_cours', 'id_classe')

        for att in attributions:
            effectif = Inscription.objects.filter(
                id_classe=att.id_classe,
                id_annee=annee_active,
                est_active=True
            ).count()
            cours_list.append({
                'classe_nom': att.id_classe.nom_classe,
                'cours_nom': att.id_cours.nom_cours,
                'cours_id': att.id_cours.id,
                'classe_id': att.id_classe.id,
                'effectif': effectif,
            })

    context = {
        'user_nom': request.session.get('user_nom'),
        'cours_list': cours_list,
        'annee_active': annee_active,
        'page_title': 'Mes cours - CS KABA'
    }
    return render(request, 'Cote/enseignant/mes_cours.html', context)


# =====================================================
# NOUVELLES VUES POUR LA SAISIE DES COTES (AJAX) - VERSION POINTS
# =====================================================

def mon_profil(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'ENSEIGNANT':
        messages.error(request, 'Accès non autorisé')
        return redirect('login')

    user_id = request.session.get('user_id')
    try:
        personnel = Personnel.objects.select_related('id_utilisateur__id_personne').get(id_utilisateur_id=user_id)
        utilisateur = personnel.id_utilisateur
        personne = utilisateur.id_personne
    except Personnel.DoesNotExist:
        messages.error(request, 'Profil enseignant introuvable')
        return redirect('dashboard_enseignant')

    # Construction des données
    profile_data = {
        'nom_complet': f"{personne.nom} {personne.prenom}".strip(),
        'email': utilisateur.email,
        'telephone': personne.telephone if personne.telephone else '',
        'specialite': personnel.specialite if personnel.specialite else '',
        'date_embauche': personnel.date_embauche.strftime('%d/%m/%Y') if personnel.date_embauche else '',
        'role': utilisateur.get_role_display(),
    }
    import json
    profile_data_json = json.dumps(profile_data, ensure_ascii=False)

    context = {
        'user_nom': request.session.get('user_nom'),
        'user_prenom': request.session.get('user_prenom', ''),
        'user_role': request.session.get('user_role'),
        'personne': personne,
        'utilisateur': utilisateur,
        'personnel': personnel,
        'profile_data': profile_data_json,
        'page_title': 'Mon profil - CS KABA'
    }
    return render(request, 'Cote/enseignant/mon_profil.html', context)


def saisir_cotes(request):
    """Vue principale pour la saisie des cotes (enseignant connecté)."""
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'ENSEIGNANT':
        messages.error(request, 'Accès non autorisé')
        return redirect('dashboard')

    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    context = {
        'user_nom': request.session.get('user_nom'),
        'page_title': 'Saisir cotes - CS KABA',
        'annee_active_id': annee_active.id if annee_active else None,
    }
    return render(request, 'Cote/enseignant/saisir_cotes.html', context)


@require_http_methods(["GET"])
def api_enseignant_annees(request):
    """Retourne les années scolaires pour lesquelles l'enseignant a des attributions, plus l'année active s'il est titulaire."""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
    except Personnel.DoesNotExist:
        return JsonResponse({'error': 'Personnel non trouvé'}, status=404)

    # Récupérer les années où il a des attributions
    annees_attrib = AnneeScolaire.objects.filter(
        attributioncours__id_personnel=personnel,
        attributioncours__est_active=True
    ).distinct()

    # Si l'utilisateur est titulaire, ajouter l'année active si elle n'y est pas
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    if annee_active and not annees_attrib.filter(id=annee_active.id).exists():
        est_titulaire = TitulaireClasse.objects.filter(
            id_personnel=personnel,
            id_annee=annee_active,
            est_actif=True
        ).exists()
        if est_titulaire:
            # Ajouter l'année active à la liste
            annees_attrib = annees_attrib | AnneeScolaire.objects.filter(id=annee_active.id)

    data = [{'id': a.id, 'annee_scolaire': a.annee_scolaire} for a in annees_attrib.order_by('-date_debut')]
    return JsonResponse({'annees': data})


@require_http_methods(["GET"])
def api_enseignant_classes(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    annee_id = request.GET.get('annee_id')
    if not annee_id:
        return JsonResponse({'error': 'annee_id requis'}, status=400)
    
    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
    except Personnel.DoesNotExist:
        return JsonResponse({'error': 'Personnel non trouvé'}, status=404)
    
    classes = Classe.objects.filter(
        attributioncours__id_personnel=personnel,
        attributioncours__id_annee_id=annee_id,
        attributioncours__est_active=True
    ).distinct().order_by('nom_classe')
    
    data = [{'id': c.id, 'nom_classe': c.nom_classe} for c in classes]
    return JsonResponse({'classes': data})


@require_http_methods(["GET"])
def api_enseignant_cours(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    annee_id = request.GET.get('annee_id')
    classe_id = request.GET.get('classe_id')
    if not annee_id or not classe_id:
        return JsonResponse({'error': 'annee_id et classe_id requis'}, status=400)
    
    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
    except Personnel.DoesNotExist:
        return JsonResponse({'error': 'Personnel non trouvé'}, status=404)
    
    cours = Cours.objects.filter(
        attributioncours__id_personnel=personnel,
        attributioncours__id_annee_id=annee_id,
        attributioncours__id_classe_id=classe_id,
        attributioncours__est_active=True
    ).distinct()
    
    data = [{
        'id': c.id,
        'nom_cours': c.nom_cours,
        'coefficient': c.coefficient,
        'points_par_periode': c.points_par_periode
    } for c in cours]
    return JsonResponse({'cours': data})


@require_http_methods(["GET"])
def api_enseignant_eleves_cotes(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    annee_id = request.GET.get('annee_id')
    classe_id = request.GET.get('classe_id')
    cours_id = request.GET.get('cours_id')
    if not all([annee_id, classe_id, cours_id]):
        return JsonResponse({'error': 'Paramètres manquants'}, status=400)
    
    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
    except Personnel.DoesNotExist:
        return JsonResponse({'error': 'Personnel non trouvé'}, status=404)
    
    # Vérifier que l'enseignant a bien le droit d'accéder à ce cours dans cette classe
    if not AttributionCours.objects.filter(
        id_personnel=personnel,
        id_annee_id=annee_id,
        id_classe_id=classe_id,
        id_cours_id=cours_id,
        est_active=True
    ).exists():
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    cours = get_object_or_404(Cours, id=cours_id)
    max_periode = cours.points_par_periode
    max_examen = max_periode * 2
    
    inscriptions = Inscription.objects.filter(
        id_classe_id=classe_id,
        id_annee_id=annee_id,
        est_active=True
    ).select_related('id_eleve__id_personne')
    
    eleves_data = []
    for ins in inscriptions:
        eleve = ins.id_eleve
        cote = Cote.objects.filter(
            eleve=eleve,
            cours_id=cours_id,
            annee_scolaire_id=annee_id,
            classe_id=classe_id,
            enseignant=personnel
        ).first()
        
        total_s1 = None
        total_s2 = None
        total_general = None
        pourcentage = None
        observation = None
        if cote:
            total_s1 = float(cote.total_semestre_1) if cote.total_semestre_1 is not None else None
            total_s2 = float(cote.total_semestre_2) if cote.total_semestre_2 is not None else None
            total_general = float(cote.total_general) if cote.total_general is not None else None
            pourcentage = float(cote.pourcentage) if cote.pourcentage is not None else None
            observation = cote.observation
        
        eleves_data.append({
            'id': eleve.id,
            'nom': eleve.id_personne.nom,
            'prenom': eleve.id_personne.prenom,
            'matricule': eleve.matricule,
            'cote': {
                'cote_p1': float(cote.cote_p1) if cote and cote.cote_p1 is not None else None,
                'cote_p2': float(cote.cote_p2) if cote and cote.cote_p2 is not None else None,
                'cote_p3': float(cote.cote_p3) if cote and cote.cote_p3 is not None else None,
                'cote_p4': float(cote.cote_p4) if cote and cote.cote_p4 is not None else None,
                'examen_semestre_1': float(cote.examen_semestre_1) if cote and cote.examen_semestre_1 is not None else None,
                'examen_semestre_2': float(cote.examen_semestre_2) if cote and cote.examen_semestre_2 is not None else None,
                'total_semestre_1': total_s1,
                'total_semestre_2': total_s2,
                'total_general': total_general,
                'pourcentage': pourcentage,
                'observation': observation,
            } if cote else {},
            'max_periode': max_periode,
            'max_examen': max_examen
        })
    return JsonResponse({'eleves': eleves_data})


@csrf_exempt
@require_http_methods(["POST"])
def api_sauvegarder_cotes(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    
    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
    except Personnel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Personnel non trouvé'}, status=404)
    
    data = json.loads(request.body)
    annee_id = data.get('annee_id')
    classe_id = data.get('classe_id')
    cours_id = data.get('cours_id')
    cotes_dict = data.get('cotes', {})
    
    # Vérification des droits
    if not AttributionCours.objects.filter(
        id_personnel=personnel,
        id_annee_id=annee_id,
        id_classe_id=classe_id,
        id_cours_id=cours_id,
        est_active=True
    ).exists():
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
    
    cours = get_object_or_404(Cours, id=cours_id)
    max_periode = cours.points_par_periode
    max_examen = max_periode * 2
    
    try:
        with transaction.atomic():
            for eleve_id_str, fields in cotes_dict.items():
                eleve_id = int(eleve_id_str)
                eleve = Eleve.objects.get(id=eleve_id)
                
                # Validation des notes par rapport aux maxima
                for key, max_val in [('p1', max_periode), ('p2', max_periode),
                                     ('p3', max_periode), ('p4', max_periode),
                                     ('examen1', max_examen), ('examen2', max_examen)]:
                    val = fields.get(key)
                    if val is not None:
                        if val == '':
                            fields[key] = None
                        else:
                            try:
                                numeric_val = float(val)
                                if numeric_val < 0 or numeric_val > max_val:
                                    return JsonResponse({
                                        'success': False,
                                        'error': f"Note {key} invalide pour l'élève {eleve_id}. Doit être entre 0 et {max_val}."
                                    })
                                fields[key] = numeric_val
                            except (TypeError, ValueError):
                                return JsonResponse({
                                    'success': False,
                                    'error': f"Valeur non numérique pour le champ {key} de l'élève {eleve_id}."
                                })
                
                Cote.objects.update_or_create(
                    eleve=eleve,
                    cours_id=cours_id,
                    annee_scolaire_id=annee_id,
                    classe_id=classe_id,
                    enseignant=personnel,
                    defaults={
                        'cote_p1': fields.get('p1'),
                        'cote_p2': fields.get('p2'),
                        'cote_p3': fields.get('p3'),
                        'cote_p4': fields.get('p4'),
                        'examen_semestre_1': fields.get('examen1'),
                        'examen_semestre_2': fields.get('examen2'),
                    }
                )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =====================================================
# BULLETIN ÉLÈVE (adapté pour utiliser Cote au lieu de Note)
# =====================================================
def bulletin_eleve(request, eleve_id, annee_id=None):
    """
    Affiche le bulletin d'un élève pour une année scolaire donnée.
    Utilise les données de la table Cote (système de points).
    Calcule également le rang de l'élève dans sa classe.
    """
    eleve = get_object_or_404(Eleve, id=eleve_id, est_actif=True)
    
    if annee_id:
        annee = get_object_or_404(AnneeScolaire, id=annee_id)
    else:
        annee = AnneeScolaire.objects.filter(est_active=True).first()
        if not annee:
            annee = AnneeScolaire.objects.order_by('-date_debut').first()
    
    inscription = get_object_or_404(Inscription, id_eleve=eleve, id_annee=annee, est_active=True)
    classe = inscription.id_classe
    
    attributions = AttributionCours.objects.filter(
        id_classe=classe,
        id_annee=annee,
        est_active=True
    ).select_related('id_cours').order_by('id_cours__nom_cours')
    
    inscriptions_classe = Inscription.objects.filter(
        id_classe=classe,
        id_annee=annee,
        est_active=True
    ).select_related('id_eleve')
    
    # Calcul du rang
    eleves_totaux = []
    for ins in inscriptions_classe:
        eleve_courant = ins.id_eleve
        total = 0
        for att in attributions:
            cours = att.id_cours
            cote = Cote.objects.filter(
                eleve=eleve_courant,
                cours=cours,
                annee_scolaire=annee,
                classe=classe
            ).first()
            if cote:
                if cote.cote_p1 is not None: total += cote.cote_p1
                if cote.cote_p2 is not None: total += cote.cote_p2
                if cote.examen_semestre_1 is not None: total += cote.examen_semestre_1
                if cote.cote_p3 is not None: total += cote.cote_p3
                if cote.cote_p4 is not None: total += cote.cote_p4
                if cote.examen_semestre_2 is not None: total += cote.examen_semestre_2
        eleves_totaux.append((eleve_courant.id, total))
    
    eleves_totaux.sort(key=lambda x: x[1], reverse=True)
    rang = None
    for idx, (eid, _) in enumerate(eleves_totaux):
        if eid == eleve.id:
            rang = idx + 1
            break
    
    # Construction des données pour l'élève courant
    bulletin_data = []
    total_general_eleve = 0
    max_possible_total = 0
    
    totals = {
        'p1': 0, 'max_p1': 0,
        'p2': 0, 'max_p2': 0,
        'ex1': 0, 'max_ex1': 0,
        'p3': 0, 'max_p3': 0,
        'p4': 0, 'max_p4': 0,
        'ex2': 0, 'max_ex2': 0,
        's1': 0, 'max_s1': 0,
        's2': 0, 'max_s2': 0,
    }
    
    for att in attributions:
        cours = att.id_cours
        points = cours.points_par_periode
        max_possible_total += points * 8
        
        cote = Cote.objects.filter(
            eleve=eleve,
            cours=cours,
            annee_scolaire=annee,
            classe=classe
        ).first()
        
        if cote:
            p1 = cote.cote_p1 if cote.cote_p1 is not None else 0
            p2 = cote.cote_p2 if cote.cote_p2 is not None else 0
            ex1 = cote.examen_semestre_1 if cote.examen_semestre_1 is not None else 0
            p3 = cote.cote_p3 if cote.cote_p3 is not None else 0
            p4 = cote.cote_p4 if cote.cote_p4 is not None else 0
            ex2 = cote.examen_semestre_2 if cote.examen_semestre_2 is not None else 0
            p1_disp = cote.cote_p1
            p2_disp = cote.cote_p2
            ex1_disp = cote.examen_semestre_1
            p3_disp = cote.cote_p3
            p4_disp = cote.cote_p4
            ex2_disp = cote.examen_semestre_2
        else:
            p1 = p2 = ex1 = p3 = p4 = ex2 = 0
            p1_disp = p2_disp = ex1_disp = p3_disp = p4_disp = ex2_disp = None
        
        tot1 = p1 + p2 + ex1
        tot2 = p3 + p4 + ex2
        total_general_cours = tot1 + tot2
        
        totals['s1'] += tot1
        totals['max_s1'] += points * 4
        totals['s2'] += tot2
        totals['max_s2'] += points * 4
        
        if p1_disp is not None:
            totals['p1'] += p1_disp
            totals['max_p1'] += points
        if p2_disp is not None:
            totals['p2'] += p2_disp
            totals['max_p2'] += points
        if ex1_disp is not None:
            totals['ex1'] += ex1_disp
            totals['max_ex1'] += points * 2
        if p3_disp is not None:
            totals['p3'] += p3_disp
            totals['max_p3'] += points
        if p4_disp is not None:
            totals['p4'] += p4_disp
            totals['max_p4'] += points
        if ex2_disp is not None:
            totals['ex2'] += ex2_disp
            totals['max_ex2'] += points * 2
        
        total_general_eleve += total_general_cours
        
        bulletin_data.append({
            'cours': cours,
            'p1': p1_disp, 'p2': p2_disp, 'ex1': ex1_disp, 'tot1': tot1,
            'p3': p3_disp, 'p4': p4_disp, 'ex2': ex2_disp, 'tot2': tot2,
            'total_general': total_general_cours,
            'pourcentage': cote.pourcentage if cote else None,
            'observation': cote.observation if cote else None,
            'points_par_periode': points,
        })
    
    totaux_obtenus = {
        'p1': totals['p1'],
        'p2': totals['p2'],
        'ex1': totals['ex1'],
        'p3': totals['p3'],
        'p4': totals['p4'],
        'ex2': totals['ex2'],
    }
    
    total_s1_eleve = totals['s1']
    total_s2_eleve = totals['s2']
    
    pourcentages = {
        'p1': (totals['p1'] / totals['max_p1'] * 100) if totals['max_p1'] > 0 else 0,
        'p2': (totals['p2'] / totals['max_p2'] * 100) if totals['max_p2'] > 0 else 0,
        'ex1': (totals['ex1'] / totals['max_ex1'] * 100) if totals['max_ex1'] > 0 else 0,
        'p3': (totals['p3'] / totals['max_p3'] * 100) if totals['max_p3'] > 0 else 0,
        'p4': (totals['p4'] / totals['max_p4'] * 100) if totals['max_p4'] > 0 else 0,
        'ex2': (totals['ex2'] / totals['max_ex2'] * 100) if totals['max_ex2'] > 0 else 0,
        's1': (totals['s1'] / totals['max_s1'] * 100) if totals['max_s1'] > 0 else 0,
        's2': (totals['s2'] / totals['max_s2'] * 100) if totals['max_s2'] > 0 else 0,
    }
    
    pourcentage_general = (total_general_eleve / max_possible_total * 100) if max_possible_total > 0 else 0
    
    context = {
        'eleve': eleve,
        'personne': eleve.id_personne,
        'classe': classe,
        'annee': annee,
        'bulletin_data': bulletin_data,
        'total_general_eleve': total_general_eleve,
        'total_s1_eleve': total_s1_eleve,
        'total_s2_eleve': total_s2_eleve,
        'pourcentage_general': round(pourcentage_general, 2),
        'max_possible_total': max_possible_total,
        'pourcentages': pourcentages,
        'totaux_obtenus': totaux_obtenus,
        'rang': rang,
        'nombre_eleves_classe': inscriptions_classe.count(),
        'page_title': f'Bulletin de {eleve.id_personne.nom} {eleve.id_personne.prenom}',
    }
    return render(request, 'Cote/bulletin.html', context)


# =====================================================
# VUES TITULAIRE : VÉRIFICATION DES COTES
# =====================================================

def verifier_cotes_titulaire_test(request):
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')
    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
        annee_active = AnneeScolaire.objects.filter(est_active=True).first()
        if annee_active:
            titulaire = TitulaireClasse.objects.filter(id_personnel=personnel, id_annee=annee_active, est_actif=True).first()
            if titulaire:
                context = {'user_nom': request.session.get('user_nom'), 'page_title': 'Vérifier les cotes - CS KABA'}
                return render(request, 'Cote/enseignant/verifier_cote.html', context)
            else:
                return HttpResponse(f"Pas titulaire pour {annee_active.annee_scolaire}")
        else:
            return HttpResponse("Pas d'année active")
    except Exception as e:
        return HttpResponse(f"Erreur : {str(e)}")


@require_http_methods(["GET"])
def api_titulaire_classe(request):
    """Retourne la classe dont l'utilisateur est titulaire pour l'année active."""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Non authentifié'}, status=401)

    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
    except Personnel.DoesNotExist:
        return JsonResponse({'error': 'Personnel non trouvé'}, status=404)

    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    if not annee_active:
        return JsonResponse({'error': 'Aucune année scolaire active'}, status=400)

    titulariat = TitulaireClasse.objects.filter(
        id_personnel=personnel,
        id_annee=annee_active,
        est_actif=True
    ).select_related('id_classe').first()

    if not titulariat:
        return JsonResponse({'error': 'Vous n\'êtes titulaire d\'aucune classe cette année'}, status=404)

    classe = titulariat.id_classe
    return JsonResponse({
        'success': True,
        'classe': {
            'id': classe.id,
            'nom': classe.nom_classe,
            'est_cycle_orientation': classe.est_cycle_orientation,
        }
    })


@require_http_methods(["GET"])
def api_titulaire_cotes_eleves(request):
    """Retourne la liste des élèves de la classe du titulaire avec toutes leurs cotes."""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Non authentifié'}, status=401)

    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
    except Personnel.DoesNotExist:
        return JsonResponse({'error': 'Personnel non trouvé'}, status=404)

    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    if not annee_active:
        return JsonResponse({'error': 'Aucune année scolaire active'}, status=400)

    titulariat = TitulaireClasse.objects.filter(
        id_personnel=personnel,
        id_annee=annee_active,
        est_actif=True
    ).select_related('id_classe').first()

    if not titulariat:
        return JsonResponse({'error': 'Vous n\'êtes titulaire d\'aucune classe'}, status=404)

    classe = titulariat.id_classe

    # Tous les élèves inscrits dans cette classe pour l'année active
    inscriptions = Inscription.objects.filter(
        id_classe=classe,
        id_annee=annee_active,
        est_active=True
    ).select_related('id_eleve__id_personne').order_by('id_eleve__id_personne__nom', 'id_eleve__id_personne__prenom')

    # TOUS les cours attribués à cette classe cette année (peu importe l'enseignant)
    attributions = AttributionCours.objects.filter(
        id_classe=classe,
        id_annee=annee_active,
        est_active=True
    ).select_related('id_cours').order_by('id_cours__nom_cours')

    # Structure de réponse
    data = {
        'classe': {
            'id': classe.id,
            'nom': classe.nom_classe,
        },
        'cours': [{'id': att.id_cours.id, 'nom': att.id_cours.nom_cours} for att in attributions],
        'eleves': []
    }

    for ins in inscriptions:
        eleve = ins.id_eleve
        eleve_data = {
            'id': eleve.id,
            'nom': eleve.id_personne.nom,
            'prenom': eleve.id_personne.prenom,
            'matricule': eleve.matricule,
            'cotes': []
        }
        for att in attributions:
            cours = att.id_cours
            cote = Cote.objects.filter(
                eleve=eleve,
                cours=cours,
                annee_scolaire=annee_active,
                classe=classe
            ).first()
            if cote:
                eleve_data['cotes'].append({
                    'cours_id': cours.id,
                    'cote_id': cote.id,
                    'validee': cote.validee_titulaire,
                    'p1': float(cote.cote_p1) if cote.cote_p1 is not None else None,
                    'p2': float(cote.cote_p2) if cote.cote_p2 is not None else None,
                    'ex1': float(cote.examen_semestre_1) if cote.examen_semestre_1 is not None else None,
                    'p3': float(cote.cote_p3) if cote.cote_p3 is not None else None,
                    'p4': float(cote.cote_p4) if cote.cote_p4 is not None else None,
                    'ex2': float(cote.examen_semestre_2) if cote.examen_semestre_2 is not None else None,
                    'total_general': float(cote.total_general) if cote.total_general is not None else None,
                    'pourcentage': float(cote.pourcentage) if cote.pourcentage is not None else None,
                })
            else:
                eleve_data['cotes'].append({
                    'cours_id': cours.id,
                    'cote_id': None,
                    'validee': False,
                })
        data['eleves'].append(eleve_data)

    return JsonResponse({'success': True, 'data': data})


@csrf_exempt
@require_http_methods(["POST"])
def api_titulaire_valider_cote(request):
    """Valide/dévalide une cote spécifique (par son ID)."""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

    try:
        data = json.loads(request.body)
        cote_id = data.get('cote_id')
        if not cote_id:
            return JsonResponse({'success': False, 'error': 'ID de cote manquant'}, status=400)

        cote = Cote.objects.select_related('classe', 'annee_scolaire').get(id=cote_id)

        # Vérifier que l'utilisateur est bien titulaire de cette classe pour cette année
        try:
            personnel = Personnel.objects.get(id_utilisateur_id=user_id)
        except Personnel.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Personnel non trouvé'}, status=404)

        est_titulaire = TitulaireClasse.objects.filter(
            id_personnel=personnel,
            id_classe=cote.classe,
            id_annee=cote.annee_scolaire,
            est_actif=True
        ).exists()

        if not est_titulaire:
            return JsonResponse({'success': False, 'error': 'Vous n\'êtes pas titulaire de cette classe pour cette année'}, status=403)

        cote.validee_titulaire = not cote.validee_titulaire
        cote.save()

        return JsonResponse({'success': True, 'validee': cote.validee_titulaire})
    except Cote.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cote introuvable'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def verifier_cotes_titulaire(request):
    print("Session user_id:", request.session.get('user_id'))
    if not request.session.get('user_id'):
        print("Pas de user_id en session, redirection vers login")
        return redirect('login')
    print("User_id trouvé, affichage du template")
    context = {
        'user_nom': request.session.get('user_nom'),
        'page_title': 'Vérifier les cotes - CS KABA',
    }
    return render(request, 'Cote/enseignant/verifier_cote.html', context)

    
def liste_cours_enseignant(request):
    """Affiche la page de sélection pour la liste imprimable des cotes par cours."""
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'ENSEIGNANT':
        messages.error(request, 'Accès non autorisé')
        return redirect('dashboard')
    
    context = {
        'user_nom': request.session.get('user_nom'),
        'page_title': 'Liste des cotes par cours - CS KABA'
    }
    return render(request, 'Cote/enseignant/liste_cours.html', context)


@require_http_methods(["GET"])
def api_enseignant_liste_cotes(request):
    """Retourne les cotes détaillées pour un enseignant, une année, une classe et un cours donnés."""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    
    annee_id = request.GET.get('annee_id')
    classe_id = request.GET.get('classe_id')
    cours_id = request.GET.get('cours_id')
    
    if not all([annee_id, classe_id, cours_id]):
        return JsonResponse({'success': False, 'error': 'Paramètres manquants'}, status=400)
    
    try:
        personnel = Personnel.objects.get(id_utilisateur_id=user_id)
    except Personnel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Personnel non trouvé'}, status=404)
    
    # Vérifier que l'enseignant a bien ce cours dans cette classe cette année
    if not AttributionCours.objects.filter(
        id_personnel=personnel,
        id_annee_id=annee_id,
        id_classe_id=classe_id,
        id_cours_id=cours_id,
        est_active=True
    ).exists():
        return JsonResponse({'success': False, 'error': 'Vous n\'êtes pas autorisé pour ce cours dans cette classe.'}, status=403)
    
    cours = get_object_or_404(Cours, id=cours_id)
    inscriptions = Inscription.objects.filter(
        id_classe_id=classe_id,
        id_annee_id=annee_id,
        est_active=True
    ).select_related('id_eleve__id_personne').order_by('id_eleve__id_personne__nom', 'id_eleve__id_personne__prenom')
    
    eleves_data = []
    for ins in inscriptions:
        eleve = ins.id_eleve
        cote = Cote.objects.filter(
            eleve=eleve,
            cours_id=cours_id,
            annee_scolaire_id=annee_id,
            classe_id=classe_id,
            enseignant=personnel
        ).first()
        
        if cote:
            eleves_data.append({
                'nom': eleve.id_personne.nom,
                'prenom': eleve.id_personne.prenom,
                'matricule': eleve.matricule,
                'cote': {
                    'p1': float(cote.cote_p1) if cote.cote_p1 is not None else None,
                    'p2': float(cote.cote_p2) if cote.cote_p2 is not None else None,
                    'ex1': float(cote.examen_semestre_1) if cote.examen_semestre_1 is not None else None,
                    'total_s1': float(cote.total_semestre_1) if cote.total_semestre_1 is not None else None,
                    'p3': float(cote.cote_p3) if cote.cote_p3 is not None else None,
                    'p4': float(cote.cote_p4) if cote.cote_p4 is not None else None,
                    'ex2': float(cote.examen_semestre_2) if cote.examen_semestre_2 is not None else None,
                    'total_s2': float(cote.total_semestre_2) if cote.total_semestre_2 is not None else None,
                    'total_general': float(cote.total_general) if cote.total_general is not None else None,
                    'pourcentage': float(cote.pourcentage) if cote.pourcentage is not None else None,
                }
            })
        else:
            eleves_data.append({
                'nom': eleve.id_personne.nom,
                'prenom': eleve.id_personne.prenom,
                'matricule': eleve.matricule,
                'cote': None
            })
    
    return JsonResponse({
        'success': True,
        'data': {
            'eleves': eleves_data,
            'cours_nom': cours.nom_cours,
            'points_par_periode': cours.points_par_periode,
        }
    })


# =====================================================
# PROFIL ADMIN (DIRECTEUR DES ÉTUDES)
# =====================================================

def profil_admin(request):
    """
    Affiche et traite le profil du Directeur des Études.
    Gère : upload photo, mise à jour coordonnées, changement mot de passe.
    """
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('dashboard_de')

    user_id = request.session.get('user_id')
    try:
        utilisateur = Utilisateur.objects.select_related('id_personne').get(id=user_id)
        personnel = Personnel.objects.get(id_utilisateur=utilisateur)
        personne = utilisateur.id_personne
    except (Utilisateur.DoesNotExist, Personnel.DoesNotExist):
        messages.error(request, 'Profil introuvable')
        return redirect('dashboard_de')

    # Statistiques (exemple : nombre d'élèves, d'enseignants, etc.)
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    total_eleves = Inscription.objects.filter(id_annee=annee_active, est_active=True).count() if annee_active else 0
    total_enseignants = Personnel.objects.count()
    total_classes = Classe.objects.filter(actif=True).count()

    # Traitement du formulaire
    if request.method == 'POST':
        # Upload photo
        if 'profile_photo' in request.FILES:
            photo = request.FILES['profile_photo']
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if photo.content_type not in allowed_types:
                messages.error(request, 'Format de photo non autorisé (JPEG, PNG, GIF, WEBP)')
            elif photo.size > 5 * 1024 * 1024:
                messages.error(request, 'La photo ne doit pas dépasser 5 Mo')
            else:
                # Supprimer l'ancienne photo si elle existe
                if personne.photo:
                    old_path = personne.photo.path
                    if os.path.isfile(old_path):
                        os.remove(old_path)
                # Sauvegarder la nouvelle
                personne.photo.save(f'admin_{utilisateur.id}.jpg', photo)
                messages.success(request, 'Photo de profil mise à jour avec succès')
            return redirect('profil_admin')

        # Modification coordonnées
        elif 'action' in request.POST and request.POST['action'] == 'update_coords':
            telephone = request.POST.get('telephone', '').strip()
            email = request.POST.get('email', '').strip()
            adresse = request.POST.get('adresse', '').strip()

            errors = []
            # Vérifier unicité téléphone
            if telephone:
                if Personne.objects.filter(telephone=telephone).exclude(id=personne.id).exists():
                    errors.append("Ce numéro de téléphone est déjà utilisé.")
            # Vérifier unicité email
            if email:
                if Personne.objects.filter(email=email).exclude(id=personne.id).exists():
                    errors.append("Cette adresse email est déjà utilisée.")
                elif not re.match(r'^[^\s@]+@([^\s@]+\.)+[^\s@]+$', email):
                    errors.append("Format d'email invalide.")

            if errors:
                for err in errors:
                    messages.error(request, err)
            else:
                personne.telephone = telephone
                personne.email = email
                personne.adresse = adresse
                personne.save()
                # Mettre à jour l'email de connexion si changé
                if email and utilisateur.email != email:
                    utilisateur.email = email
                    utilisateur.save()
                messages.success(request, 'Coordonnées mises à jour avec succès')
            return redirect('profil_admin')

        # Changement mot de passe
        elif 'action' in request.POST and request.POST['action'] == 'change_password':
            old_password = request.POST.get('old_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            errors = []
            if not old_password:
                errors.append("Veuillez saisir votre mot de passe actuel.")
            if not new_password:
                errors.append("Veuillez saisir un nouveau mot de passe.")
            if new_password != confirm_password:
                errors.append("Les nouveaux mots de passe ne correspondent pas.")
            if len(new_password) < 6:
                errors.append("Le nouveau mot de passe doit contenir au moins 6 caractères.")

            if not utilisateur.check_password(old_password):
                errors.append("Mot de passe actuel incorrect.")

            if errors:
                for err in errors:
                    messages.error(request, err)
            else:
                utilisateur.set_password(new_password)
                utilisateur.save()
                messages.success(request, 'Mot de passe changé avec succès. Utilisez-le pour vos prochaines connexions.')
            return redirect('profil_admin')

    # Construction de la photo de profil
    photo_url = personne.photo.url if personne.photo else None
    if not photo_url:
        photo_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234b5563'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/%3E%3C/svg%3E"

    cover_url = "/static/images/default-cover.jpg"

    context = {
        'user_nom': request.session.get('user_nom'),
        'user_role': 'DE',
        'personne': personne,
        'utilisateur': utilisateur,
        'personnel': personnel,
        'photo_url': photo_url,
        'cover_url': cover_url,
        'total_eleves': total_eleves,
        'total_enseignants': total_enseignants,
        'total_classes': total_classes,
        'annee_active': annee_active,
        'page_title': 'Mon profil - Directeur des Études'
    }
    return render(request, 'Cote/admin/profil.html', context)


# =====================================================
# PROFIL ENSEIGNANT
# =====================================================

def profil_enseignant(request):
    """
    Affiche et traite le profil de l'enseignant connecté.
    Gère : upload photo, mise à jour coordonnées, changement mot de passe.
    """
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('user_role') != 'ENSEIGNANT':
        messages.error(request, 'Accès non autorisé')
        return redirect('dashboard_enseignant')

    user_id = request.session.get('user_id')
    try:
        utilisateur = Utilisateur.objects.select_related('id_personne').get(id=user_id)
        personnel = Personnel.objects.get(id_utilisateur=utilisateur)
        personne = utilisateur.id_personne
    except (Utilisateur.DoesNotExist, Personnel.DoesNotExist):
        messages.error(request, 'Profil introuvable')
        return redirect('dashboard_enseignant')

    # Statistiques pour l'enseignant
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    if annee_active:
        attributions = AttributionCours.objects.filter(id_personnel=personnel, id_annee=annee_active, est_active=True)
        total_cours = attributions.count()
        total_classes = attributions.values('id_classe').distinct().count()
        classes_ids = attributions.values_list('id_classe', flat=True).distinct()
        total_eleves = Inscription.objects.filter(id_classe__in=classes_ids, id_annee=annee_active, est_active=True).count()
    else:
        total_cours = total_classes = total_eleves = 0

    # Traitement des formulaires
    if request.method == 'POST':
        # Upload photo
        if 'profile_photo' in request.FILES:
            photo = request.FILES['profile_photo']
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if photo.content_type not in allowed_types:
                messages.error(request, 'Format de photo non autorisé (JPEG, PNG, GIF, WEBP)')
            elif photo.size > 5 * 1024 * 1024:
                messages.error(request, 'La photo ne doit pas dépasser 5 Mo')
            else:
                if personne.photo:
                    old_path = personne.photo.path
                    if os.path.isfile(old_path):
                        os.remove(old_path)
                personne.photo.save(f'enseignant_{utilisateur.id}.jpg', photo)
                messages.success(request, 'Photo de profil mise à jour avec succès')
            return redirect('profil_enseignant')

        # Modification coordonnées
        elif 'action' in request.POST and request.POST['action'] == 'update_coords':
            telephone = request.POST.get('telephone', '').strip()
            email = request.POST.get('email', '').strip()
            adresse = request.POST.get('adresse', '').strip()

            errors = []
            if telephone and Personne.objects.filter(telephone=telephone).exclude(id=personne.id).exists():
                errors.append("Ce numéro de téléphone est déjà utilisé.")
            if email:
                if Personne.objects.filter(email=email).exclude(id=personne.id).exists():
                    errors.append("Cette adresse email est déjà utilisée.")
                elif not re.match(r'^[^\s@]+@([^\s@]+\.)+[^\s@]+$', email):
                    errors.append("Format d'email invalide.")

            if errors:
                for err in errors:
                    messages.error(request, err)
            else:
                personne.telephone = telephone
                personne.email = email
                personne.adresse = adresse
                personne.save()
                if email and utilisateur.email != email:
                    utilisateur.email = email
                    utilisateur.save()
                messages.success(request, 'Coordonnées mises à jour avec succès')
            return redirect('profil_enseignant')

        # Changement mot de passe
        elif 'action' in request.POST and request.POST['action'] == 'change_password':
            old_password = request.POST.get('old_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            errors = []
            if not old_password:
                errors.append("Veuillez saisir votre mot de passe actuel.")
            if not new_password:
                errors.append("Veuillez saisir un nouveau mot de passe.")
            if new_password != confirm_password:
                errors.append("Les nouveaux mots de passe ne correspondent pas.")
            if len(new_password) < 6:
                errors.append("Le nouveau mot de passe doit contenir au moins 6 caractères.")

            if not utilisateur.check_password(old_password):
                errors.append("Mot de passe actuel incorrect.")

            if errors:
                for err in errors:
                    messages.error(request, err)
            else:
                utilisateur.set_password(new_password)
                utilisateur.save()
                messages.success(request, 'Mot de passe changé avec succès. Utilisez-le pour vos prochaines connexions.')
            return redirect('profil_enseignant')

    # Construction de la photo de profil
    photo_url = personne.photo.url if personne.photo else None
    if not photo_url:
        photo_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234b5563'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/%3E%3C/svg%3E"

    cover_url = "/static/images/default-cover.jpg"

    context = {
        'user_nom': request.session.get('user_nom'),
        'user_role': 'ENSEIGNANT',
        'personne': personne,
        'utilisateur': utilisateur,
        'personnel': personnel,
        'photo_url': photo_url,
        'cover_url': cover_url,
        'total_cours': total_cours,
        'total_classes': total_classes,
        'total_eleves': total_eleves,
        'annee_active': annee_active,
        'page_title': 'Mon profil - Enseignant'
    }
    return render(request, 'Cote/enseignant/profil.html', context)


# =====================================================
# 4. GESTION DES CLASSES ET OPTIONS (page + API) - SUITE
# =====================================================

@csrf_exempt
@csrf_exempt
@csrf_exempt
def ajouter_classe(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.session.get('user_role') != 'DE':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

    if request.method == 'POST':
        try:
            classe_id = request.POST.get('classe_id')
            nom_classe = request.POST.get('nom_classe', '').strip()
            cycle = request.POST.get('cycle', '')
            annee = request.POST.get('annee', '').strip()
            division = request.POST.get('division', '').strip()
            id_option = request.POST.get('id_option')
            capacite_max = request.POST.get('capacite_max', 30)
            actif = request.POST.get('actif') == 'on'

            est_cycle_orientation = (cycle == 'CO')

            # Génération du nom si non fourni
            if not nom_classe and annee and division:
                if est_cycle_orientation:
                    nom_classe = f"{annee}e{division}"
                else:
                    suffix = {1: 'ère', 2: 'ème', 3: 'ème', 4: 'ème'}
                    annee_int = int(annee)
                    nom_classe = f"{annee_int}{suffix.get(annee_int, 'ème')}{division}"

            if not nom_classe:
                return JsonResponse({'success': False, 'error': 'Nom de classe manquant'})

            if classe_id:
                # Modification
                try:
                    classe = Classe.objects.get(id=classe_id)
                except Classe.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Classe non trouvée'})

                if not est_cycle_orientation and id_option:
                    if Classe.objects.filter(nom_classe=nom_classe, id_option_id=id_option).exclude(id=classe_id).exists():
                        return JsonResponse({'success': False, 'error': f'Une classe "{nom_classe}" avec cette option existe déjà'})
                else:
                    if Classe.objects.filter(nom_classe=nom_classe).exclude(id=classe_id).exists():
                        return JsonResponse({'success': False, 'error': f'Une classe "{nom_classe}" existe déjà'})

                classe.nom_classe = nom_classe
                classe.est_cycle_orientation = est_cycle_orientation
                classe.capacite_max = capacite_max
                classe.actif = actif

                if not est_cycle_orientation and id_option:
                    try:
                        classe.id_option = OptionEtude.objects.get(id=id_option)
                    except OptionEtude.DoesNotExist:
                        return JsonResponse({'success': False, 'error': 'Option non trouvée'})
                else:
                    classe.id_option = None

                classe.save()
                return JsonResponse({'success': True, 'message': f'Classe {nom_classe} modifiée avec succès'})
            else:
                # Création
                if not est_cycle_orientation and id_option:
                    if Classe.objects.filter(nom_classe=nom_classe, id_option_id=id_option).exists():
                        return JsonResponse({'success': False, 'error': f'Une classe "{nom_classe}" avec cette option existe déjà'})
                else:
                    if Classe.objects.filter(nom_classe=nom_classe).exists():
                        return JsonResponse({'success': False, 'error': f'Une classe "{nom_classe}" existe déjà'})

                classe = Classe.objects.create(
                    nom_classe=nom_classe,
                    est_cycle_orientation=est_cycle_orientation,
                    capacite_max=capacite_max,
                    actif=actif
                )

                if not est_cycle_orientation and id_option:
                    try:
                        classe.id_option = OptionEtude.objects.get(id=id_option)
                        classe.save()
                    except OptionEtude.DoesNotExist:
                        pass

                return JsonResponse({'success': True, 'message': f'Classe {nom_classe} ajoutée avec succès'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


def get_classe(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    try:
        classe = Classe.objects.get(id=id)
        return JsonResponse({'success': True, 'classe': {
            'id': classe.id, 'nom_classe': classe.nom_classe, 'niveau': classe.niveau,
            'id_option': classe.id_option.id if classe.id_option else None,
            'capacite_max': classe.capacite_max, 'est_cycle_orientation': classe.est_cycle_orientation,
            'actif': classe.actif
        }})
    except Classe.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Classe non trouvée'})


@csrf_exempt
def supprimer_classe(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    try:
        classe = Classe.objects.get(id=id)
        nom = classe.nom_classe

        # Supprimer les inscriptions liées (si cascade non configurée)
        Inscription.objects.filter(id_classe=classe).delete()

        # Supprimer la classe
        classe.delete()

        return JsonResponse({'success': True, 'message': f'Classe {nom} supprimée avec succès'})
    except Classe.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Classe non trouvée'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def toggle_classe(request, id):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            classe = Classe.objects.get(id=id)
            classe.actif = data.get('actif', False)
            classe.save()
            return JsonResponse({'success': True, 'message': f'Classe {"activée" if classe.actif else "désactivée"} avec succès'})
        except Classe.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Classe non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


# =====================================================
# FONCTIONS UTILITAIRES POUR LA RÉINSCRIPTION
# =====================================================

def get_niveau_ordre(niveau):
    """
    Retourne l'ordre d'un niveau pour comparaison
    Progression : 7e (1) → 8e (2) → 1ère (3) → 2ème (4) → 3ème (5) → 4ème (6)
    """
    if not niveau:
        return 0
    
    niveau_propre = str(niveau).strip().lower()
    niveau_propre = niveau_propre.replace('è', 'e').replace('é', 'e').replace('ê', 'e')
    
    niveaux_ordre = {
        '7e': 1, 
        '8e': 2,
        '1ere': 3,
        '1ère': 3,
        '2eme': 4,
        '2ème': 4,
        '3eme': 5,
        '3ème': 5,
        '4eme': 6,
        '4ème': 6
    }
    return niveaux_ordre.get(niveau_propre, 0)


def get_prochain_niveau(niveau_actuel):
    """
    Retourne le niveau suivant pour une classe donnée
    Progression : 7e → 8e → 1ère → 2ème → 3ème → 4ème
    """
    if not niveau_actuel:
        return None
    
    niveau_propre = str(niveau_actuel).strip().lower()
    niveau_propre = niveau_propre.replace('è', 'e').replace('é', 'e').replace('ê', 'e')
    
    niveaux_suivants = {
        '7e': '8e', 
        '8e': '1ère',
        '1ere': '2ème',
        '1ère': '2ème',
        '2eme': '3ème',
        '2ème': '3ème',
        '3eme': '4ème',
        '3ème': '4ème',
        '4eme': None,
        '4ème': None
    }
    return niveaux_suivants.get(niveau_propre)


def get_cycle_from_niveau(niveau):
    """
    Détermine le cycle d'un niveau
    """
    if not niveau:
        return None
    
    niveau_propre = str(niveau).strip().lower()
    niveau_propre = niveau_propre.replace('è', 'e').replace('é', 'e').replace('ê', 'e')
    
    if niveau_propre in ['7e', '8e']:
        return 'CO'
    elif niveau_propre in ['1ere', '1ère', '2eme', '2ème', '3eme', '3ème', '4eme', '4ème']:
        return 'SECONDAIRE'
    return None


# =============================================
# VUE PRINCIPALE DE RÉINSCRIPTION
# =============================================

def reinscription_view(request):
    """
    Vue principale pour la réinscription des élèves
    """
    # Vérification d'authentification personnalisée
    if not request.session.get('user_id'):
        messages.error(request, 'Veuillez vous connecter pour accéder à cette page.')
        return redirect('login')
    
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('dashboard_de')
    
    # Récupérer l'année active
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    if not annee_active:
        messages.error(request, 'Aucune année académique active. Veuillez d\'abord définir l\'année en cours.')
        return redirect('annee_scolaire_page')
    
    context = {
        'user_nom': request.session.get('user_nom'),
        'annee_active': annee_active,
        'annee_active_id': annee_active.id,
        'page_title': 'Réinscription - CS KABA',
        'eleve': None,
        'personne': None,
        'classe_actuelle': None,
        'prochain_niveau': None,
        'classes_disponibles': [],
        'cycle_actuel': None,
        'search_performed': False,
    }
    
    # Traitement du formulaire POST
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'search':
            # Recherche d'étudiant
            matricule = request.POST.get('matricule', '').strip()
            
            if not matricule:
                messages.error(request, 'Veuillez saisir un matricule.')
                return render(request, 'Cote/admin/reinscription.html', context)
            
            try:
                eleve = Eleve.objects.select_related('id_personne').get(
                    matricule=matricule, 
                    est_actif=True
                )
                
                # Vérifier si déjà inscrit pour cette année
                deja_inscrit = Inscription.objects.filter(
                    id_eleve=eleve,
                    id_annee=annee_active,
                    est_active=True
                ).exists()
                
                if deja_inscrit:
                    messages.error(request, f"Cet étudiant est déjà inscrit pour l'année {annee_active.annee_scolaire}")
                    return render(request, 'Cote/admin/reinscription.html', context)
                
                # Récupérer la dernière inscription
                derniere_inscription = Inscription.objects.filter(
                    id_eleve=eleve,
                    est_active=True
                ).select_related('id_classe').order_by('-date_inscription').first()
                
                if not derniere_inscription:
                    messages.error(request, "Cet étudiant n'a aucune inscription antérieure. Veuillez l'inscrire comme nouvel élève.")
                    return render(request, 'Cote/admin/reinscription.html', context)
                
                classe_actuelle = derniere_inscription.id_classe
                niveau_actuel = classe_actuelle.niveau
                
                prochain_niveau = get_prochain_niveau(niveau_actuel)
                
                # Récupérer toutes les classes disponibles pour le prochain niveau
                classes_disponibles = []
                if prochain_niveau:
                    classes_disponibles = Classe.objects.filter(
                        niveau=prochain_niveau
                    ).order_by('nom_classe')
                    
                    if not classes_disponibles:
                        messages.warning(request, f"Aucune classe n'a été créée pour le niveau {prochain_niveau}. Veuillez d'abord créer une classe dans 'Gestion des classes et options'.")
                else:
                    messages.info(request, "Cet élève est en 4ème (Terminale). C'est la dernière classe du secondaire, il ne peut plus progresser.")
                
                context.update({
                    'eleve': eleve,
                    'personne': eleve.id_personne,
                    'classe_actuelle': classe_actuelle,
                    'prochain_niveau': prochain_niveau,
                    'classes_disponibles': classes_disponibles,
                    'derniere_inscription': derniere_inscription,
                    'search_performed': True,
                    'cycle_actuel': get_cycle_from_niveau(niveau_actuel),
                    'prochain_cycle': get_cycle_from_niveau(prochain_niveau) if prochain_niveau else None,
                })
                
                messages.success(request, f"Élève trouvé : {eleve.id_personne.prenom} {eleve.id_personne.nom}")
                
            except Eleve.DoesNotExist:
                messages.error(request, f"Aucun étudiant trouvé avec le matricule : {matricule}")
        
        elif action == 'confirm_reinscription':
            # Confirmation de la réinscription
            eleve_id = request.POST.get('eleve_id')
            classe_id = request.POST.get('classe_id')
            est_redoublant = request.POST.get('est_redoublant') == 'on'
            observations = request.POST.get('observations', '')
            
            if not eleve_id or not classe_id:
                messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
                return render(request, 'Cote/admin/reinscription.html', context)
            
            try:
                with transaction.atomic():
                    eleve = get_object_or_404(Eleve, id=eleve_id, est_actif=True)
                    classe_nouvelle = get_object_or_404(Classe, id=classe_id)
                    
                    # Récupérer la dernière inscription
                    derniere_inscription = Inscription.objects.filter(
                        id_eleve=eleve,
                        est_active=True
                    ).select_related('id_classe').order_by('-date_inscription').first()
                    
                    if not derniere_inscription:
                        messages.error(request, "Cet étudiant n'a aucune inscription antérieure.")
                        return render(request, 'Cote/admin/reinscription.html', context)
                    
                    classe_ancienne = derniere_inscription.id_classe
                    
                    # Validation
                    if est_redoublant:
                        if classe_ancienne.id != classe_nouvelle.id:
                            messages.error(request, "En cas de redoublement, l'élève doit rester dans la même classe.")
                            return render(request, 'Cote/admin/reinscription.html', context)
                    else:
                        ancien_niveau = classe_ancienne.niveau
                        nouveau_niveau = classe_nouvelle.niveau
                        prochain_niveau = get_prochain_niveau(ancien_niveau)
                        
                        if nouveau_niveau != prochain_niveau:
                            messages.error(request, f"L'élève doit passer de {ancien_niveau} à {prochain_niveau} (progression d'un niveau).")
                            return render(request, 'Cote/admin/reinscription.html', context)
                    
                    # Créer la réinscription
                    from .models import Reinscription
                    reinscription = Reinscription.objects.create(
                        eleve=eleve,
                        annee_scolaire=annee_active,
                        classe_ancienne=classe_ancienne,
                        classe_nouvelle=classe_nouvelle,
                        est_redoublant=est_redoublant,
                        observations=observations,
                        est_validee=True,
                        validee_par=Utilisateur.objects.get(id=request.session.get('user_id')),
                        date_validation=timezone.now()
                    )
                    
                    # Créer la nouvelle inscription
                    Inscription.objects.create(
                        id_eleve=eleve,
                        id_classe=classe_nouvelle,
                        id_annee=annee_active,
                        type_inscription='REINSCRIPTION',
                        est_active=True,
                        created_by=Utilisateur.objects.get(id=request.session.get('user_id'))
                    )
                    
                    messages.success(request, f'✅ Réinscription effectuée avec succès ! {eleve.id_personne.prenom} {eleve.id_personne.nom} est maintenant en {classe_nouvelle.nom_classe}.')
                    
                    return redirect('reinscription_confirmation', reinscription_id=reinscription.id)
                    
            except Exception as e:
                messages.error(request, f'❌ Erreur lors de la réinscription : {str(e)}')
                return render(request, 'Cote/admin/reinscription.html', context)
    
    return render(request, 'Cote/admin/reinscription.html', context)


def reinscription_confirmation(request, reinscription_id):
    """
    Page de confirmation après une réinscription réussie
    """
    if not request.session.get('user_id'):
        messages.error(request, 'Veuillez vous connecter pour accéder à cette page.')
        return redirect('login')
    
    if request.session.get('user_role') != 'DE':
        messages.error(request, 'Accès non autorisé')
        return redirect('dashboard_de')
    
    from .models import Reinscription
    reinscription = get_object_or_404(
        Reinscription.objects.select_related(
            'eleve__id_personne',
            'classe_ancienne',
            'classe_nouvelle',
            'annee_scolaire',
            'validee_par__id_personne'
        ),
        id=reinscription_id
    )
    
    context = {
        'user_nom': request.session.get('user_nom'),
        'reinscription': reinscription,
        'page_title': 'Confirmation de réinscription - CS KABA'
    }
    
    return render(request, 'Cote/admin/reinscription_confirmation.html', context)


# =============================================
# APIS AJAX pour la réinscription
# =============================================

def api_get_classes_by_niveau(request):
    """
    API pour récupérer les classes disponibles pour un niveau donné
    GET: ?niveau=1ère
    """
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    
    niveau = request.GET.get('niveau')
    
    if not niveau:
        return JsonResponse({'success': False, 'error': 'Niveau non spécifié'}, status=400)
    
    classes = Classe.objects.filter(
        niveau=niveau
    ).values('id', 'nom_classe', 'est_cycle_orientation')
    
    return JsonResponse({
        'success': True,
        'classes': list(classes)
    })


def api_search_eleve(request):
    """
    API pour la recherche instantanée d'élèves
    GET: ?q=KABA2026
    """
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    
    q = request.GET.get('q', '').strip()
    
    if len(q) < 3:
        return JsonResponse({'success': False, 'error': 'Minimum 3 caractères'}, status=400)
    
    eleves = Eleve.objects.select_related('id_personne').filter(
        Q(matricule__icontains=q) |
        Q(id_personne__nom__icontains=q) |
        Q(id_personne__prenom__icontains=q),
        est_actif=True
    )[:10]
    
    data = []
    for eleve in eleves:
        data.append({
            'id': eleve.id,
            'matricule': eleve.matricule,
            'nom': eleve.id_personne.nom,
            'postnom': eleve.id_personne.postnom or '',
            'prenom': eleve.id_personne.prenom,
            'sexe': eleve.id_personne.sexe,
        })
    
    return JsonResponse({
        'success': True,
        'data': data
    })


def api_get_eleve_info(request):
    """
    API pour récupérer les informations complètes d'un élève pour la réinscription
    GET: ?matricule=KABA2026001
    """
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    
    matricule = request.GET.get('matricule', '').strip()
    
    if not matricule:
        return JsonResponse({'success': False, 'error': 'Matricule requis'}, status=400)
    
    try:
        eleve = Eleve.objects.select_related('id_personne').get(
            matricule=matricule,
            est_actif=True
        )
        
        derniere_inscription = Inscription.objects.filter(
            id_eleve=eleve,
            est_active=True
        ).select_related('id_classe').order_by('-date_inscription').first()
        
        if not derniere_inscription:
            return JsonResponse({
                'success': False,
                'error': "Cet élève n'a pas d'inscription antérieure"
            })
        
        classe_actuelle = derniere_inscription.id_classe
        prochain_niveau = get_prochain_niveau(classe_actuelle.niveau)
        
        classes_disponibles = []
        if prochain_niveau:
            classes_disponibles = list(Classe.objects.filter(
                niveau=prochain_niveau
            ).values('id', 'nom_classe'))
        
        return JsonResponse({
            'success': True,
            'eleve': {
                'id': eleve.id,
                'matricule': eleve.matricule,
                'nom': eleve.id_personne.nom,
                'postnom': eleve.id_personne.postnom or '',
                'prenom': eleve.id_personne.prenom,
                'sexe': eleve.id_personne.sexe,
                'date_naissance': eleve.id_personne.date_naissance.strftime('%d/%m/%Y') if eleve.id_personne.date_naissance else None,
                'classe_actuelle': {
                    'id': classe_actuelle.id,
                    'nom': classe_actuelle.nom_classe,
                    'niveau': classe_actuelle.niveau
                },
                'prochain_niveau': prochain_niveau,
                'classes_disponibles': classes_disponibles,
                'photo': eleve.photo.url if eleve.photo else None
            }
        })
        
    except Eleve.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f"Aucun élève trouvé avec le matricule {matricule}"
        })


def api_get_cycle_info(request):
    """
    API pour récupérer les informations sur les cycles
    """
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    
    return JsonResponse({
        'success': True,
        'cycles': [
            {'code': 'CO', 'label': 'Cycle d\'Orientation (7e-8e)', 'niveaux': ['7e', '8e']},
            {'code': 'SECONDAIRE', 'label': 'Secondaire (1ère-4ème)', 'niveaux': ['1ère', '2ème', '3ème', '4ème']}
        ]
    })


def api_get_cycles(request):
    """
    API pour récupérer les cycles disponibles
    GET: /api/reinscription/cycles/
    Retourne: JSON avec les cycles et leurs niveaux disponibles
    """
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    
    cycles = [
        {
            'code': 'CO',
            'label': "Cycle d'Orientation (7e-8e)",
            'niveaux': ['7e', '8e']
        },
        {
            'code': 'SECONDAIRE',
            'label': 'Secondaire (1ère-4ème)',
            'niveaux': ['1ère', '2ème', '3ème', '4ème']
        }
    ]
    
    for cycle in cycles:
        niveaux_disponibles = []
        for niveau in cycle['niveaux']:
            if Classe.objects.filter(niveau=niveau).exists():
                niveaux_disponibles.append(niveau)
        cycle['niveaux_disponibles'] = niveaux_disponibles
    
    return JsonResponse({
        'success': True,
        'cycles': cycles
    })


def api_get_niveaux_par_cycle(request):
    """
    API pour récupérer les niveaux disponibles pour un cycle donné
    GET: /api/reinscription/niveaux/?cycle=CO ou cycle=SECONDAIRE
    Retourne: JSON avec la liste des niveaux
    """
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    
    cycle = request.GET.get('cycle', '')
    
    if cycle == 'CO':
        niveaux = ['7e', '8e']
    elif cycle == 'SECONDAIRE':
        niveaux = ['1ère', '2ème', '3ème', '4ème']
    else:
        return JsonResponse({'success': False, 'error': 'Cycle non reconnu'}, status=400)
    
    niveaux_disponibles = []
    for niveau in niveaux:
        if Classe.objects.filter(niveau=niveau).exists():
            niveaux_disponibles.append(niveau)
    
    return JsonResponse({
        'success': True,
        'niveaux': niveaux_disponibles
    })


def api_get_classes_par_niveau(request):
    """
    API pour récupérer les classes disponibles pour un niveau donné
    GET: /api/reinscription/classes/?niveau=1ère
    Retourne: JSON avec la liste des classes
    """
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    
    niveau = request.GET.get('niveau', '')
    
    if not niveau:
        return JsonResponse({'success': False, 'error': 'Niveau non spécifié'}, status=400)
    
    classes = Classe.objects.filter(
        niveau=niveau
    ).select_related('id_option').order_by('nom_classe')
    
    data = []
    for classe in classes:
        data.append({
            'id': classe.id,
            'nom_classe': classe.nom_classe,
            'est_cycle_orientation': classe.est_cycle_orientation,
            'option': classe.id_option.nom_option if classe.id_option else None,
            'option_id': classe.id_option.id if classe.id_option else None,
            'actif': classe.actif,
        })
    
    return JsonResponse({
        'success': True,
        'classes': data
    })


def debug_niveau(request):
    """
    Fonction de débogage pour voir les niveaux existants dans la base de données
    """
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    
    niveaux = Classe.objects.exclude(niveau__isnull=True).exclude(niveau='').values_list('niveau', flat=True).distinct()
    
    test_progression = {}
    for niveau in niveaux:
        test_progression[niveau] = get_prochain_niveau(niveau)
    
    return JsonResponse({
        'niveaux_existants': list(niveaux),
        'test_progression': test_progression,
        'niveaux_suivants': {
            '7e': get_prochain_niveau('7e'),
            '8e': get_prochain_niveau('8e'),
            '1ère': get_prochain_niveau('1ère'),
            '2ème': get_prochain_niveau('2ème'),
            '3ème': get_prochain_niveau('3ème'),
            '4ème': get_prochain_niveau('4ème'),
        }
    })