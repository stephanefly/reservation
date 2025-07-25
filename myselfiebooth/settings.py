"""
Django settings for myselfiebooth project.

Generated by 'django-admin startproject' using Django 4.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
import yaml

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_YML = os.path.join(BASE_DIR, 'myselfiebooth', 'settings.yaml')
with open(STATIC_YML, 'r') as yaml_file:
    config = yaml.safe_load(yaml_file)

TIME_ZONE = 'UTC'  # Ou tout autre fuseau horaire approprié
USE_TZ = True

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config.get('SECRET_KEY')
KEY_TRELLO = config.get('key'),
TOKEN_TRELLO = config.get('token')
PDF_REPERTORY = config.get('PDF_REPERTORY')
MAIL_TEMPLATE_REPOSITORY = config.get('MAIL_TEMPLATE_REPOSITORY')


TITULAIRE_DU_COMPTE_A = config.get('TITULAIRE_DU_COMPTE_A')
IBAN_A = config.get('IBAN_A')
BIC_A = config.get('BIC_A')

TITULAIRE_DU_COMPTE_B = config.get('TITULAIRE_DU_COMPTE_B')
IBAN_B = config.get('IBAN_B')
BIC_B = config.get('BIC_B')

MAIL_MYSELFIEBOOTH = config.get('MAIL_MYSELFIEBOOTH')
MAIL_BCC = config.get('MAIL_BCC')
MP = config.get('MP')

API_PCLOUD_URL = config.get("API_PCLOUD_URL")
ACCESS_TOKEN = config.get("ACCESS_TOKEN")  # Remplacez par le token obtenu
ROOT_FOLDER_ID = config.get("ROOT_FOLDER_ID")  # ID du dossier racine
ROOT_FOLDER_PREPA_ID = config.get("ROOT_FOLDER_PREPA_ID")  # ID du dossier racine
ROOT_FOLDER_MONTAGE_2025 = config.get("ROOT_FOLDER_MONTAGE_2025")  # ID du dossier racine
ROOT_FOLDER_MONTAGE_2026 = config.get("ROOT_FOLDER_MONTAGE_2026")  # ID du dossier racine

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config.get('DEBUG')

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
    'bootstrap5',
    "django_forms_bootstrap",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'myselfiebooth.middleware.BackendAuthMiddleware',
    'myselfiebooth.middleware.TeamOnlyMiddleware',  # Assure-toi de mettre le chemin correct vers le middleware

]

LOGIN_REDIRECT_URL = 'backend/lst_devis/'

ROOT_URLCONF = 'myselfiebooth.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Correction ici
        'DIRS': [os.path.join(BASE_DIR, 'app', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',  # Correction ici
                'django.template.context_processors.request',  # Correction ici
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

WSGI_APPLICATION = 'myselfiebooth.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = config.get('DATABASES')

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
# settings.py
LOGOUT_REDIRECT_URL = '/login/'  # Par exemple, redirection vers la page d'accueil
