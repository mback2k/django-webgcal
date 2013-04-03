import os.path
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(PROJECT_ROOT, '_media')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, '_static')

TEMPLATE_DIRS = (os.path.join(PROJECT_ROOT, 'templates'),)

sys.path.append(PROJECT_ROOT)
