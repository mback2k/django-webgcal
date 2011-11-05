from django.core.cache import cache
from models import TokenCollection
import atom.http_interface
import atom.token_store
import pickle

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


class DjangoTokenStore(atom.token_store.TokenStore):
    def __init__(self, request):
        self.user = request.user if request else None

    def add_token(self, token):
        tokens = load_auth_tokens(self.user)
        
        if not hasattr(token, 'scopes') or not token.scopes:
            return False
            
        for scope in token.scopes:
            tokens[str(scope)] = token
        
        key = save_auth_tokens(tokens, self.user)
        return True if key else False

    def find_token(self, url):
        if url is None:
            return None
            
        if isinstance(url, (str, unicode)):
            url = atom.url.parse_url(url)
            
        tokens = load_auth_tokens(self.user)
        if url in tokens:
            token = tokens[url]
            if token.valid_for_scope(url):
                return token
            else:
                del tokens[url]
                save_auth_tokens(tokens, self.user)
        
        for scope, token in tokens.iteritems():
            if token.valid_for_scope(url):
                return token
                
        return atom.http_interface.GenericToken()

    def remove_token(self, token):
        token_found = False
        scopes_to_delete = []
        tokens = load_auth_tokens(self.user)
        
        for scope, stored_token in tokens.iteritems():
            if stored_token == token:
                scopes_to_delete.append(scope)
                token_found = True
                
        for scope in scopes_to_delete:
            del tokens[scope]
            
        if token_found:
            save_auth_tokens(tokens, self.user)
            
        return token_found

    def remove_all_tokens(self):
        save_auth_tokens({}, self.user)


def save_auth_tokens(token_dict, user=None):
    if user is None:
        return None
    
    pickled_tokens = pickle.dumps(token_dict)
    cache.set('gdata_pickled_tokens:%s' % user, pickled_tokens)
    
    try:  
        user_tokens = TokenCollection.objects.get(user=user)
    except TokenCollection.DoesNotExist:
        user_tokens = None        
    
    if user_tokens:
        user_tokens.pickled_tokens = pickled_tokens
        return user_tokens.save()
    else:
        user_tokens = TokenCollection(user=user, pickled_tokens=pickled_tokens)
        return user_tokens.save()
     

def load_auth_tokens(user=None):
    if user is None:
        return {}
        
    pickled_tokens = cache.get('gdata_pickled_tokens:%s' % user, {})
    if pickled_tokens:
        try:
            return pickle.loads(pickled_tokens)
        except:
            pass
    
    try:  
        user_tokens = TokenCollection.objects.get(user=user)
    except TokenCollection.DoesNotExist:
        user_tokens = None
        
    if user_tokens:
        cache.set('gdata_pickled_tokens:%s' % user, user_tokens.pickled_tokens)
        try:
            return pickle.loads(user_tokens.pickled_tokens)
        except:
            pass
    
    return {}
