from google.appengine.api import users
from django.contrib.auth import logout

class GoogleAccountMiddleware(object):
    def process_request(self, request):
        google_user = users.get_current_user()
        
        if not request.user.is_authenticated():
            return None
            
        if not google_user:
            return logout(request)
            
        if not google_user.user_id() == request.user.password:
            return logout(request)
