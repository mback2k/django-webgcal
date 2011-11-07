from django.conf import settings
from django.conf.urls.defaults import *
import django.contrib.auth.views
import django.contrib.admin.sites
import views

django.contrib.auth.views.login = views.view_login
django.contrib.auth.views.logout = lambda request, **kwargs: views.view_logout(request)

django.contrib.admin.sites.AdminSite.login = lambda site, request: views.view_login(request)
django.contrib.admin.sites.AdminSite.logout = lambda site, request, **kwargs: views.view_logout(request)

urlpatterns = patterns('django.contrib.auth.views',
    (r'^%s$' % getattr(settings, 'LOGIN_URL', '/login/')[1:], 'login'),
    (r'^%s$' % getattr(settings, 'LOGOUT_URL', '/logout/')[1:], 'logout'),
)
