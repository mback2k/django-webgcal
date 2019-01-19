from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
from oauth2client.client import OAuth2Credentials, AccessTokenRefreshError
from social.backends.google import GoogleOAuth2
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import caches
from django.conf import settings
import httplib2

class DjangoDiscoveryCache(Cache):
    def __init__(self):
        self.cache = caches['default']

    def get(self, url):
        return self.cache.get(url, None)

    def set(self, url, content):
        return self.cache.set(url, content)

def get_social_auth(user):
    if user.is_authenticated():
        try:
            return user.social_auth.get(provider='google-oauth2')
        except ObjectDoesNotExist:
            pass
    return None

def get_credentials(social_auth):
    client_id = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
    client_secret = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')

    credentials = OAuth2Credentials(
        access_token=social_auth.extra_data['access_token'],
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=social_auth.extra_data['refresh_token'],
        token_expiry=None,
        token_uri=GoogleOAuth2.ACCESS_TOKEN_URL,
        user_agent='WebGCal/0.1')
    return credentials

def get_session(credentials):
    http = httplib2.Http()
    session = credentials.authorize(http)
    return session

def get_calendar_service(discovery_cache, session):
    service = build('calendar', 'v3', cache=discovery_cache, http=session)
    return service

def build_calendar_service(social_auth):
    credentials = get_credentials(social_auth)
    session = get_session(credentials)
    discovery_cache = DjangoDiscoveryCache()
    service = get_calendar_service(discovery_cache, session)
    return service

def check_calendar_access(calendar_service):
    try:
        calendar_service.settings().list().execute()
    except AccessTokenRefreshError:
        return False
    return True
