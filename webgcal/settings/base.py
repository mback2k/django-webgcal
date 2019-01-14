# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from .path import *

DEBUG = False

SITE_ID = 1
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'
USE_TZ = True

USE_I18N = True
USE_L10N = True

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_OFFLINE = True
COMPRESS_PARSER = 'compressor.parser.HtmlParser'
COMPRESS_OUTPUT_DIR = 'cache'
COMPRESS_CSS_FILTERS = (
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
)
COMPRESS_JS_FILTERS = (
    'compressor.filters.jsmin.JSMinFilter',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'social.apps.django_app.middleware.SocialAuthExceptionMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            TEMPLATE_DIR,
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.csrf',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', (
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                )),
            ]
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'stream': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['stream', 'mail_admins'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django': {
            'handlers': ['stream', 'mail_admins'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
