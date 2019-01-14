# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from channels.routing import get_default_application
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webgcal.settings")
django.setup()
application = get_default_application()
