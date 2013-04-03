import djcelery
djcelery.setup_loader()

def application(environ, *args, **kwargs):
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', environ.get('DJANGO_SETTINGS_MODULE', 'webgcal.settings'))
    os.environ.setdefault('CELERY_LOADER', environ.get('CELERY_LOADER', 'django'))

    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

    return application(environ, *args, **kwargs)
