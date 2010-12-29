import atom
import urllib
import urllib2
import logging
import datetime
import hcalendar
import gdata.service
import gdata.calendar
import gdata.calendar.service
from google.appengine.ext import deferred
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from webgcal.models import Calendar, Website, Event
from webgcal.tokens import run_on_django

def start_worker(request):
    for calendar in Calendar.objects.all():
        for website in calendar.websites:
            deferred.defer(_parse_website, calendar.id, website.id)
    return HttpResponse('deferred')

def update_calendar(request, calendar_id):
    deferred.defer(_update_calendar, calendar_id)
    return HttpResponse('deferred')

def parse_website(request, calendar_id, website_id):
    deferred.defer(_parse_website, calendar_id, website_id)
    return HttpResponse('deferred')


def _update_calendar(calendar_id):    
    try:
        calendar = Calendar.objects.get(id=calendar_id)
    
        if not calendar.enabled:
            return
            
        calendar.running = True
        calendar.errors = 0
        calendar.save()
    
        logging.info('Starting sync of calendar "%s" for "%s"' % (calendar.name, calendar.user))
    
        calendar_service = run_on_django(gdata.calendar.service.CalendarService())
        calendar_service.token_store.user = calendar.user
        calendar_service.AuthSubTokenInfo()
        
        calendar_remote = None
        calendar_feed = None
        
        if calendar.href:
            calendars = calendar_service.GetOwnCalendarsFeed()
            logging.info('Queried calendars feed for user "%s"' % calendar.user)
            
            for cal in calendars.entry:
                if cal.id.text == calendar.href:
                    calendar_remote = cal
                elif cal.summary and cal.summary.text == '%s generated by webgcal.appspot.com' % calendar.name:
                    calendar_service.DeleteCalendarEntry(cal.GetEditLink().href)
        
        if not calendar_remote:
            cal = gdata.calendar.CalendarListEntry()
            cal.title = atom.Title(text=calendar.name)
            cal.summary = atom.Summary(text='%s generated by webgcal.appspot.com' % calendar.name)
            cal.hidden = gdata.calendar.Hidden(value='false')
            cal.selected = gdata.calendar.Selected(value='true')
            
            calendar_remote = calendar_service.InsertCalendar(new_calendar=cal)
            calendar.href = calendar_remote.id.text
            calendar.save()
            logging.info('Inserted calendar "%s" for user "%s"' % (calendar.name, calendar.user))
        
        if calendar_remote:
            for link in calendar_remote.link:
                if link.rel == 'http://schemas.google.com/gCal/2005#eventFeed':
                    calendar_feed = link.href
                    break
            
            if calendar_feed:
                for website in calendar.websites:
                    deferred.defer(_update_calendar_sync, calendar_id, website.id, calendar_feed, _countdown=3)
                    logging.info('Deferred initial sync of calendar "%s" and website "%s" for user "%s"' % (calendar.name, website.name, calendar.user))

    except gdata.service.RequestError, e:
        if e.args[0]['status'] in [401, 302] and calendar.errors < 15:
            calendar.errors += 1
            calendar.save()
            raise deferred.Error(e)
        elif e.args[0]['status'] in [401, 403]:
            calendar.enabled = False
            calendar.running = False
            calendar.errors = 0
            calendar.save()
            raise deferred.PermanentTaskFailure(e)
        else:
            calendar.running = False
            calendar.errors = 0
            calendar.save()
            raise deferred.PermanentTaskFailure(e)
            
    except gdata.service.NonAuthSubToken, e:
        calendar.enabled = False
        calendar.running = False
        calendar.errors = 0
        calendar.save()
        raise deferred.PermanentTaskFailure(e)

    except Calendar.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

def _update_calendar_sync(calendar_id, website_id, calendar_feed, offset=0, limit=5):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
        
        if not calendar.enabled:
            return
            
        website = Website.objects.get(calendar=calendar, id=website_id)
        website.running = True
        website.errors = 0
        website.save()
        
        logging.info('Syncing events from %d to %d of calendar "%s" and website "%s" for "%s"' % (offset, offset+limit, calendar.name, website.name, calendar.user))
            
        calendar_service = run_on_django(gdata.calendar.service.CalendarService())
        calendar_service.token_store.user = calendar.user
        calendar_service.AuthSubTokenInfo()
        
        websites = calendar.websites.count()
        batch = gdata.calendar.CalendarEventFeed()
        
        requests = {}
        for event in website.events[offset:offset+limit]:
            if not website.enabled:
                event.deleted = True
            
            if event.href:
                try:
                    entry = calendar_service.GetCalendarEventEntry(event.href)
                except gdata.service.RequestError, e:
                    if e.args[0]['status'] in [401, 403, 404]:
                        event.href = ''
            
            if event.href:
                if not event.deleted:
                    if websites > 1:
                        entry.title = atom.Title(text=u'%s: %s' % (website.name, event.summary))
                    else:
                        entry.title = atom.Title(text=event.summary)
                    if event.dtstart.hour == 0 and event.dtstart.minute == 0 and event.dtstart.second == 0:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.strftime('%Y-%m-%d'), end_time=(event.dtstart+datetime.timedelta(days=1)).strftime('%Y-%m-%d'))]
                    else:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.strftime('%Y-%m-%dT%H:%M:%S%z'))]
                    entry.transparency = gdata.calendar.Transparency()
                    entry.transparency.value = 'TRANSPARENT'
                    entry.uid = gdata.calendar.UID(value='webgcal-%d' % event.id)
                    entry.batch_id = gdata.BatchId(text='update-request-%d' % event.id)
                    batch.AddUpdate(entry=entry)
                    requests[entry.batch_id.text] = event
                    logging.info('%s %s' % (entry.batch_id.text, event.summary))
                    
                else:
                    entry.batch_id = gdata.BatchId(text='delete-request-%d' % event.id)
                    batch.AddDelete(entry=entry)
                    requests[entry.batch_id.text] = event
                    logging.info('%s %s' % (entry.batch_id.text, event.summary))
            
            else:
                if not event.deleted:
                    entry = gdata.calendar.CalendarEventEntry()
                    if websites > 1:
                        entry.title = atom.Title(text=u'%s: %s' % (website.name, event.summary))
                    else:
                        entry.title = atom.Title(text=event.summary)
                    if event.dtstart.hour == 0 and event.dtstart.minute == 0 and event.dtstart.second == 0:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.strftime('%Y-%m-%d'), end_time=(event.dtstart+datetime.timedelta(days=1)).strftime('%Y-%m-%d'))]
                    else:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.strftime('%Y-%m-%dT%H:%M:%S%z'))]
                    entry.transparency = gdata.calendar.Transparency()
                    entry.transparency.value = 'TRANSPARENT'
                    entry.uid = gdata.calendar.UID(value='webgcal-%d' % event.id)
                    entry.batch_id = gdata.BatchId(text='insert-request-%d' % event.id)
                    batch.AddInsert(entry=entry)
                    requests[entry.batch_id.text] = event
                    logging.info('%s %s' % (entry.batch_id.text, event.summary))
                    
                else:
                    event.delete()
                    
        logging.info('Fetching event feed')
        calendar_events = calendar_service.GetCalendarEventFeed(calendar_feed)
        logging.info('Executing batch request')
        result = calendar_service.ExecuteBatch(batch, calendar_events.GetBatchLink().href)
        logging.info('Executed batch request')
        
        for entry in result.entry:
            if entry.batch_id and entry.batch_id.text in requests:
                if entry.batch_status.code in ['200', '201']:
                    logging.info('%s %s %s' % (entry.batch_id.text, entry.batch_status.code, entry.batch_status.reason))
                    event = requests[entry.batch_id.text]
                    if event.deleted and entry.batch_operation.type == gdata.BATCH_DELETE:
                        event.delete()
                    elif not event.href:
                        event.href = entry.id.text
                        event.save()
                elif not entry.batch_status.code in ['409']:
                    logging.error(entry)
            else:
                logging.warning(entry)
        
        if offset+limit < website.events.count():
            deferred.defer(_update_calendar_sync, calendar_id, website_id, calendar_feed, offset+limit, limit, _countdown=1)
            logging.info('Deferred additional sync of calendar "%s" and website "%s" for user "%s"' % (calendar.name, website.name, calendar.user))
        else:
            website.running = False
            website.save()
            logging.info('Finished sync of calendar "%s" and website "%s" for %s' % (calendar.name, website.name, calendar.user))
        
        if not calendar.websites.filter(running=True).count():
            calendar = Calendar.objects.get(id=calendar_id)
            calendar.running = False
            calendar.update = datetime.datetime.now()
            calendar.save()
            logging.info('Finished sync of calendar "%s" for %s' % (calendar.name, calendar.user))

    except gdata.service.RequestError, e:
        if e.args[0]['status'] in [401, 302] and website.errors < 15:
            website.errors += 1
            website.save()
            raise deferred.Error(e)
        elif e.args[0]['status'] in [401, 403]:
            website.enabled = False
            website.running = False
            website.errors = 0
            website.save()
            raise deferred.PermanentTaskFailure(e)
        else:
            website.running = False
            website.errors = 0
            website.save()
            raise deferred.PermanentTaskFailure(e)
            
    except gdata.service.NonAuthSubToken, e:
        website.enabled = False
        website.running = False
        website.errors = 0
        website.save()
        raise deferred.PermanentTaskFailure(e)

    except Calendar.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

    except Website.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

def _parse_website(calendar_id, website_id):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
        website = Website.objects.get(calendar=calendar, id=website_id)
        
        if not website.enabled:
            return
            
        website.running = True
        website.save()
        
        logging.info('Parsing website %s for %s' % (website.name, calendar.user))
        
        events_remote = {}
        html = urllib2.urlopen(urllib2.Request(website.href, headers={'User-agent': 'WebGCal'})).read()
        for cal in hcalendar.hCalendar(html):
            for event in cal:
                if event.summary and event.dtstart:
                    events_remote[hash(event.summary)^hash(event.dtstart)] = event
        
        logging.info('Parsed website %s for %s' % (website.name, calendar.user))
        
        events = {}
        for event in website.events.all():
            events[hash(event.summary)^hash(event.dtstart)] = event
        
        logging.info('Updating website %s for %s' % (website.name, calendar.user))
        
        for key, event_remote in events_remote.iteritems():
            if not key in events:
                Event.objects.create(website=website, summary=event_remote.summary, dtstart=event_remote.dtstart)
            else:
                save = False
                event = events[key]
                if event.summary != event_remote.summary:
                    event.summary = event_remote.summary
                    save = True
                if event.dtstart != event_remote.dtstart:
                    event.dtstart = event_remote.dtstart
                    save = True
                if save:
                    event.save()
        
        for key, event in events.iteritems():
            if not key in events_remote:
                event.deleted = True
                event.save()
                
        website.running = False
        website.update = datetime.datetime.now()
        website.save()
        logging.info('Updated website %s for %s' % (website.name, calendar.user))
        
        if not calendar.websites.filter(running=True).count():
            deferred.defer(_update_calendar, calendar_id, _countdown=3)
            logging.info('Deferred calendar %s sync for %s' % (calendar.name, calendar.user))
        
    except Calendar.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)
        
    except Website.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)
