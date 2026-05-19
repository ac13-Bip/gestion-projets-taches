"""
URL configuration for gemploye project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views 
from gemploye import settings
from gestion_taches import views
from django.conf import settings
from django.conf.urls.static import static

 



urlpatterns = [

    path('admin/', admin.site.urls),
    path('', views.accueil, name='accueil'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('redirection/', views.redirection_apres_login, name='dashboard_redirect'),
    path('dashboard/admin/', views.admin_dashboard, name='dashboard_admin'),
    path('ajouter-chef/', views.ajouter_chef, name='ajouter_chef'),
    path('ajouter-employe/', views.ajouter_employe, name='ajouter_employe'),
    path('dashboard/chef/', views.dashboard_chef, name='dashboard_chef'),

    
    path('dashboard/employe/', views.dashboard_employe, name='dashboard_employe'),


    path('projet/creer/', views.creer_projet, name='creer_projet'),
    path('projet/<int:projet_id>/taches/', views.liste_taches_projet, name='liste_taches_projet'),
    path('projet/<int:projet_id>/distribuer/', views.distribuer_taches, name='distribuer_taches'),
    path('projet/<int:projet_id>/tache/etape-1/', views.creer_tache_etape1, name='tache_etape1'),
    path('tache/<int:tache_id>/etape-2/', views.assigner_tache_etape2, name='tache_etape2'),
    path('tache/<int:tache_id>/gerer/', views.gerer_tache_employe, name='gerer_tache_employe'),
    path('tache/<int:tache_id>/details/', views.details_tache, name='details_tache'),
    path('tache/<int:tache_id>/evaluer/', views.evaluer_tache, name='evaluer_tache'),
    path('generer-ia/', views.generer_description_ia, name='generer_ia'),
    path('statistiques/', views.statistiques_chef, name='statistiques_chef'),
    path('employes/supprimer/<int:employe_id>/', views.supprimer_employe, name='supprimer_employe'),
    path('chefs/supprimer/<int:chef_id>/', views.supprimer_chef, name='supprimer_chef'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    