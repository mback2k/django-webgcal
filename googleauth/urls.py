from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('django.contrib.auth.views',
    (r'^%s$' % getattr(settings, 'LOGIN_URL', '/login/')[1:], 'login'),
    (r'^%s$' % getattr(settings, 'LOGOUT_URL', '/logout/')[1:], 'logout'),
)

from django.contrib.auth import views, authenticate, login as user_login, logout as user_logout
from django.contrib.admin import sites

def login(request):
    from google.appengine.api import users
    from django.core.urlresolvers import reverse
    from django.http import HttpResponseRedirect
    from django.conf import settings
    
    user = authenticate()
    if user:
        user_login(request, user)
        return HttpResponseRedirect(getattr(settings, 'LOGIN_REDIRECT_URL', '/'))
    
    return HttpResponseRedirect(users.create_login_url(reverse('django.contrib.auth.views.login')))
    
def logout(request):
    from google.appengine.api import users
    from django.http import HttpResponseRedirect
    from django.conf import settings
    
    user_logout(request)
    
    return HttpResponseRedirect(users.create_logout_url(getattr(settings, 'LOGOUT_REDIRECT_URL', '/')))

views.login = login
views.logout = logout
sites.AdminSite.login = lambda s, r: login(r)
