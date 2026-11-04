from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def admin_requis(vue):
    """Réservé aux administrateurs (rôle ADMIN ou superutilisateur)."""
    @login_required
    @wraps(vue)
    def _vue(request, *args, **kwargs):
        if not request.user.est_admin:
            raise PermissionDenied
        return vue(request, *args, **kwargs)
    return _vue


def chef_requis(vue):
    """Réservé aux chefs de projet."""
    @login_required
    @wraps(vue)
    def _vue(request, *args, **kwargs):
        if not request.user.est_chef:
            raise PermissionDenied
        return vue(request, *args, **kwargs)
    return _vue


def employe_requis(vue):
    """Réservé aux employés."""
    @login_required
    @wraps(vue)
    def _vue(request, *args, **kwargs):
        if not request.user.est_employe:
            raise PermissionDenied
        return vue(request, *args, **kwargs)
    return _vue
