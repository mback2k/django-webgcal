from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto import Random

import time
import zlib
import base64
import pickle

RNG = Random.new().read

with open('googleauth/keypair/PRIVATE_KEY', 'r') as f:
  PRIVATE_KEY = RSA.importKey(f.read())

with open('googleauth/keypair/REMOTE_KEY', 'r') as f:
  REMOTE_KEY = RSA.importKey(f.read())
  
def redirect_request(request):
    request_data = {}
    request_data['time'] = time.time()
    request_data['location'] = request.build_absolute_uri(request.path + '?rsp=%(rsp)s&sig=%(sig)s')
    
    req = pickle.dumps(request_data)
    sig = SHA256.new(req).digest()
    
    enc_req = REMOTE_KEY.encrypt(req, RNG)
    enc_sig = PRIVATE_KEY.sign(sig, RNG)
    
    pkl_req = pickle.dumps(enc_req)
    pkl_sig = pickle.dumps(enc_sig)
    
    gzp_req = zlib.compress(pkl_req, 9)
    gzp_sig = zlib.compress(pkl_sig, 9)
    
    b64_req = base64.urlsafe_b64encode(gzp_req)
    b64_sig = base64.urlsafe_b64encode(gzp_sig)
    
    return HttpResponseRedirect('https://uxnrauth.appspot.com/auth/?req=%(req)s&sig=%(sig)s' % {'req': b64_req, 'sig': b64_sig})

def parse_response(request):
    if not 'rsp' in request.GET:
        return redirect_request(request)
      
    if not 'sig' in request.GET:
      return redirect_request(request)

    b64_rsp = request.GET['rsp']
    b64_sig = request.GET['sig']
    
    if not b64_rsp or not b64_sig:
        return redirect_request(request)
    
    gzp_rsp = base64.urlsafe_b64decode(b64_rsp.encode('ascii'))
    gzp_sig = base64.urlsafe_b64decode(b64_sig.encode('ascii'))
    
    if not gzp_rsp or not gzp_sig:
        return redirect_request(request)
    
    pkl_rsp = zlib.decompress(gzp_rsp)
    pkl_sig = zlib.decompress(gzp_sig)
    
    if not pkl_rsp or not pkl_sig:
        return redirect_request(request)
      
    enc_rsp = pickle.loads(pkl_rsp)
    enc_sig = pickle.loads(pkl_sig)
    
    if not enc_rsp or not enc_sig:
        return redirect_request(request)
    
    rsp = PRIVATE_KEY.decrypt(enc_rsp)
    sig = SHA256.new(rsp).digest()
    
    if not REMOTE_KEY.verify(sig, enc_sig):
        return redirect_request(request)

    response_data = pickle.loads(rsp)
    
    if not 'time' in response_data:
        return redirect_request(request)
      
    if time.time() > response_data['time'] + 15:
        return redirect_request(request)
    
    if not 'email' in response_data:
        return redirect_request(request)
      
    if not 'user_id' in response_data:
        return redirect_request(request)
      
    if not 'nickname' in response_data:
        return redirect_request(request)
      
    if not 'is_admin' in response_data:
        return redirect_request(request)
      
    return response_data

def view_login(request):
    google_user = parse_response(request)
    
    if isinstance(google_user, HttpResponse):
        return google_user

    try:
        user = User.objects.get(password=google_user['user_id'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        
    except User.DoesNotExist:
        user = User.objects.create(username=google_user['nickname'].split('@', 1)[0], password=google_user['user_id'], email=google_user['email'], is_staff=google_user['is_admin'], is_superuser=google_user['is_admin'], first_name='', last_name='')
        user.backend = 'django.contrib.auth.backends.ModelBackend'

    if user:
        login(request, user)
        
    return HttpResponseRedirect(getattr(settings, 'LOGIN_REDIRECT_URL', '/'))
    
def view_logout(request):
    logout(request)
    
    return HttpResponseRedirect(getattr(settings, 'LOGOUT_REDIRECT_URL', '/'))
