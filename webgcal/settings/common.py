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

    'djcelery',
    'djcelery_model',

    'social.apps.django_app.default',
    'social_appengine_auth',

    'webgcal.libs.yamlcss',
    'webgcal.libs.jdatetime',
    'webgcal.libs.keeperr',

    'webgcal.apps.webgcal',

    'django.contrib.admin',
    'django.contrib.admindocs',

    'swampdragon',
    'compressor',
)

AUTHENTICATION_BACKENDS = (
    'social.backends.google.GoogleOAuth2',
    'social_appengine_auth.backends.GoogleAppEngineOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

TEMPLATE_CONTEXT_PROCESSORS += (
    'webgcal.apps.webgcal.context_processors.dragon_url',
)

LOGIN_BACKEND = 'google-appengine-oauth2'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_ERROR_URL = LOGIN_REDIRECT_URL
LOGIN_URL = '/login/%s/' % LOGIN_BACKEND
LOGOUT_URL = '/logout/?next=%s' % LOGOUT_REDIRECT_URL

CELERY_RESULT_BACKEND = 'djcelery.backends.database.DatabaseBackend'
CELERY_TRACK_STARTED = True
CELERY_SEND_EVENTS = True
CELERY_SEND_TASK_SENT_EVENT = True
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = CELERY_TASK_SERIALIZER
CELERY_ACCEPT_CONTENT = [CELERY_TASK_SERIALIZER]

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

SOCIAL_AUTH_GOOGLE_OAUTH2_USE_UNIQUE_USER_ID = True
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {'access_type': 'offline', 'approval_prompt': 'force'}

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')

SOCIAL_AUTH_GOOGLE_APPENGINE_OAUTH2_USE_UNIQUE_USER_ID = SOCIAL_AUTH_GOOGLE_OAUTH2_USE_UNIQUE_USER_ID

SOCIAL_AUTH_GOOGLE_APPENGINE_OAUTH2_KEY = SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
SOCIAL_AUTH_GOOGLE_APPENGINE_OAUTH2_SECRET = SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

SWAMP_DRAGON_CONNECTION = ('webgcal.libs.connection.MysqlHeartbeatConnection', '/data')
