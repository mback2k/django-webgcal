import os.path
import gdata.auth
import gdata.calendar.service
from googledata import run_on_django
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import messages
from webgcal.forms import CalendarForm, WebsiteForm
from webgcal.models import User, Calendar, Website, Event
from webgcal import tasks, google

with open(os.path.join(os.path.dirname(__file__), 'secure/RSA_KEY'), 'r') as f:
    RSA_KEY = f.read().strip()

def check_authsub(request):
    calendar_service = run_on_django(gdata.calendar.service.CalendarService(), request)
    
    try:
        calendar_service.AuthSubTokenInfo()
    except (gdata.service.NonAuthSubToken, gdata.service.RequestError):
        button = '<a class="ym-button ym-next float-right" href="%s" title="Connect">Connect</a>' % reverse('webgcal.views.authsub_request')
        messages.warning(request, '%sPlease connect to your Google Calendar' % button)

def check_social_auth(request):
    if request.user.is_authenticated():
        for social_auth in request.user.social_auth.all():
            if social_auth.provider == 'google-oauth2':
                return None
        return HttpResponseRedirect(reverse('socialauth_begin', kwargs={'backend': 'google-oauth2'}))
    return None

def show_home(request):
    check = check_social_auth(request)
    if check:
        return check

    social_auth = google.get_social_auth(request.user)
    if social_auth:
        credentials = google.get_credentials(social_auth)
        service = google.get_calendar_service(credentials)
        if not google.check_calendar_access(service):
            button = '<a class="ym-button ym-next float-right" href="%s" title="Grant Access">Grant Access</a>' % reverse('socialauth_begin', kwargs={'backend': 'google-oauth2'})
            messages.warning(request, '%sYou need to grant this application access to your Google Calendar' % button)

    users = User.objects.filter(is_active=True).count()
    calendars = Calendar.objects.filter(enabled=True).count()
    websites = Website.objects.filter(enabled=True).count()

    template_values = {
        'users': users,
        'calendars': calendars,
        'websites': websites,
    }

    return render_to_response('show_home.html', template_values, context_instance=RequestContext(request))

@login_required
def show_dashboard(request):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    create_form = CalendarForm()
    
    check_authsub(request)

    template_values = {
        'calendars': calendars,
        'calendar_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def show_calendar(request, calendar_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    create_form = WebsiteForm()
    
    check_authsub(request)

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website_create_form': create_form,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def create_calendar(request):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    create_form = CalendarForm(data=request.POST)

    if create_form.is_valid():
        calendar = create_form.save(commit=False)
        calendar.user = request.user
        calendar.save()
        return HttpResponseRedirect(reverse('webgcal.views.show_calendar', kwargs={'calendar_id': calendar.id}))

    template_values = {
        'calendars': calendars,
        'calendar_create_form': create_form,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def edit_calendar(request, calendar_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
    edit_form = CalendarForm(instance=calendar, data=request.POST if request.method == 'POST' else None)

    if edit_form.is_valid():
        calendar = edit_form.save(commit=False)
        calendar.user = request.user
        calendar.save()
        return HttpResponseRedirect(reverse('webgcal.views.show_calendar', kwargs={'calendar_id': calendar.id}))
    
    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'calendar_edit_form': edit_form,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def switch_calendar(request, calendar_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
    calendar.enabled = not(calendar.enabled)
    calendar.save()
    
    messages.success(request, 'Switched calendar "%s" %s!' % (calendar, 'on' if calendar.enabled else 'off'))
    
    return HttpResponseRedirect(reverse('webgcal.views.show_dashboard'))

@login_required
def delete_calendar(request, calendar_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
    Website.objects.filter(calendar=calendar).delete()
    calendar.delete()
    create_form = CalendarForm()
    
    messages.success(request, 'Deleted calendar "%s" from your Dashboard!' % calendar)
    
    check_authsub(request)
    
    template_values = {
        'calendars': calendars,
        'calendar_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def delete_calendar_ask(request, calendar_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
    create_form = CalendarForm()

    button = '<a class="ym-button ym-delete float-right" href="%s" title="Yes">Yes</a>' % reverse('webgcal.views.delete_calendar', kwargs={'calendar_id': calendar_id})    
    messages.warning(request, '%sDo you want to delete calendar "%s"?' % (button, calendar))

    template_values = {
        'calendars': calendars,
        'calendar_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))


@login_required
def create_website(request, calendar_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    create_form = WebsiteForm(data=request.POST)
    
    if create_form.is_valid():
        website = create_form.save(commit=False)
        website.calendar = calendar
        website.save()
        tasks.task_parse_website.delay(calendar.id, website.id)
        return HttpResponseRedirect(reverse('webgcal.views.show_calendar', kwargs={'calendar_id': calendar.id}))

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website_create_form': create_form,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def edit_website(request, calendar_id, website_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    website = get_object_or_404(Website, calendar=calendar, id=website_id, running=False)
    edit_form = WebsiteForm(instance=website, data=request.POST if request.method == 'POST' else None)

    if edit_form.is_valid():
        website = edit_form.save(commit=False)
        website.calendar = calendar
        website.save()
        tasks.task_parse_website.delay(calendar.id, website.id)
        return HttpResponseRedirect(reverse('webgcal.views.show_calendar', kwargs={'calendar_id': calendar.id}))
    
    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website': website,
        'website_edit_form': edit_form,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def switch_website(request, calendar_id, website_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    website = get_object_or_404(Website, calendar=calendar, id=website_id, running=False)
    website.enabled = not(website.enabled)
    website.save()
    
    messages.success(request, 'Switched website "%s" %s!' % (website, 'on' if website.enabled else 'off'))
    
    return HttpResponseRedirect(reverse('webgcal.views.show_calendar', kwargs={'calendar_id': calendar.id}))

@login_required
def delete_website(request, calendar_id, website_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    website = get_object_or_404(Website, calendar=calendar, id=website_id, running=False)
    website.delete()
    create_form = WebsiteForm()
    
    messages.success(request, 'Deleted website "%s" from your Dashboard!' % website)

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website_create_form': create_form,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def delete_website_ask(request, calendar_id, website_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    website = get_object_or_404(Website, calendar=calendar, id=website_id, running=False)
    create_form = WebsiteForm()

    button = '<a class="ym-button ym-delete float-right" href="%s" title="Yes">Yes</a>' % reverse('webgcal.views.delete_website', kwargs={'calendar_id': calendar_id, 'website_id': website_id})    
    messages.warning(request, '%sDo you want to delete website "%s"?' % (button, website))

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))


@login_required
def authsub_request(request):
    calendar_service = run_on_django(gdata.calendar.service.CalendarService(), request)
    
    try:
        calendar_service.AuthSubTokenInfo()
    
    except (gdata.service.NonAuthSubToken, gdata.service.RequestError):
        calendar_service.token_store.remove_all_tokens()
        
        absolute_url = request.build_absolute_uri(reverse('webgcal.views.authsub_response'))
        redirect_url = calendar_service.GenerateAuthSubURL(absolute_url, 'http://www.google.com/calendar/feeds/', secure=True, session=True)
        
        return HttpResponseRedirect(redirect_url)
    
    return HttpResponseRedirect(reverse('webgcal.views.authsub_response'))

@login_required
def authsub_response(request):
    calendar_service = run_on_django(gdata.calendar.service.CalendarService(), request)

    absolute_url = request.build_absolute_uri()
    auth_token = gdata.auth.extract_auth_sub_token_from_url(absolute_url, rsa_key=RSA_KEY)

    if auth_token:
        calendar_service.UpgradeToSessionToken(auth_token)

    try:
        calendar_service.AuthSubTokenInfo()

    except gdata.service.RequestError:
        return HttpResponseRedirect(reverse('webgcal.views.authsub_request'))

    else:
        return HttpResponseRedirect(reverse('webgcal.views.show_dashboard'))


@login_required
def test_resource_method(request, resource, method):
    social_auth = google.get_social_auth(request.user)
    if not social_auth:
        return HttpResponseForbidden()

    credentials = google.get_credentials(social_auth)
    service = google.get_calendar_service(credentials)
    if not google.check_calendar_access(service):
        return HttpResponseForbidden()

    resource = getattr(service, resource)()
    method = getattr(resource, method)()
    result = method.execute()

    return HttpResponse('%s' % result, mimetype='text/plain')

def redirect_login(request):
    from django.conf import settings
    return HttpResponseRedirect(settings.LOGIN_URL)
