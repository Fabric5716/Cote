# Cote/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Pages publiques
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register-admin/', views.register_admin, name='register_admin'),
    
    # Tableaux de bord
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-de/', views.dashboard_de, name='dashboard_de'),
    path('dashboard-enseignant/', views.dashboard_enseignant, name='dashboard_enseignant'),
    path('dashboard-titulaire/', views.dashboard_titulaire, name='dashboard_titulaire'),
    
    # Pages HTML (gestion)
    path('gestion/enseignants/ajouter/', views.ajouter_enseignant_page, name='ajouter_enseignant_page'),
    path('gestion/eleves/ajouter/', views.ajouter_eleve_page, name='ajouter_eleve_page'),
    path('gestion/eleves/liste/', views.liste_eleves, name='liste_eleves'),
    path('gestion/eleves/detail/<int:eleve_id>/', views.detail_eleve, name='detail_eleve'),
    path('gestion/eleves/modifier/<int:eleve_id>/', views.modifier_eleve_page, name='modifier_eleve_page'),
    path('gestion/eleves/recu/<int:eleve_id>/', views.generer_recu_inscription, name='recu_inscription'),
    path('gestion/annee-scolaire/', views.annee_scolaire_page, name='annee_scolaire_page'),
    path('gestion/classes-options/', views.gestion_cls_option_page, name='gestion_cls_option_page'),
    path('gestion/cours/', views.cours_de_page, name='cours_de'),
    
    # =============================================
    # RÉINSCRIPTION
    # =============================================
    path('reinscription/', views.reinscription_view, name='reinscription'),
    path('reinscription/confirmation/<int:reinscription_id>/', 
         views.reinscription_confirmation, 
         name='reinscription_confirmation'),
    
    # =============================================
    # APIS POUR LA RÉINSCRIPTION - RECHERCHE
    # =============================================
    path('api/reinscription/search-eleve/', 
         views.api_search_eleve, 
         name='api_search_eleve'),
    path('api/reinscription/eleve-info/', 
         views.api_get_eleve_info, 
         name='api_eleve_info'),
    path('api/reinscription/classes-par-niveau/', 
         views.api_get_classes_by_niveau, 
         name='api_classes_par_niveau'),
    path('api/reinscription/cycle-info/', 
         views.api_get_cycle_info, 
         name='api_cycle_info'),
    
    # =============================================
    # APIS POUR LA RÉINSCRIPTION - FILTRES DYNAMIQUES (NOUVEAU)
    # =============================================
    path('api/reinscription/cycles/', 
         views.api_get_cycles, 
         name='api_reinscription_cycles'),
    path('api/reinscription/niveaux/', 
         views.api_get_niveaux_par_cycle, 
         name='api_reinscription_niveaux'),
    path('api/reinscription/classes/', 
         views.api_get_classes_par_niveau, 
         name='api_reinscription_classes'),
    
    # API : Enseignants
    path('api/enseignants/ajouter/', views.ajouter_enseignant, name='ajouter_enseignant'),
    
    # API : Élèves
    path('api/eleves/ajouter/', views.ajouter_eleve, name='ajouter_eleve'),
    path('api/eleves/modifier/<int:eleve_id>/', views.modifier_eleve, name='modifier_eleve'),
    
    # API : Années scolaires
    path('api/annee/definir/', views.definir_annee, name='definir_annee'),
    path('api/annee/ajouter/', views.ajouter_annee, name='ajouter_annee'),
    path('api/annee/<int:id>/get/', views.get_annee, name='get_annee'),
    path('api/annee/<int:id>/activer/', views.activer_annee, name='activer_annee'),
    path('api/annee/<int:id>/desactiver/', views.desactiver_annee, name='desactiver_annee'),
    path('api/annee/<int:id>/supprimer/', views.supprimer_annee, name='supprimer_annee'),
    path('api/annee/<int:id>/stats/', views.get_annee_stats, name='get_annee_stats'),
    path('api/annee/<int:id>/print/', views.print_annee_report, name='print_annee_report'),
    
    # API : Classes
    path('api/classe/ajouter/', views.ajouter_classe, name='ajouter_classe'),
    path('api/classe/<int:id>/get/', views.get_classe, name='get_classe'),
    path('api/classe/<int:id>/toggle/', views.toggle_classe, name='toggle_classe'),
    path('api/classe/<int:id>/supprimer/', views.supprimer_classe, name='supprimer_classe'),
    
    # API : Options
    path('api/option/ajouter/', views.ajouter_option, name='ajouter_option'),
    path('api/option/<int:id>/get/', views.get_option, name='get_option'),
    path('api/option/<int:id>/toggle/', views.toggle_option, name='toggle_option'),
    path('api/option/<int:id>/supprimer/', views.supprimer_option, name='supprimer_option'),
    
    # API : Cours
    path('api/cours/ajouter/', views.ajouter_cours, name='ajouter_cours'),
    path('api/cours/<int:id>/get/', views.get_cours, name='get_cours'),
    path('api/cours/<int:id>/modifier/', views.modifier_cours, name='modifier_cours'),
    path('api/cours/<int:id>/supprimer/', views.supprimer_cours, name='supprimer_cours'),
    path('api/cours/par-option/', views.get_cours_par_option, name='cours_par_option'),
    
    # API : Attributions
    path('api/attributions/ajouter/', views.attribuer_cours, name='attribuer_cours'),
    path('api/attributions/classe/', views.get_attributions_classe, name='attributions_classe'),
    path('api/attributions/<int:attribution_id>/supprimer/', views.supprimer_attribution, name='supprimer_attribution'),
    
    # API : Titulaires
    path('api/titulaire/definir/', views.definir_titulaire, name='definir_titulaire'),
    path('api/titulaire/get/', views.get_titulaire, name='get_titulaire'),
    path('api/titulaire/<int:titulaire_id>/supprimer/', views.supprimer_titulaire_par_id, name='supprimer_titulaire_par_id'),
    
    # API : Statistiques, palmarès, exports
    path('api/stats/data/', views.stats_data, name='stats_data'),
    path('api/palmares/generer/', views.generer_palmares, name='generer_palmares'),
    path('api/archives/export-pdf/', views.export_pdf, name='export_pdf'),
    path('api/archives/export-excel/', views.export_excel, name='export_excel'),
    path('api/classes/filter/', views.filtrer_classes_par_cycle, name='filtrer_classes'),
    
    # API Enseignant (saisie cotes, etc.)
    path('api/enseignant/annees/', views.api_enseignant_annees, name='api_enseignant_annees'),
    path('api/enseignant/classes/', views.api_enseignant_classes, name='api_enseignant_classes'),
    path('api/enseignant/cours/', views.api_enseignant_cours, name='api_enseignant_cours'),
    path('api/enseignant/eleves-cotes/', views.api_enseignant_eleves_cotes, name='api_enseignant_eleves_cotes'),
    path('api/enseignant/sauvegarder-cotes/', views.api_sauvegarder_cotes, name='api_sauvegarder_cotes'),
    path('api/enseignant/data/', views.get_enseignant_data, name='get_enseignant_data'),
    
    # Pages enseignant
    path('mes-cours/', views.mes_cours, name='mes_cours'),
    path('saisir-cotes/', views.saisir_cotes, name='saisir_cotes'),
    path('mon-profil/', views.mon_profil, name='mon_profil'),
    
    # Bulletins
    path('bulletin/<int:eleve_id>/', views.bulletin_eleve, name='bulletin_eleve'),
    path('bulletin/<int:eleve_id>/annee/<int:annee_id>/', views.bulletin_eleve, name='bulletin_eleve_annee'),
    
    # Titulaire : vérification des cotes
    path('verifier-cotes/', views.verifier_cotes_titulaire, name='verifier_cotes_titulaire'),
    path('api/titulaire/classe/', views.api_titulaire_classe, name='api_titulaire_classe'),
    path('api/titulaire/cotes-eleves/', views.api_titulaire_cotes_eleves, name='api_titulaire_cotes_eleves'),
    path('api/titulaire/valider-cote/', views.api_titulaire_valider_cote, name='api_titulaire_valider_cote'),
    path('liste-cours/', views.liste_cours_enseignant, name='liste_cours_enseignant'),
    path('api/enseignant/liste-cotes/', views.api_enseignant_liste_cotes, name='api_enseignant_liste_cotes'),
    path('profil/', views.profil_admin, name='profil_admin'),
    path('profil-enseignant/', views.profil_enseignant, name='profil_enseignant'),
    
    # =============================================
    # DÉBOGAGE
    # =============================================
    path('api/debug/niveaux/', views.debug_niveau, name='debug_niveaux'),
]