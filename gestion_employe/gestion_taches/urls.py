from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Accueil / authentification
    path('', views.accueil, name='accueil'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True),
         name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirection/', views.redirection_apres_login, name='dashboard_redirect'),

    # Administrateur
    path('dashboard/admin/', views.admin_dashboard, name='dashboard_admin'),
    path('ajouter-chef/', views.ajouter_chef, name='ajouter_chef'),
    path('ajouter-employe/', views.ajouter_employe, name='ajouter_employe'),
    path('employes/supprimer/<int:employe_id>/', views.supprimer_employe, name='supprimer_employe'),
    path('chefs/supprimer/<int:chef_id>/', views.supprimer_chef, name='supprimer_chef'),
    path('utilisateurs/reactiver/<int:user_id>/', views.reactiver_utilisateur, name='reactiver_utilisateur'),

    # Chef de projet
    path('dashboard/chef/', views.dashboard_chef, name='dashboard_chef'),
    path('statistiques/', views.statistiques_chef, name='statistiques_chef'),
    path('projet/creer/', views.creer_projet, name='creer_projet'),
    path('projet/<int:projet_id>/taches/', views.liste_taches_projet, name='liste_taches_projet'),
    path('projet/<int:projet_id>/distribuer/', views.distribuer_taches, name='distribuer_taches'),
    path('projet/<int:projet_id>/tache/etape-1/', views.creer_tache_etape1, name='tache_etape1'),
    path('tache/<int:tache_id>/etape-2/', views.assigner_tache_etape2, name='tache_etape2'),
    path('tache/<int:tache_id>/evaluer/', views.evaluer_tache, name='evaluer_tache'),
    path('generer-ia/', views.generer_description_ia, name='generer_ia'),

    # Employé
    path('dashboard/employe/', views.dashboard_employe, name='dashboard_employe'),
    path('tache/<int:tache_id>/gerer/', views.gerer_tache_employe, name='gerer_tache_employe'),

    # Commun
    path('tache/<int:tache_id>/details/', views.details_tache, name='details_tache'),
    path('tache/<int:tache_id>/livrable/', views.telecharger_rendu, name='telecharger_rendu'),
]
