# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import messages
from .forms import CalendarForm, WebsiteForm
from .models import User, Calendar, Website, Event
from .subtasks.website import task_parse_website
from .subtasks.calendar import task_sync_calendar
from . import google

def migrate_social_auth(request):
    if request.user.is_authenticated():
        if not request.user.social_auth.filter(provider='google-oauth2').exists():
            button = '<a class="ym-button ym-next ym-success float-right" href="%s" title="Migrate Account">Migrate Account</a>' % reverse('social:begin', kwargs={'backend': 'google-oauth2'})
            messages.info(request, '%sPlease migrate your account from Google App Engine to Google OAuth 2.0 for Login (OpenID Connect)' % button)
            return True
    return False

def check_social_auth(request):
    if not migrate_social_auth(request):
        social_auth = google.get_social_auth(request.user)
        if social_auth:
            credentials = google.get_credentials(social_auth)
            session = google.get_session(credentials)
            service = google.get_calendar_service(session)
            if not google.check_calendar_access(service):
                button = '<a class="ym-button ym-next ym-success float-right" href="%s" title="Grant Access">Grant Access</a>' % reverse('socialauth_begin', kwargs={'backend': 'google-oauth2'})
                messages.info(request, '%sPlease grant this application access to your Google Calendar' % button)

def show_home(request):
    check_social_auth(request)

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
    check_social_auth(request)

    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    create_form = CalendarForm()

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

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def create_calendar(request):
    create_form = CalendarForm(data=request.POST)

    if create_form.is_valid():
        calendar = create_form.save(commit=False)
        calendar.user = request.user
        calendar.save()
        return HttpResponseRedirect(reverse('webgcal:show_calendar', kwargs={'calendar_id': calendar.id}))

    calendars = Calendar.objects.filter(user=request.user).order_by('name')

    template_values = {
        'calendars': calendars,
        'calendar_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def edit_calendar(request, calendar_id):
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    if calendar.has_running_task:
        return HttpResponseForbidden('Cannot manipulate calendar with active background task.')

    edit_form = CalendarForm(instance=calendar, data=request.POST if request.method == 'POST' else None)

    if edit_form.is_valid():
        calendar = edit_form.save(commit=False)
        calendar.user = request.user
        calendar.save()
        return HttpResponseRedirect(reverse('webgcal:show_calendar', kwargs={'calendar_id': calendar.id}))

    calendars = Calendar.objects.filter(user=request.user).order_by('name')

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'calendar_edit_form': edit_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def switch_calendar(request, calendar_id):
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    if calendar.has_running_task:
        return HttpResponseForbidden('Cannot manipulate calendar with active background task.')

    calendar.enabled = not(calendar.enabled)
    calendar.save()

    messages.success(request, 'Switched calendar "%s" %s!' % (calendar, 'on' if calendar.enabled else 'off'))

    return HttpResponseRedirect(reverse('webgcal:show_dashboard'))

@login_required
def delete_calendar(request, calendar_id):
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    if calendar.has_running_task:
        return HttpResponseForbidden('Cannot manipulate calendar with active background task.')

    calendar.delete()

    messages.success(request, 'Deleted calendar "%s" from your Dashboard!' % calendar)

    return HttpResponseRedirect(reverse('webgcal:show_dashboard'))

@login_required
def delete_calendar_ask(request, calendar_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    if calendar.has_running_task:
        return HttpResponseForbidden('Cannot manipulate calendar with active background task.')

    create_form = CalendarForm()

    button = '<a class="ym-button ym-delete ym-danger float-right" href="%s" title="Yes">Yes</a>' % reverse('webgcal:delete_calendar', kwargs={'calendar_id': calendar_id})
    messages.warning(request, '%sDo you want to delete calendar "%s"?' % (button, calendar))

    template_values = {
        'calendars': calendars,
        'calendar_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@permission_required('webgcal.change_calendar')
def sync_calendar_now(request, calendar_id):
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    if calendar.has_running_task:
        return HttpResponseForbidden('Cannot manipulate calendar with active background task.')

    args = (request.user.id, calendar.id)
    task_id = 'sync-calendar-%d-%d' % args
    calendar.apply_async(task_sync_calendar, args=args, task_id=task_id, countdown=10)

    messages.info(request, 'Queued syncing of calendar "%s" ...' % calendar)

    return HttpResponseRedirect(reverse('webgcal:show_dashboard'))


@login_required
def create_website(request, calendar_id):
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    create_form = WebsiteForm(data=request.POST)

    if create_form.is_valid():
        website = create_form.save(commit=False)
        website.calendar = calendar
        website.save()
        return HttpResponseRedirect(reverse('webgcal:show_calendar', kwargs={'calendar_id': calendar.id}))

    calendars = Calendar.objects.filter(user=request.user).order_by('name')

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def edit_website(request, calendar_id, website_id):
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    website = get_object_or_404(Website, calendar=calendar, id=website_id)
    if website.has_running_task:
        return HttpResponseForbidden('Cannot manipulate website with active background task.')

    edit_form = WebsiteForm(instance=website, data=request.POST if request.method == 'POST' else None)

    if edit_form.is_valid():
        website = edit_form.save(commit=False)
        website.calendar = calendar
        website.save()
        return HttpResponseRedirect(reverse('webgcal:show_calendar', kwargs={'calendar_id': calendar.id}))

    calendars = Calendar.objects.filter(user=request.user).order_by('name')

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website': website,
        'website_edit_form': edit_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def switch_website(request, calendar_id, website_id):
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    website = get_object_or_404(Website, calendar=calendar, id=website_id)
    if website.has_running_task:
        return HttpResponseForbidden('Cannot manipulate website with active background task.')

    website.enabled = not(website.enabled)
    website.save()

    messages.success(request, 'Switched website "%s" %s!' % (website, 'on' if website.enabled else 'off'))

    return HttpResponseRedirect(reverse('webgcal:show_calendar', kwargs={'calendar_id': calendar.id}))

@login_required
def delete_website(request, calendar_id, website_id):
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    website = get_object_or_404(Website, calendar=calendar, id=website_id)
    if website.has_running_task:
        return HttpResponseForbidden('Cannot manipulate website with active background task.')

    website.delete()

    messages.success(request, 'Deleted website "%s" from your Dashboard!' % website)

    return HttpResponseRedirect(reverse('webgcal:show_calendar', kwargs={'calendar_id': calendar.id}))

@login_required
def delete_website_ask(request, calendar_id, website_id):
    calendars = Calendar.objects.filter(user=request.user).order_by('name')
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    website = get_object_or_404(Website, calendar=calendar, id=website_id)
    if website.has_running_task:
        return HttpResponseForbidden('Cannot manipulate website with active background task.')

    create_form = WebsiteForm()

    button = '<a class="ym-button ym-delete ym-danger float-right" href="%s" title="Yes">Yes</a>' % reverse('webgcal:delete_website', kwargs={'calendar_id': calendar_id, 'website_id': website_id})
    messages.warning(request, '%sDo you want to delete website "%s"?' % (button, website))

    template_values = {
        'calendars': calendars,
        'calendar': calendar,
        'website_create_form': create_form,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@permission_required('webgcal.change_website')
def parse_website_now(request, calendar_id, website_id):
    calendar = get_object_or_404(Calendar, user=request.user, id=calendar_id)
    website = get_object_or_404(Website, calendar=calendar, id=website_id)
    if website.has_running_task:
        return HttpResponseForbidden('Cannot manipulate website with active background task.')

    args = (request.user.id, website.id)
    task_id = 'parse-website-%d-%d' % args
    website.apply_async(task_parse_website, args=args, task_id=task_id, countdown=10)

    messages.info(request, 'Queued parsing of website "%s" ...' % website)

    return HttpResponseRedirect(reverse('webgcal:show_calendar', kwargs={'calendar_id': calendar.id}))


def redirect_login(request):
    from django.conf import settings
    return HttpResponseRedirect(settings.LOGIN_URL)
