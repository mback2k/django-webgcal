import os.path
import gdata.calendar.service
import gdata.auth
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from webgcal.forms import CalendarForm
from webgcal.models import Calendar, Website
from webgcal.tokens import run_on_django
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import messages

def show_home(request):
    return render_to_response('show_home.html', context_instance=RequestContext(request))

@login_required
def show_dashboard(request):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('name')
    create_form = CalendarForm()
    
    calendar_service = run_on_django(gdata.calendar.service.CalendarService(), request)
    
    try:
        calendar_service.AuthSubTokenInfo()
    except (gdata.service.NonAuthSubToken, gdata.service.RequestError):
        messages.warning(request, '<a href="%s">Please connect to your Google Calendar</a>' % reverse('webgcal.views.authsub_request'))

    template_values = {
        'calendars': calendars,
        'create_form': create_form,
        'edit_form': None,
        'calendar': None,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def create_item(request):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('name')
    create_form = CalendarForm(data=request.POST)

    if create_form.is_valid():
        calendar = create_form.save(commit=False)
        calendar.user = request.user
        calendar.save()
        create_form = None

    template_values = {
        'calendars': calendars,
        'create_form': create_form,
        'edit_form': None,
        'calendar': None,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def show_item(request, id):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=id)

    template_values = {
        'calendars': calendars,
        'create_form': None,
        'edit_form': None,
        'calendar': calendar,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def edit_item(request, id):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=id)
    edit_form = CalendarForm(instance=calendar, data=request.POST if request.method == 'POST' else None)
    edit_form.id = calendar.id
    
    if edit_form.is_valid():
        calendar = edit_form.save(commit=False)
        calendar.user = request.user
        calendar.save()
        edit_form = None
    
    template_values = {
        'calendars': calendars,
        'create_form': None,
        'edit_form': edit_form,
        'calendar': calendar,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def delete_item(request, id):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=id)
    calendar.delete()
    create_form = CalendarForm()
    
    messages.success(request, 'Deleted calendar from your Dashboard!')
    
    template_values = {
        'calendars': services,
        'create_form': create_form,
        'edit_form': None,
        'calendar': None,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def delete_item_ask(request, id):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=id)
    create_form = CalendarForm()
    
    messages.warning(request, 'Do you want to delete %s? <a href="%s" title="Yes">Yes</a>' % (calendar, reverse('webgcal.views.delete_item', kwargs={'id': id})))
    
    template_values = {
        'calendars': calendars,
        'create_form': create_form,
        'edit_form': None,
        'calendar': None,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))


@login_required
def authsub_request(request):
    calendar_service = run_on_django(gdata.calendar.service.CalendarService(), request)
    
    try:
        calendar_service.AuthSubTokenInfo()
    except (gdata.service.NonAuthSubToken, gdata.service.RequestError):
        return HttpResponseRedirect(calendar_service.GenerateAuthSubURL(request.build_absolute_uri(reverse('webgcal.views.authsub_response')), 'https://www.google.com/calendar/feeds/', secure=True, session=True))
    
    return HttpResponseRedirect(reverse('webgcal.views.authsub_response'))

@login_required
def authsub_response(request):
    calendar_service = run_on_django(gdata.calendar.service.CalendarService(), request)
    
    session_token = None
    auth_token = gdata.auth.extract_auth_sub_token_from_url(request.get_full_path(), rsa_key=file('%s/certificates/rsakey.pem' % os.path.dirname(__file__), 'r').read())
    
    if auth_token:
        session_token = calendar_service.upgrade_to_session_token(auth_token)
    if session_token:
        calendar_service.token_store.add_token(session_token) 

    return HttpResponseRedirect(reverse('webgcal.views.show_dashboard'))
