from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('django.contrib.auth.views',
    (r'^%s$' % getattr(settings, 'LOGIN_URL', '/login/')[1:], 'login'),
    (r'^%s$' % getattr(settings, 'LOGOUT_URL', '/logout/')[1:], 'logout'),
)

from django.contrib.auth import views, authenticate, login, logout
from django.contrib.admin import sites

def view_login(request):
    from google.appengine.api import users
    from django.core.urlresolvers import reverse
    from django.http import HttpResponseRedirect
    from django.conf import settings
    
    user = authenticate()
    if user:
        login(request, user)
        return HttpResponseRedirect(getattr(settings, 'LOGIN_REDIRECT_URL', '/'))
    
    return HttpResponseRedirect(users.create_login_url(reverse('django.contrib.auth.views.login')))
    
def view_logout(request):
    from google.appengine.api import users
    from django.http import HttpResponseRedirect
    from django.conf import settings
    
    logout(request)
    
    return HttpResponseRedirect(users.create_logout_url(getattr(settings, 'LOGOUT_REDIRECT_URL', '/')))

views.login = view_login
views.logout = view_logout
sites.AdminSite.login = lambda s, r: login(r)
