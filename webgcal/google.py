import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials, AccessTokenRefreshError
from social_auth.backends.google import GoogleOAuth2
from django.conf import settings

def get_social_auth(user):
    if user.is_authenticated():
        for social_auth in user.social_auth.all():
            if social_auth.provider == 'google-oauth2':
                return social_auth
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

def get_calendar_service(credentials):
    http = httplib2.Http()
    http = credentials.authorize(http)

    service = build('calendar', 'v3', http=http)
    return service

def check_calendar_access(calendar_service):
    try:
        calendar_service.settings().list().execute()
    except AccessTokenRefreshError:
        return False
    return True
