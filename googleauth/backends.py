from google.appengine.api import users
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class GoogleAccountBackend(ModelBackend):
    def authenticate(self):
        google_user = users.get_current_user()
        
        if not google_user:
            return None
            
        try:
            return User.objects.get(password=google_user.user_id())
            
        except User.DoesNotExist:
            return User.objects.create(username=google_user.nickname().split('@', 1)[0], password=google_user.user_id(), email=google_user.email(), is_staff=users.is_current_user_admin(), is_superuser=users.is_current_user_admin(), first_name='', last_name='')
