from .common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',   # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'docker',                       # Or path to database file if using sqlite3.
        'USER': 'docker',                       # Not used with sqlite3.
        'PASSWORD': 'docker',                   # Not used with sqlite3.
        'HOST': 'db',                           # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',                         # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {
            'init_command': 'SET storage_engine=InnoDB',
        }
    }
}
DATABASES['default']['ENGINE'] = 'transaction_hooks.backends.mysql'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

BROKER_URL = 'redis://redis:6379/1'
CELERY_RESULT_BACKEND = BROKER_URL

SWAMP_DRAGON_REDIS_HOST = 'redis'
SWAMP_DRAGON_HOST = '0.0.0.0'
SWAMP_DRAGON_PORT = 9999
DRAGON_URL = 'http://dockerhost:9999/'

ALLOWED_HOSTS = ['dockerhost']
DEFAULT_FROM_EMAIL = 'no-reply@dockerhost'

SESSION_COOKIE_NAME = 'webgcal'
SESSION_COOKIE_DOMAIN = 'dockerhost'
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'THIS_IS_A_DEVELOPMENT_KEY_WHICH_SHOULD_NOT_BE_USED_IN_PRODUCTION!'
