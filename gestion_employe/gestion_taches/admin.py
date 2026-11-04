from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import Commentaire, Evaluation, Projet, Specialite, Tache, Utilisateur


class UtilisateurCreationAdminForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ('email',)


class UtilisateurChangeAdminForm(UserChangeForm):
    class Meta:
        model = Utilisateur
        fields = '__all__'


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """Admin basé sur UserAdmin : les mots de passe sont hachés correctement
    et un formulaire dédié permet de les changer."""

    form = UtilisateurChangeAdminForm
    add_form = UtilisateurCreationAdminForm
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'role', 'specialite', 'departement', 'is_active')
    list_filter = ('role', 'specialite', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'telephone')}),
        ('Poste', {'fields': ('role', 'specialite', 'departement', 'date_embauche')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'specialite', 'password1', 'password2'),
        }),
    )


@admin.register(Specialite)
class SpecialiteAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)


class TacheInline(admin.TabularInline):
    model = Tache
    extra = 0
    fields = ('titre', 'assigne_a', 'priorite', 'statut', 'date_limite')
    show_change_link = True


@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    list_display = ('titre', 'chef_de_projet', 'statut', 'date_debut', 'date_fin_prevue')
    list_filter = ('statut', 'chef_de_projet')
    search_fields = ('titre',)
    inlines = [TacheInline]


@admin.register(Tache)
class TacheAdmin(admin.ModelAdmin):
    list_display = ('titre', 'projet', 'assigne_a', 'assigne_par', 'priorite', 'statut', 'date_limite')
    list_filter = ('statut', 'priorite', 'specialite_requise')
    search_fields = ('titre', 'projet__titre')
    list_select_related = ('projet', 'assigne_a', 'assigne_par')


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'tache', 'date_ajout')
    list_select_related = ('auteur', 'tache')


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('tache_evaluee', 'manager', 'note', 'date_evaluation')
    list_filter = ('note',)
