"""Configuration des URLs du projet gemploye.

Les URLs de l'application sont définies dans gestion_taches/urls.py.
"""
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "ProTask — Administration"
admin.site.site_title = "ProTask"
admin.site.index_title = "Gestion de projets et de tâches"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gestion_taches.urls')),
]

# Les livrables (media/) ne sont PAS servis publiquement : ils passent par la vue
# protégée « telecharger_rendu », qui vérifie les droits de l'utilisateur.
