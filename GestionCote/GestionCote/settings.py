# GestionCote/settings.py

from pathlib import Path
import os
import sys
from django.contrib.messages import constants as messages

# ========== BASE DIRECTORY ==========
BASE_DIR = Path(__file__).resolve().parent.parent

# ========== SECURITY ==========
# Utiliser une variable d'environnement pour la clé secrète
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-)sul!3m)n8x5b_svh%$rqldj_2=8%974z^&309dm&!(&f9*0#-')

# DEBUG doit être False en production
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Pour PythonAnywhere, Railway, etc.
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'votre-nom-utilisateur.pythonanywhere.com',  # À remplacer par votre URL
    '*.pythonanywhere.com',
    '*.railway.app',
    '*.onrender.com',
    'Fabric5716.github.io',  # Si vous utilisez GitHub Pages
]

# ========== APPLICATIONS ==========
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Cote',  # Votre application
]

# ========== MIDDLEWARE ==========
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Pour servir les fichiers statiques en production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ========== URLS ==========
ROOT_URLCONF = 'GestionCote.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'GestionCote.wsgi.application'

# ========== DATABASE ==========
# Garder SQLite pour le développement, mais prévoir PostgreSQL pour la production
if os.environ.get('DATABASE_URL'):
    # Pour PostgreSQL (Railway, Heroku, etc.)
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
    }
else:
    # SQLite pour le développement
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ========== VALIDATEURS DE MOTS DE PASSE ==========
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ========== INTERNATIONALISATION ==========
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_TZ = True

# ========== FICHIERS STATIQUES ET MÉDIAS ==========
STATIC_URL = '/static/'

# Dossier où Django cherche les fichiers statiques pendant le développement
STATICFILES_DIRS = [BASE_DIR / 'static']

# Dossier où Django collecte les fichiers statiques pour la production
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configuration pour Whitenoise (servir les fichiers statiques en production)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Fichiers médias (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ========== PARAMÈTRES DE SESSION ==========
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 28800  # 8 heures
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True

# ========== AUTHENTIFICATION ==========
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# ========== MESSAGES ==========
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# ========== DEFAUT ==========
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========== SÉCURITÉ HTTPS (Pour la production) ==========
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'