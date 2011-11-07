from store import DjangoTokenStore

def run_on_django(gdata_service, request=None, store_tokens=True, single_user_mode=False, deadline=10):
    try:
        import google.appengine
    except:
        pass
    else:
        from gdata.alt.appengine import run_on_appengine
        gdata_service = run_on_appengine(gdata_service, deadline=deadline)

    try:
        gdata_service._SetSessionId(None)
    except:
        pass

    gdata_service.token_store = DjangoTokenStore(request)
    gdata_service.auto_store_tokens = store_tokens
    gdata_service.auto_set_current_token = single_user_mode

    return gdata_service
