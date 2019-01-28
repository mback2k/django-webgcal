# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import Celery, signals
import os

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webgcal.settings')

app = Celery('webgcal')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Use Django logging settings for Celery logging.
@signals.setup_logging.connect
def setup_logging(*args, **kwargs):
    from django.conf import settings
    from django.utils.log import configure_logging
    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)
