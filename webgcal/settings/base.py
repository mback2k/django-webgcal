from .path import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SITE_ID = 1
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'
USE_TZ = True

USE_I18N = True
USE_L10N = True

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
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.csrf',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
)

TEMPLATE_LOADERS = (
  ('django.template.loaders.cached.Loader', (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
  )),
)

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
