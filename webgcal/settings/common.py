import djcelery
djcelery.setup_loader()

from .base import *
import os

ROOT_URLCONF = 'webgcal.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'south',
    'djcelery',
    'social_auth',
    'appengine_auth',

    'webgcal.libs.yamlcss',
    'webgcal.libs.jdatetime',
    'webgcal.libs.keeperr',

    'webgcal.apps.webgcal',

    'django.contrib.admin',
    'django.contrib.admindocs',

    'compressor',
)

AUTHENTICATION_BACKENDS = (
    'appengine_auth.backends.GoogleAppEngineOAuthBackend',
    'social_auth.backends.google.GoogleOAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_BACKEND = 'google-appengine-oauth'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_ERROR_URL = LOGIN_REDIRECT_URL
LOGIN_URL = '/login/%s/' % LOGIN_BACKEND
LOGOUT_URL = '/logout/?next=%s' % LOGOUT_REDIRECT_URL

CELERY_RESULT_BACKEND = 'djcelery.backends.database.DatabaseBackend'
CELERY_TRACK_STARTED = True
CELERY_SEND_EVENTS = True
CELERY_SEND_TASK_SENT_EVENT = True

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

GOOGLE_APPENGINE_OAUTH_SERVER = 'oauth-profile.appspot.com'
GOOGLE_APPENGINE_OAUTH_USE_UNIQUE_USER_ID = True

GOOGLE_OAUTH2_USE_UNIQUE_USER_ID = True
GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {'access_type': 'offline', 'approval_prompt': 'force'}
GOOGLE_OAUTH_EXTRA_SCOPE = ['https://www.googleapis.com/auth/calendar']

GOOGLE_OAUTH2_CLIENT_ID = os.environ.get('GOOGLE_OAUTH2_CLIENT_ID', '')
GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET', '')
