import os.path
import gdata.auth
import gdata.calendar.service
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from webgcal.forms import CalendarForm, WebsiteForm
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
        'calendar_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def show_calendar(request, calendar_id):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    create_form = WebsiteForm()

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website_create_form': create_form,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def create_calendar(request):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('name')
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
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
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
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
    calendar.enabled = not(calendar.enabled)
    calendar.save()
    create_form = CalendarForm()
    
    messages.success(request, 'Switched calendar "%s" %s!' % (calendar, 'on' if calendar.enabled else 'off'))
    
    template_values = {
        'calendars': calendars,
        'calendar_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def delete_calendar(request, calendar_id):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
    calendar.delete()
    create_form = CalendarForm()
    
    messages.success(request, 'Deleted calendar "%s" from your Dashboard!' % calendar)
    
    template_values = {
        'calendars': calendars,
        'calendar_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def delete_calendar_ask(request, calendar_id):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
    create_form = CalendarForm()
    
    messages.warning(request, 'Do you want to delete calendar "%s"? <a href="%s" title="Yes">Yes</a>' % (calendar, reverse('webgcal.views.delete_calendar', kwargs={'calendar_id': calendar_id})))
    
    template_values = {
        'calendars': calendars,
        'calendar_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))


@login_required
def create_website(request, calendar_id):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    create_form = WebsiteForm(data=request.POST)
    
    if create_form.is_valid():
        website = create_form.save(commit=False)
        website.calendar = calendar
        website.save()
        return HttpResponseRedirect(reverse('webgcal.views.show_calendar', kwargs={'calendar_id': calendar.id}))

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website_create_form': create_form,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def edit_website(request, calendar_id, website_id):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
    website = get_object_or_404(Website, calendar=calendar, id=website_id, running=False)
    edit_form = WebsiteForm(instance=website, data=request.POST if request.method == 'POST' else None)

    if edit_form.is_valid():
        website = edit_form.save(commit=False)
        website.calendar = calendar
        website.save()
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
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
    website = get_object_or_404(Website, calendar=calendar, id=website_id, running=False)
    website.enabled = not(website.enabled)
    website.save()
    create_form = WebsiteForm()
    
    messages.success(request, 'Switched website "%s" %s!' % (website, 'on' if website.enabled else 'off'))
    
    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website': website,
        'website_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def delete_website(request, calendar_id, website_id):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
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
    calendars = Calendar.objects.all().filter(user=request.user).order_by('-tstamp')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id, running=False)
    website = get_object_or_404(Website, calendar=calendar, id=website_id, running=False)
    create_form = WebsiteForm()
    
    messages.warning(request, 'Do you want to delete website "%s"? <a href="%s" title="Yes">Yes</a>' % (website, reverse('webgcal.views.delete_website', kwargs={'calendar_id': calendar_id, 'website_id': website_id})))
    
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
        return HttpResponseRedirect(calendar_service.GenerateAuthSubURL(request.build_absolute_uri(reverse('webgcal.views.authsub_response')), 'http://www.google.com/calendar/feeds/', secure=True, session=True))
    
    return HttpResponseRedirect(reverse('webgcal.views.authsub_response'))

@login_required
def authsub_response(request):
    calendar_service = run_on_django(gdata.calendar.service.CalendarService(), request)
    
    session_token = None
    auth_token = gdata.auth.extract_auth_sub_token_from_url(request.build_absolute_uri(), rsa_key=file('%s/certificates/rsakey.pem' % os.path.dirname(__file__), 'r').read())
    
    if auth_token:
        session_token = calendar_service.upgrade_to_session_token(auth_token)
    if session_token:
        calendar_service.token_store.add_token(session_token) 

    try:
        calendar_service.AuthSubTokenInfo()
    except gdata.service.RequestError:
        return HttpResponseRedirect(reverse('webgcal.views.authsub_request'))
    else:
        return HttpResponseRedirect(reverse('webgcal.views.show_dashboard'))
