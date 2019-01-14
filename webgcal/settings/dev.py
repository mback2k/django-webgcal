# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from .common import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'devdatabase.sqlite',           # Or path to database file if using sqlite3.
        'USER': '',                             # Not used with sqlite3.
        'PASSWORD': '',                         # Not used with sqlite3.
        'HOST': '',                             # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                             # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': { }
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

DRAGON_URL = 'http://localhost:9999/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'THIS_IS_A_DEVELOPMENT_KEY_WHICH_SHOULD_NOT_BE_USED_IN_PRODUCTION!'
