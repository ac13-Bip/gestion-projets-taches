"""
Configuration Django du projet gemploye (ProTask — gestion de projets et de tâches).

Toutes les valeurs sensibles ou propres à une machine sont lues depuis des variables
d'environnement, éventuellement définies dans le fichier .env (à côté de manage.py).
Voir .env.example pour la liste complète.
"""

import importlib.util
import os
from pathlib import Path

from django.contrib.messages import constants as message_constants
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Chargement des variables d'environnement depuis le fichier .env (non versionné)
_env_file = BASE_DIR / '.env'
if _env_file.exists():
    for _line in _env_file.read_text(encoding='utf-8').splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))


def env_bool(nom, defaut=False):
    return os.environ.get(nom, str(defaut)).strip().lower() in ('1', 'true', 'yes', 'oui', 'on')


def env_liste(nom, defaut=''):
    return [v.strip() for v in os.environ.get(nom, defaut).split(',') if v.strip()]


# ==========================================
# SÉCURITÉ
# ==========================================
DEBUG = env_bool('DJANGO_DEBUG', True)

_CLE_DEV = 'django-insecure-cle-de-developpement-uniquement'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', _CLE_DEV)
if not DEBUG and SECRET_KEY == _CLE_DEV:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY doit être définie quand DJANGO_DEBUG=False.")

ALLOWED_HOSTS = env_liste('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost' if DEBUG else '')
CSRF_TRUSTED_ORIGINS = env_liste('DJANGO_CSRF_TRUSTED_ORIGINS')

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '3600'))
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 8  # déconnexion automatique après 8 h


# ==========================================
# APPLICATIONS
# ==========================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gestion_taches',
]

# Thème Jazzmin pour l'admin, seulement s'il est installé
if importlib.util.find_spec('jazzmin') is not None:
    INSTALLED_APPS.insert(0, 'jazzmin')
    JAZZMIN_SETTINGS = {
        'site_title': 'ProTask',
        'site_header': 'ProTask',
        'site_brand': 'ProTask',
        'welcome_sign': 'Administration de ProTask',
        'copyright': 'ProTask',
        'search_model': ['gestion_taches.Utilisateur', 'gestion_taches.Projet'],
        'show_ui_builder': False,
    }

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gemploye.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,  # les templates sont dans gestion_taches/templates/
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gemploye.wsgi.application'


# ==========================================
# BASE DE DONNÉES
# DB_ENGINE=postgresql (défaut) ou sqlite (pratique pour tester rapidement)
# ==========================================
if os.environ.get('DB_ENGINE', 'postgresql').lower() == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'GestionEmploye_DB'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==========================================
# AUTHENTIFICATION
# ==========================================
AUTH_USER_MODEL = 'gestion_taches.Utilisateur'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard_redirect'
LOGOUT_REDIRECT_URL = 'login'


# ==========================================
# LANGUE ET FUSEAU HORAIRE
# ==========================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'Africa/Casablanca')
USE_I18N = True
USE_TZ = True


# ==========================================
# FICHIERS STATIQUES ET LIVRABLES
# ==========================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024


# ==========================================
# MESSAGES (classes Bootstrap)
# ==========================================
MESSAGE_TAGS = {message_constants.ERROR: 'danger'}


# ==========================================
# JOURNALISATION
# ==========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'gestion_taches': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}
