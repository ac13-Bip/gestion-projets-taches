from django.contrib import admin

from django.contrib import admin
from .models import Utilisateur, Specialite, Projet, Tache, Commentaire, Evaluation
from django.contrib.auth.hashers import make_password



@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'specialite', 'departement')
    # Les filtres f j-jnb l-imen
    list_filter = ('role', 'specialite')
    search_fields = ('email', 'first_name', 'last_name')

    def save_model(self, request, obj, form, change):
        if obj.password and not obj.password.startswith('pbkdf2_'):
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


@admin.register(Specialite)
class SpecialiteAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)


@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    list_display = ('titre', 'chef_de_projet', 'statut', 'date_debut', 'date_fin_prevue')
    list_filter = ('statut', 'chef_de_projet')


@admin.register(Tache)
class TacheAdmin(admin.ModelAdmin):
    list_display = ('titre', 'projet', 'assigne_a', 'assigne_par', 'priorite', 'statut')
    list_filter = ('statut', 'priorite', 'specialite_requise')
    search_fields = ('titre',)


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'tache', 'date_ajout')


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('tache_evaluee', 'manager', 'note', 'date_evaluation')
    list_filter = ('note',)

def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password) # Cryptih db!
        super().save(*args, **kwargs)