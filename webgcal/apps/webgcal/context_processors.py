# -*- coding: utf-8 -*-
from django.conf import settings

def dragon_url(request):
    return {'DRAGON_URL': settings.DRAGON_URL}
