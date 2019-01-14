# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = (
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'', include('webgcal.apps.webgcal.urls', namespace='webgcal')),
    url(r'', include('social_django.urls', namespace='social')),
    url(r'', include('django.contrib.auth.urls')),
)
