import datetime
from google.appengine.ext import db
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from webgcal.forms import CalendarForm
from webgcal.models import Calendar, Website
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404

def show_home(request):
    return render_to_response('show_home.html', context_instance=RequestContext(request))

@login_required
def show_dashboard(request):
    calendars = Calendar.objects.all().filter(user=request.user).order_by('name')
    create_form = CalendarForm()

    template_values = {
        'calendars': calendars,
        'create_form': create_form,
        'edit_form': None,
        'calendar': None,
        'message': None,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def create_item(request):
    services = Service.objects.all().filter(user=request.user).order_by('-tstamp')
    create_form = ServiceForm(data=request.POST)

    if create_form.is_valid():
        service = create_form.save(commit=False)
        service.user = request.user
        service.save()
        create_form = None

    template_values = {
        'services': services,
        'create_form': create_form,
        'edit_form': None,
        'service': None,
        'message': None,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def show_item(request, id):
    services = Service.objects.all().filter(user=request.user).order_by('-tstamp')
    service = get_object_or_404(Service, user=request.user, id=id)

    Result.objects.all().filter(crdate__lt=datetime.datetime.now()-datetime.timedelta(days=7)).delete()

    template_values = {
        'services': services,
        'create_form': None,
        'edit_form': None,
        'service': service,
        'message': None,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def edit_item(request, id):
    services = Service.objects.all().filter(user=request.user).order_by('-tstamp')
    service = get_object_or_404(Service, user=request.user, id=id)
    edit_form = ServiceForm(instance=service, data=request.POST if request.method == 'POST' else None)
    edit_form.id = service.id
    
    if edit_form.is_valid():
        service = edit_form.save(commit=False)
        service.user = request.user
        service.waiting = True
        service.save()
        edit_form = None
    
    template_values = {
        'services': services,
        'create_form': None,
        'edit_form': edit_form,
        'service': service,
        'message': None,
    }
    
    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def switch_item(request, id):
    services = Service.objects.all().filter(user=request.user).order_by('-tstamp')
    service = get_object_or_404(Service, user=request.user, id=id)
    service.enabled = not(service.enabled)
    service.save()
    create_form = ServiceForm()
    message = 'Switched service %s!' % ('on' if service.enabled else 'off')

    template_values = {
        'services': services,
        'create_form': create_form,
        'edit_form': None,
        'service': None,
        'message': message,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def force_item(request, id):
    services = Service.objects.all().filter(user=request.user).order_by('-tstamp')
    service = get_object_or_404(Service, user=request.user, id=id)
    service.waiting = True
    service.save()
    message = 'The service will be updated on next IP check!'

    template_values = {
        'services': services,
        'create_form': None,
        'edit_form': None,
        'service': service,
        'message': message,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

def feed_item(request, id):
    feed = ResultFeed()
    return feed(request, id)

@login_required
def delete_item(request, id):
    services = Service.objects.all().filter(user=request.user).order_by('-tstamp')
    service = get_object_or_404(Service, user=request.user, id=id)
    service.delete()
    create_form = ServiceForm()
    message = 'Deleted service from your Dashboard!'

    template_values = {
        'services': services,
        'create_form': create_form,
        'edit_form': None,
        'service': None,
        'message': message,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

@login_required
def delete_item_ask(request, id):
    services = Service.objects.all().filter(user=request.user).order_by('-tstamp')
    service = get_object_or_404(Service, user=request.user, id=id)
    create_form = ServiceForm()
    message = 'Do you want to delete %s? <a href="%s" title="Yes">Yes</a>' % (service, reverse('webgcal.views.delete_item', kwargs={'id': id}))

    template_values = {
        'services': services,
        'create_form': create_form,
        'edit_form': None,
        'service': None,
        'message': message,
    }

    return render_to_response('show_dashboard.html', template_values, context_instance=RequestContext(request))

def feed_item_key(request, key):
    from google.appengine.ext import db
    return HttpResponseRedirect(reverse('webgcal.views.feed_item', kwargs={'id': db.Key(key).id()}))
