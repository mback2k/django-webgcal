from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials, AccessTokenRefreshError
from social_auth.backends.google import GoogleOAuth2
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import httplib2

def get_social_auth(user):
    if user.is_authenticated():
        try:
            return user.social_auth.get(provider='google-oauth2')
        except ObjectDoesNotExist:
            pass
    return None

def get_credentials(social_auth):
    client_id = getattr(settings, GoogleOAuth2.SETTINGS_KEY_NAME)
    client_secret = getattr(settings, GoogleOAuth2.SETTINGS_SECRET_NAME)

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

def get_calendar_service(session):
    service = build('calendar', 'v3', http=session)
    return service

def check_calendar_access(calendar_service):
    try:
        calendar_service.settings().list().execute()
    except AccessTokenRefreshError:
        return False
    return True