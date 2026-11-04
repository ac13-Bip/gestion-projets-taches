import os

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from .models import Commentaire, Evaluation, Projet, Tache, Utilisateur

# Fichiers de rendu acceptés
EXTENSIONS_AUTORISEES = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
    '.txt', '.csv', '.md', '.zip', '.rar', '.7z',
    '.png', '.jpg', '.jpeg', '.gif', '.webp',
    '.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.sql', '.json',
}
TAILLE_MAX_FICHIER = 10 * 1024 * 1024  # 10 Mo


# ==========================================
# PROJETS
# ==========================================
class ProjetForm(forms.ModelForm):
    class Meta:
        model = Projet
        fields = ['titre', 'description', 'date_debut', 'date_fin_prevue']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du projet'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'date_fin_prevue': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }
    # La cohérence des dates est vérifiée par Projet.clean() (appelé automatiquement)


# ==========================================
# TÂCHES (création en 2 étapes)
# ==========================================
class TacheEtape1Form(forms.ModelForm):
    def __init__(self, *args, projet=None, **kwargs):
        self.projet = projet
        super().__init__(*args, **kwargs)
        self.fields['specialite_requise'].empty_label = "— Aucune (tout employé) —"

    class Meta:
        model = Tache
        fields = ['titre', 'description', 'specialite_requise', 'priorite', 'date_limite']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la tâche'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'specialite_requise': forms.Select(attrs={'class': 'form-select'}),
            'priorite': forms.Select(attrs={'class': 'form-select'}),
            'date_limite': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }

    def clean_date_limite(self):
        date_limite = self.cleaned_data['date_limite']
        if date_limite < timezone.localdate():
            raise forms.ValidationError("La date limite ne peut pas être dans le passé.")
        if self.projet and date_limite < self.projet.date_debut:
            raise forms.ValidationError("La date limite doit être après le début du projet.")
        return date_limite


class TacheEtape2Form(forms.ModelForm):
    """Assignation : la liste des employés proposés est fournie par la vue."""

    def __init__(self, *args, employes=None, **kwargs):
        super().__init__(*args, **kwargs)
        champ = self.fields['assigne_a']
        champ.required = True
        champ.empty_label = "— Choisir un employé —"
        if employes is not None:
            champ.queryset = employes
        champ.label_from_instance = lambda u: f"{u.nom_affiche} — {u.specialite or 'Généraliste'}"

    class Meta:
        model = Tache
        fields = ['assigne_a']
        widgets = {'assigne_a': forms.Select(attrs={'class': 'form-select'})}
        labels = {'assigne_a': 'Assigner à'}


class MiseAJourTacheForm(forms.ModelForm):
    """Formulaire de l'employé : changer le statut et joindre un livrable."""

    class Meta:
        model = Tache
        fields = ['statut', 'fichier_rendu']
        widgets = {
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'fichier_rendu': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {'fichier_rendu': 'Livrable (optionnel)'}

    def clean_fichier_rendu(self):
        fichier = self.cleaned_data.get('fichier_rendu')
        # Un nouveau fichier envoyé possède un attribut "size" et un "content_type"
        if fichier and hasattr(fichier, 'content_type'):
            ext = os.path.splitext(fichier.name)[1].lower()
            if ext not in EXTENSIONS_AUTORISEES:
                raise forms.ValidationError(f"Type de fichier non autorisé ({ext or 'sans extension'}).")
            if fichier.size > TAILLE_MAX_FICHIER:
                raise forms.ValidationError("Le fichier dépasse la taille maximale de 10 Mo.")
        return fichier


# ==========================================
# COMMENTAIRES ET ÉVALUATIONS
# ==========================================
class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Écrivez votre commentaire ici...',
                'maxlength': 2000,
            })
        }
        labels = {'contenu': ''}

    def clean_contenu(self):
        contenu = self.cleaned_data['contenu'].strip()
        if not contenu:
            raise forms.ValidationError("Le commentaire ne peut pas être vide.")
        return contenu


class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ['note', 'feedback_manager']
        widgets = {
            'note': forms.Select(attrs={'class': 'form-select'}),
            'feedback_manager': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4, 'placeholder': 'Votre avis sur le travail...'
            }),
        }
        labels = {'note': 'Note (sur 5)', 'feedback_manager': 'Feedback / remarques'}


# ==========================================
# COMPTES UTILISATEURS (créés par l'administrateur)
# ==========================================
class _CreationUtilisateurForm(forms.ModelForm):
    role_attribue = None  # défini dans les sous-classes

    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    password_confirmation = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email', 'telephone', 'departement']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nom@entreprise.com'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '06 00 00 00 00'}),
            'departement': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {'first_name': 'Prénom', 'last_name': 'Nom'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte existe déjà avec cette adresse email.")
        return email

    def clean(self):
        cleaned = super().clean()
        mdp, confirmation = cleaned.get('password'), cleaned.get('password_confirmation')
        if mdp and confirmation and mdp != confirmation:
            self.add_error('password_confirmation', "Les deux mots de passe ne correspondent pas.")
        if mdp:
            # Applique les règles AUTH_PASSWORD_VALIDATORS (longueur, mot de passe trop courant, etc.)
            utilisateur = Utilisateur(
                email=cleaned.get('email', ''),
                first_name=cleaned.get('first_name', ''),
                last_name=cleaned.get('last_name', ''),
            )
            try:
                validate_password(mdp, user=utilisateur)
            except forms.ValidationError as erreur:
                self.add_error('password', erreur)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = self.role_attribue
        if commit:
            user.save()
        return user


class CreationChefForm(_CreationUtilisateurForm):
    role_attribue = Utilisateur.Role.CHEF_PROJET


class CreationEmployeForm(_CreationUtilisateurForm):
    role_attribue = Utilisateur.Role.EMPLOYE

    class Meta(_CreationUtilisateurForm.Meta):
        fields = _CreationUtilisateurForm.Meta.fields + ['specialite']
        widgets = {
            **_CreationUtilisateurForm.Meta.widgets,
            'specialite': forms.Select(attrs={'class': 'form-select'}),
        }
