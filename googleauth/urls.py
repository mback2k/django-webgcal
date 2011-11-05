from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib.auth import views
from django.contrib.admin import sites

import views as v

views.login = v.view_login
views.logout = v.view_logout
sites.AdminSite.login = lambda s, r: v.view_login(r)

urlpatterns = patterns('django.contrib.auth.views',
    (r'^%s$' % getattr(settings, 'LOGIN_URL', '/login/')[1:], 'login'),
    (r'^%s$' % getattr(settings, 'LOGOUT_URL', '/logout/')[1:], 'logout'),
)
