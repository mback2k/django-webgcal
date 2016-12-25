# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

def application(environ, *args, **kwargs):
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', environ.get('DJANGO_SETTINGS_MODULE', 'webgcal.settings'))

    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

    return application(environ, *args, **kwargs)
