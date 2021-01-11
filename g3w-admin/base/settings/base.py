"""
Django settings for qdjango2 project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'y#-4cgqw2(zyt1uy_(l5sa(xq550*6$s#3y*r=v+6#wb6^3(4)'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost']


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    #'django.contrib.sites'
]

THIRD_PARTY_APPS = [
    'django_file_form',
    'django_file_form.ajaxuploader',
    'model_utils',
    'formtools',
    'crispy_forms',
    'guardian',
    'sitetree',
    'django_extensions',
    'rest_framework',
    'rest_framework_gis',
    'rest_framework.authtoken',
    'import_export',
    'mptt',
    'ordered_model',
    'ajax_select',
    'djcelery',
    'modeltranslation',
    'debug_toolbar',
]

G3WADMIN_APPS = [
    'base',
    'core',
    'client',
    'usersmanage',
    'OWS'
]

G3WADMIN_PROJECT_APPS_BASE = [
    'qdjango'
]

G3WADMIN_PROJECT_APPS = []


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    #'django_user_agents.middleware.UserAgentMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]

G3WADMIN_MIDDLEWARE = []

ROOT_URLCONF = 'base.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '../templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'base.context_processors.global_settings'
            ],
            'loaders': [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader'
                    #('django.template.loaders.cached.Loader', [
                    #    'django.template.loaders.filesystem.Loader',
                    #    'django.template.loaders.app_directories.Loader'
                    #]),
            ]
        },

    },
]

WSGI_APPLICATION = 'base.wsgi.application'


ATOMIC_REQUESTS = True

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend'
)

GUARDIAN_RAISE_403 = True

CRISPY_TEMPLATE_PACK = 'bootstrap3'

SITETREE_MODEL_TREE = 'core.G3W2Tree'
SITETREE_MODEL_TREE_ITEM = 'core.G3W2TreeItem'


LOGIN_URL = 'login'
LOGOUT_NEXT_PAGE = '/'
LOGIN_REDIRECT_URL = '/'

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'it-it'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


LOCALE_PATHS = (
    BASE_DIR + '/../locale',
)

gettext = lambda s: s
LANGUAGES = (
    ('it', 'Italian'),
    ('en', 'English'),
    ('fi', 'Finnish'),
    ('se', 'Swedish')
)

MODELTRANSLATION_DEFAULT_LANGUAGE = 'it'

# if prefix for default language put in to url
PREFIX_DEFAULT_LANGUAGE = True


# for sessions
SESSION_COOKIE_NAME = 'g3wadmin_sessionid'

# FOR rest_framework
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'core.api.base.views.G3WExceptionHandler',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'UNICODE_JSON': False
}

# FOR MEDIA
MEDIA_ROOT = '/home/www/django-qgis-static/media/'
MEDIA_URL = '/media/'

# FOR USER MEDIA DIR (IN PARTICULAR FOR EDITING MODULE)
USER_MEDIA_ROOT = None

# For Data gis source
DATASOURCE_PATH = ''

# for django-file-form
MUST_LOGIN = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

SITE_TITLE = 'g3w-admin'

# for qdjango module, this is the base URL for WMS/WFS visible by the client
QDJANGO_SERVER_URL = 'http://localhost'
QDJANGO_PRJ_CACHE_KEY = 'qdjango_prj_{}'

# data for proxy server
PROXY_SERVER = False

# LOGGING_CONFIG = None

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/tmp/debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}


MGC = '-99:dodfEz3K2rziGayGnw_FyOuWdCM'
MPC = '-99:dodfEz3K2rziGayGnw_FyOuWdCM'

FRONTEND = False
FRONTEND_APP = 'frontend'

SENTRY = False

SITE_PREFIX_URL = None

# CLIENT SETTINGS
CLIENTS_AVAILABLE = []
CLIENT_DEFAULT = 'client'
CLIENT_G3WSUITE_LOGO = 'g3wsuite_logo_h40.png'
CLIENT_OWS_METHOD = 'GET'
G3W_CLIENT_SEARCH_ENDPOINT = 'ows' #or 'api' for to use api layer vector with FieldFilterBackend

SITE_ID = 1


INTERNAL_IPS = [
    '127.0.0.1'
]


# DJANGO-FILE-FORM SETTINGS
# -------------------------
FILE_FORM_UPLOAD_BACKEND = 'core.utils.response.G3WFileFormUploadBackend'

G3WADMIN_VECTOR_LAYER_DOWNLOAD_FORMATS = ['shp', 'xls', 'csv']

# Setting to activate/deactivate user password reset by email.
RESET_USER_PASSWORD = False

# QPLOTLY DEFAULT SETTINGS
# ------------------------

LOAD_QPLOTLY_FROM_PROJECT = False
