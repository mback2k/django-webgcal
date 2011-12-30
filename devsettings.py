from basesettings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

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

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'THIS_IS_A_DEVELOPMENT_KEY_WHICH_SHOULD_NOT_BE_USED_IN_PRODUCTION!'
