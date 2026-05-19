from django import forms
from .models import Commentaire, Evaluation, Projet, Tache, Utilisateur


class ProjetForm(forms.ModelForm):
    class Meta:
        model = Projet
        fields = ['titre', 'description', 'date_debut', 'date_fin_prevue']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin_prevue': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class TacheEtape1Form(forms.ModelForm):
    class Meta:
        model = Tache
        fields = ['titre', 'description', 'specialite_requise', 'priorite', 'date_limite']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'specialite_requise': forms.Select(attrs={'class': 'form-control'}),
            'priorite': forms.Select(attrs={'class': 'form-control'}),
            'date_limite': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class TacheEtape2Form(forms.ModelForm):
    
    class Meta:
        model = Tache
        fields = ['assigne_a']
        widgets = {
            'assigne_a': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'assigne_a': 'Assigner à',
        }


class TacheForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigne_a'].queryset = Utilisateur.objects.filter(role='EMPLOYE')

    class Meta:
        model = Tache
        fields = ['titre', 'description', 'specialite_requise', 'priorite', 'date_limite', 'assigne_a']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'specialite_requise': forms.Select(attrs={'class': 'form-control'}),
            'priorite': forms.Select(attrs={'class': 'form-control'}),
            'date_limite': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'assigne_a': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'assigne_a': 'Assigner à',
        }

class  CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Écrivez votre commentaire ici...'
            })
        }
        labels = {
            'contenu': ''  
        }        
class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        # Bddli 'remarque' b 'feedback_manager' hna:
        fields = ['note', 'feedback_manager'] 
        widgets = {
            'note': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5, 'placeholder': 'Note sur 5'}),
            # Bddli 'remarque' b 'feedback_manager' hta hna:
            'feedback_manager': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Votre avis sur le travail...'}),
        }
class CreationChefForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    
    class Meta:
        model = Utilisateur
        fields = ['first_name', 'email', 'password'] # Username mmsou7 kima glti

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = Utilisateur.Role.CHEF_PROJET  
        user.is_staff = True          
        if commit:
            user.save()
        return user       

class CreationEmployeForm(forms.ModelForm):
    # 1. Zwaqna l-password w 3tinah la classe 'form-control'
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}),
        label="Mot de passe"
    )
    
    class Meta:
        model = Utilisateur
        fields = ['first_name', 'email', 'password', 'specialite'] 
        
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Adresse Email'}),
            
            
            'specialite': forms.Select(attrs={'class': 'form-control'}), 
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = Utilisateur.Role.EMPLOYE  
        if commit:
            user.save()
        return user