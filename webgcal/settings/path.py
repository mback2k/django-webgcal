# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os.path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(PROJECT_ROOT, '_media')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, '_static')

TEMPLATE_DIR = os.path.join(PROJECT_ROOT, 'templates')

if os.path.exists('/etc/ssl/certs/ca-certificates.crt'):
    os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/certs/ca-certificates.crt'
