# forms.py
from django import forms
from .models import Cote, AnneeScolaire, Classe, Cours, Eleve
from django.forms import modelformset_factory

class CoteForm(forms.ModelForm):
    class Meta:
        model = Cote
        fields = ['cote_p1', 'cote_p2', 'cote_p3', 'cote_p4', 'examen_semestre_1', 'examen_semestre_2']
        widgets = {
            'cote_p1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0', 'max': '20'}),
            'cote_p2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0', 'max': '20'}),
            'cote_p3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0', 'max': '20'}),
            'cote_p4': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0', 'max': '20'}),
            'examen_semestre_1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0', 'max': '20'}),
            'examen_semestre_2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0', 'max': '20'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # validation supplémentaire si nécessaire
        return cleaned_data

# Formulaire pour sélectionner la classe, le cours et l'année
class SelectionForm(forms.Form):
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all(),
        label="Année scolaire",
        empty_label="-- Sélectionnez --",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.none(),  # sera filtré dynamiquement
        label="Classe",
        empty_label="-- Sélectionnez --",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cours = forms.ModelChoiceField(
        queryset=Cours.objects.none(),
        label="Cours",
        empty_label="-- Sélectionnez --",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, enseignant_personnel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Classes où l'enseignant intervient (via AttributionCours)
        annees = AnneeScolaire.objects.filter(est_active=True) | AnneeScolaire.objects.all()
        self.fields['annee_scolaire'].queryset = annees.order_by('-date_debut')

        # On ne filtre classe et cours qu'après avoir reçu les données
        # (sera fait dans la vue)