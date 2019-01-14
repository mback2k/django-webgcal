# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from .common import *

DEBUG = True

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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'webgcal',
    },
    'django-live-templates': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
        },
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

CELERY_BROKER_URL = 'redis://redis:6379/1'
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

ALLOWED_HOSTS = ['localhost']
DEFAULT_FROM_EMAIL = 'no-reply@localhost'

SESSION_COOKIE_NAME = 'webgcal'
SESSION_COOKIE_DOMAIN = 'localhost'
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'THIS_IS_A_DEVELOPMENT_KEY_WHICH_SHOULD_NOT_BE_USED_IN_PRODUCTION!'
