# Cote/models.py

from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from datetime import datetime

# =====================================================
# 1. TABLE OPTION_ETUDE
# =====================================================
class OptionEtude(models.Model):
    nom_option = models.CharField(max_length=100, verbose_name="Nom de l'option")
    code_option = models.CharField(max_length=10, unique=True, verbose_name="Code option")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Option d'étude"
        verbose_name_plural = "Options d'étude"
        ordering = ['nom_option']

    def __str__(self):
        return f"{self.nom_option} ({self.code_option})"


# =====================================================
# 2. TABLE CLASSE (CORRIGÉE)
# =====================================================
class Classe(models.Model):
    nom_classe = models.CharField(max_length=50, verbose_name="Nom de la classe")
    niveau = models.CharField(max_length=20, blank=True, null=True, verbose_name="Niveau")
    id_option = models.ForeignKey(OptionEtude, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Option")
    est_cycle_orientation = models.BooleanField(default=False, verbose_name="Est cycle d'orientation")
    capacite_max = models.IntegerField(default=30, verbose_name="Capacité maximale")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ['niveau', 'nom_classe']
        # =============================================
        # CORRECTION : Suppression de la contrainte unique
        # pour permettre plusieurs classes avec le même nom
        # mais des options différentes
        # =============================================
        # unique_together = ['nom_classe', 'id_option']  # SUPPRIMÉ
        unique_together = []  # Pas de contrainte d'unicité sur nom_classe + option

    def __str__(self):
        if self.est_cycle_orientation:
            return f"{self.nom_classe} (CO)"
        return f"{self.nom_classe} - {self.id_option.nom_option if self.id_option else 'Sans option'}"


# =====================================================
# 3. TABLE ANNEE_SCOLAIRE
# =====================================================
class AnneeScolaire(models.Model):
    annee_scolaire = models.CharField(max_length=20, unique=True, verbose_name="Année scolaire")
    est_active = models.BooleanField(default=False, verbose_name="Année active")
    date_debut = models.DateField(verbose_name="Date début")
    date_fin = models.DateField(verbose_name="Date fin")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Année scolaire"
        verbose_name_plural = "Années scolaires"
        ordering = ['-id']

    def __str__(self):
        return self.annee_scolaire

    def save(self, *args, **kwargs):
        if self.est_active:
            AnneeScolaire.objects.filter(est_active=True).update(est_active=False)
        super().save(*args, **kwargs)


# =====================================================
# 4. TABLE PERSONNE
# =====================================================
class Personne(models.Model):
    SEXE_CHOICES = [('M', 'Masculin'), ('F', 'Féminin')]
    
    nom = models.CharField(max_length=100, verbose_name="Nom")
    postnom = models.CharField(max_length=100, blank=True, null=True, verbose_name="Postnom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    lieu_naissance = models.CharField(max_length=100, blank=True, null=True, verbose_name="Lieu de naissance")
    date_naissance = models.DateField(blank=True, null=True, verbose_name="Date de naissance")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, blank=True, null=True, verbose_name="Sexe")
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name="Email")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    photo = models.ImageField(upload_to='photos/personnes/', blank=True, null=True, verbose_name="Photo de profil")

    class Meta:
        verbose_name = "Personne"
        verbose_name_plural = "Personnes"
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom}"


# =====================================================
# 5. TABLE UTILISATEUR
# =====================================================
class Utilisateur(models.Model):
    ROLE_CHOICES = [('DE', 'Directeur des Études'), ('ENSEIGNANT', 'Enseignant'), ('TITULAIRE', 'Titulaire')]
    
    id_personne = models.OneToOneField(Personne, on_delete=models.CASCADE, verbose_name="Personne")
    email = models.EmailField(max_length=255, unique=True, verbose_name="Email")
    password_hash = models.CharField(max_length=255, verbose_name="Mot de passe hashé")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Rôle")
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")
    est_principal = models.BooleanField(default=False, verbose_name="Est principal")
    dernier_connexion = models.DateTimeField(blank=True, null=True, verbose_name="Dernière connexion")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.email} - {self.get_role_display()}"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)


# =====================================================
# 6. TABLE PERSONNEL
# =====================================================
class Personnel(models.Model):
    id_utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, verbose_name="Utilisateur")
    date_embauche = models.DateField(blank=True, null=True, verbose_name="Date d'embauche")
    specialite = models.CharField(max_length=100, blank=True, null=True, verbose_name="Spécialité")
    est_titulaire = models.BooleanField(default=False, verbose_name="Est titulaire")

    class Meta:
        verbose_name = "Personnel"
        verbose_name_plural = "Personnels"

    def __str__(self):
        return f"{self.id_utilisateur.id_personne.nom} {self.id_utilisateur.id_personne.prenom}"


# =====================================================
# 7. TABLE ELEVE (avec photo)
# =====================================================
class Eleve(models.Model):
    id_personne = models.OneToOneField(Personne, on_delete=models.CASCADE, verbose_name="Personne")
    matricule = models.CharField(max_length=50, unique=True, verbose_name="Matricule")
    telephone_parent = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone parent")
    email_parent = models.EmailField(max_length=255, blank=True, null=True, verbose_name="Email parent")
    photo = models.ImageField(upload_to='photos/eleves/', blank=True, null=True, verbose_name="Photo de l'élève")
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ['id_personne__nom', 'id_personne__prenom']

    def __str__(self):
        return f"{self.matricule} - {self.id_personne.nom} {self.id_personne.prenom}"


# =====================================================
# 8. TABLE INSCRIPTION
# =====================================================
class Inscription(models.Model):
    TYPE_CHOICES = [('NOUVEAU', 'Nouveau'), ('REINSCRIPTION', 'Réinscription')]
    
    id_eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, verbose_name="Élève")
    id_classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe")
    id_annee = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année scolaire")
    type_inscription = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type d'inscription")
    date_inscription = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    est_active = models.BooleanField(default=True, verbose_name="Est active")
    created_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créé par")

    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"
        unique_together = ['id_eleve', 'id_annee']

    def __str__(self):
        return f"{self.id_eleve} - {self.id_annee.annee_scolaire}"


# =====================================================
# 9. TABLE COURS (ajout du champ points_par_periode)
# =====================================================
class Cours(models.Model):
    nom_cours = models.CharField(max_length=100, verbose_name="Nom du cours")
    code_cours = models.CharField(max_length=20, unique=True, verbose_name="Code cours")
    coefficient = models.IntegerField(default=1, verbose_name="Coefficient")
    points_par_periode = models.PositiveSmallIntegerField(default=40, verbose_name="Points par période")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    id_option = models.ForeignKey(OptionEtude, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Option")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    created_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créé par")

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ['nom_cours']

    def __str__(self):
        return f"{self.nom_cours} (Coeff: {self.coefficient}, Points/période: {self.points_par_periode})"


# =====================================================
# 10. TABLE ATTRIBUTION_COURS (avec double contrainte)
# =====================================================
class AttributionCours(models.Model):
    id_personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, verbose_name="Personnel")
    id_cours = models.ForeignKey(Cours, on_delete=models.CASCADE, verbose_name="Cours")
    id_classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe")
    id_annee = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année scolaire")
    date_attribution = models.DateField(auto_now_add=True, verbose_name="Date d'attribution")
    est_active = models.BooleanField(default=True, verbose_name="Est active")

    class Meta:
        verbose_name = "Attribution de cours"
        verbose_name_plural = "Attributions de cours"
        unique_together = [
            ['id_personnel', 'id_cours', 'id_classe', 'id_annee'],
            ['id_cours', 'id_classe', 'id_annee'],
        ]

    def __str__(self):
        return f"{self.id_cours.nom_cours} - {self.id_classe} - {self.id_annee.annee_scolaire}"


# =====================================================
# 11. TABLE TITULAIRE_CLASSE
# =====================================================
class TitulaireClasse(models.Model):
    id_personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, verbose_name="Personnel")
    id_classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe")
    id_annee = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année scolaire")
    date_nomination = models.DateField(auto_now_add=True, verbose_name="Date de nomination")
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")

    class Meta:
        verbose_name = "Titulaire de classe"
        verbose_name_plural = "Titulaires de classe"
        unique_together = ['id_classe', 'id_annee']

    def __str__(self):
        return f"Titulaire: {self.id_classe} - {self.id_annee.annee_scolaire}"


# =====================================================
# 12. TABLE PERIODE
# =====================================================
class Periode(models.Model):
    nom_periode = models.CharField(max_length=20, verbose_name="Nom de la période")
    numero_periode = models.SmallIntegerField(verbose_name="Numéro période", choices=[(1, '1ère Période'), (2, '2ème Période')])
    date_debut = models.DateField(blank=True, null=True, verbose_name="Date début")
    date_fin = models.DateField(blank=True, null=True, verbose_name="Date fin")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Période"
        verbose_name_plural = "Périodes"

    def __str__(self):
        return self.nom_periode


# =====================================================
# 13. TABLE SEMESTRE
# =====================================================
class Semestre(models.Model):
    nom_semestre = models.CharField(max_length=20, verbose_name="Nom du semestre")
    numero_semestre = models.SmallIntegerField(verbose_name="Numéro semestre", choices=[(1, '1er Semestre'), (2, '2ème Semestre')])
    date_debut = models.DateField(blank=True, null=True, verbose_name="Date début")
    date_fin = models.DateField(blank=True, null=True, verbose_name="Date fin")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Semestre"
        verbose_name_plural = "Semestres"

    def __str__(self):
        return self.nom_semestre


# =====================================================
# 14. TABLE NOTE (conservée pour compatibilité)
# =====================================================
class Note(models.Model):
    id_eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, verbose_name="Élève")
    id_cours = models.ForeignKey(Cours, on_delete=models.CASCADE, verbose_name="Cours")
    id_classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe")
    id_annee = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année scolaire")
    id_periode = models.ForeignKey(Periode, on_delete=models.CASCADE, verbose_name="Période")
    note = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Note", help_text="Note entre 0 et 20")
    date_saisie = models.DateTimeField(auto_now_add=True, verbose_name="Date de saisie")
    id_personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, verbose_name="Enseignant")
    est_validee = models.BooleanField(default=False, verbose_name="Est validée")
    commentaire = models.TextField(blank=True, null=True, verbose_name="Commentaire")

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        unique_together = ['id_eleve', 'id_cours', 'id_annee', 'id_periode']

    def clean(self):
        if self.note < 0 or self.note > 20:
            raise ValidationError("La note doit être comprise entre 0 et 20")

    def __str__(self):
        return f"{self.id_eleve} - {self.id_cours.nom_cours}: {self.note}"


# =====================================================
# 15. TABLE BULLETIN
# =====================================================
class Bulletin(models.Model):
    id_eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, verbose_name="Élève")
    id_classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe")
    id_annee = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année scolaire")
    id_semestre = models.ForeignKey(Semestre, on_delete=models.CASCADE, verbose_name="Semestre")
    moyenne_periode1 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Moyenne 1ère période")
    moyenne_periode2 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Moyenne 2ème période")
    moyenne_semestrielle = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Moyenne semestrielle")
    rang_classe = models.IntegerField(blank=True, null=True, verbose_name="Rang dans la classe")
    appreciation = models.TextField(blank=True, null=True, verbose_name="Appréciation")
    date_generation = models.DateTimeField(auto_now_add=True, verbose_name="Date de génération")
    pdf_path = models.CharField(max_length=500, blank=True, null=True, verbose_name="Chemin du PDF")
    generated_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Généré par")

    class Meta:
        verbose_name = "Bulletin"
        verbose_name_plural = "Bulletins"

    def __str__(self):
        return f"Bulletin {self.id_eleve} - {self.id_annee.annee_scolaire}"


# =====================================================
# 16. TABLE PALMARES
# =====================================================
class Palmares(models.Model):
    MENTION_CHOICES = [
        ('EXCELLENT', 'Excellent'), ('TRES BIEN', 'Très Bien'),
        ('BIEN', 'Bien'), ('ASSEZ BIEN', 'Assez Bien'), ('PASSABLE', 'Passable')
    ]
    id_annee = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année scolaire")
    id_classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe")
    id_eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, verbose_name="Élève")
    rang = models.IntegerField(verbose_name="Rang")
    mention = models.CharField(max_length=20, choices=MENTION_CHOICES, verbose_name="Mention")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Palmarès"
        verbose_name_plural = "Palmarès"

    def __str__(self):
        return f"{self.id_annee.annee_scolaire} - {self.id_classe} - Rang {self.rang}"


# =====================================================
# 17. TABLE COTE (adaptée pour utiliser points_par_periode)
# =====================================================
class Cote(models.Model):
    """
    Enregistrement complet des cotes d'un élève pour un cours sur une année scolaire.
    Utilise le système de points défini par cours (points_par_periode).
    """
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, verbose_name="Élève")
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, verbose_name="Cours")
    enseignant = models.ForeignKey(Personnel, on_delete=models.CASCADE, verbose_name="Enseignant")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année scolaire")
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe")
    validee_titulaire = models.BooleanField(default=False, verbose_name="Validée par le titulaire")

    # Cotes du premier semestre (périodes 1 et 2 + examen)
    cote_p1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Cote P1")
    cote_p2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Cote P2")
    examen_semestre_1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Examen S1")

    # Cotes du second semestre (périodes 3 et 4 + examen)
    cote_p3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Cote P3")
    cote_p4 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Cote P4")
    examen_semestre_2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Examen S2")

    # Champs calculés automatiquement
    total_semestre_1 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Total S1")
    total_semestre_2 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Total S2")
    total_general = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Total général")
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Pourcentage")
    observation = models.CharField(max_length=20, null=True, blank=True, verbose_name="Observation")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cote"
        verbose_name_plural = "Cotes"
        unique_together = [['eleve', 'cours', 'annee_scolaire', 'classe']]

    def __str__(self):
        return f"{self.eleve} - {self.cours.nom_cours} ({self.annee_scolaire})"

    def clean(self):
        """Validation : chaque note doit être comprise entre 0 et le maximum autorisé (points_par_periode ou 2×points_par_periode pour les examens)."""
        if not self.cours_id:
            return
        max_periode = self.cours.points_par_periode
        max_examen = max_periode * 2

        for field, max_val in [
            ('cote_p1', max_periode), ('cote_p2', max_periode),
            ('cote_p3', max_periode), ('cote_p4', max_periode),
            ('examen_semestre_1', max_examen), ('examen_semestre_2', max_examen)
        ]:
            value = getattr(self, field)
            if value is not None and (value < 0 or value > max_val):
                raise ValidationError(
                    f"{field} doit être compris entre 0 et {max_val} "
                    f"(points_par_periode = {max_periode})."
                )

    def save(self, *args, **kwargs):
        max_periode = self.cours.points_par_periode
        max_examen = max_periode * 2
        max_total_semestre = max_periode * 2 + max_examen
        max_total_general = max_total_semestre * 2

        if self.cote_p1 is not None and self.cote_p2 is not None and self.examen_semestre_1 is not None:
            self.total_semestre_1 = self.cote_p1 + self.cote_p2 + self.examen_semestre_1
        else:
            self.total_semestre_1 = None

        if self.cote_p3 is not None and self.cote_p4 is not None and self.examen_semestre_2 is not None:
            self.total_semestre_2 = self.cote_p3 + self.cote_p4 + self.examen_semestre_2
        else:
            self.total_semestre_2 = None

        if self.total_semestre_1 is not None and self.total_semestre_2 is not None:
            self.total_general = self.total_semestre_1 + self.total_semestre_2
            if max_total_general > 0:
                self.pourcentage = (self.total_general / max_total_general) * 100
                self.observation = "Réussi" if self.pourcentage >= 50 else "Échec"
            else:
                self.pourcentage = None
                self.observation = None
        else:
            self.total_general = None
            self.pourcentage = None
            self.observation = None

        super().save(*args, **kwargs)


# =====================================================
# 18. TABLE ARCHIVAGE
# =====================================================
class Archivage(models.Model):
    table_source = models.CharField(max_length=50, verbose_name="Table source")
    record_id = models.IntegerField(verbose_name="ID de l'enregistrement")
    data = models.JSONField(verbose_name="Données archivées")
    date_archivage = models.DateTimeField(auto_now_add=True, verbose_name="Date d'archivage")
    archived_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Archivé par")
    raison = models.CharField(max_length=255, blank=True, null=True, verbose_name="Raison de l'archivage")

    class Meta:
        verbose_name = "Archivage"
        verbose_name_plural = "Archivages"

    def __str__(self):
        return f"{self.table_source} - ID: {self.record_id} - {self.date_archivage}"


# =====================================================
# 19. TABLE REINSCRIPTION
# =====================================================
class Reinscription(models.Model):
    """
    Modèle pour gérer les réinscriptions des élèves d'une année à l'autre
    """
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, verbose_name="Élève")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, verbose_name="Année scolaire")
    classe_ancienne = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='anciennes_reinscriptions', verbose_name="Ancienne classe")
    classe_nouvelle = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='nouvelles_reinscriptions', verbose_name="Nouvelle classe")
    est_redoublant = models.BooleanField(default=False, verbose_name="Est redoublant")
    date_reinscription = models.DateTimeField(auto_now_add=True, verbose_name="Date de réinscription")
    est_validee = models.BooleanField(default=False, verbose_name="Est validée")
    validee_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Validée par")
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation")
    observations = models.TextField(blank=True, null=True, verbose_name="Observations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Réinscription"
        verbose_name_plural = "Réinscriptions"
        ordering = ['-date_reinscription']
        unique_together = [['eleve', 'annee_scolaire']]

    def __str__(self):
        return f"{self.eleve} - {self.annee_scolaire.annee_scolaire}"

    def clean(self):
        """Validation des règles métier"""
        from django.core.exceptions import ValidationError
        
        # 1. Vérifier que l'élève n'est pas déjà inscrit pour cette année
        if hasattr(self.eleve, 'inscription_set'):
            inscriptions_existantes = self.eleve.inscription_set.filter(
                id_annee=self.annee_scolaire,
                est_active=True
            ).exclude(id=self.id if self.id else None)
            
            if inscriptions_existantes.exists():
                raise ValidationError("Cet élève est déjà inscrit pour cette année académique.")
        
        # 2. Vérifier la progression logique des classes
        if not self.est_redoublant:
            ancien_niveau = self.classe_ancienne.niveau
            nouveau_niveau = self.classe_nouvelle.niveau
            
            if not self._is_valid_progression(ancien_niveau, nouveau_niveau):
                raise ValidationError(
                    "La progression de classe n'est pas valide. L'élève doit passer à la classe immédiatement supérieure "
                    "ou rester dans la même classe (redoublement)."
                )
        else:
            if self.classe_ancienne.id != self.classe_nouvelle.id:
                raise ValidationError("En cas de redoublement, l'élève doit rester dans la même classe.")

    def _is_valid_progression(self, ancien_niveau, nouveau_niveau):
        """
        Vérifie si la progression d'un niveau à l'autre est valide
        Progression : 7e → 8e → 1ère → 2ème → 3ème → 4ème
        """
        niveaux_ordre = {
            '7e': 1, 
            '8e': 2,
            '1ère': 3, 
            '2ème': 4, 
            '3ème': 5,
            '4ème': 6
        }
        
        ancien_ordre = niveaux_ordre.get(ancien_niveau)
        nouveau_ordre = niveaux_ordre.get(nouveau_niveau)
        
        if ancien_ordre is None or nouveau_ordre is None:
            return False
            
        return nouveau_ordre == ancien_ordre + 1