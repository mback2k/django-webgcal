import atom
import random
import urllib
import urllib2
import logging
import datetime
import hcalendar
import gdata.service
import gdata.calendar
import gdata.calendar.service
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from webgcal.models import Calendar, Website, Event
from webgcal.tokens import run_on_django
from webgcal import deferred

def start_worker(request):
    for calendar in Calendar.objects.all():
        deferred.defer('update_website_wait', calendar.id, _update_website_wait, calendar.id, _countdown=60)
        for website in calendar.websites:
            deferred.defer('parse_website', website.id, _parse_website, calendar.id, website.id)
    return HttpResponse('deferred')

def update_calendar(request, calendar_id):
    deferred.defer('update_calendar', calendar_id, _update_calendar, calendar_id)
    return HttpResponse('deferred')

def parse_website(request, calendar_id, website_id):
    deferred.defer('parse_website', website_id, _parse_website, calendar_id, website_id)
    return HttpResponse('deferred')


def _update_calendar(calendar_id):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
    
        if not calendar.enabled:
            return
            
        calendar.running = True
        calendar.status = 'Syncing calendar'
        calendar.errors = 0
        calendar.save()
    
        logging.info('Starting sync of calendar "%s" for "%s"' % (calendar, calendar.user))
    
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
                    deferred.defer('update_calendar_sync', website.id, _update_calendar_sync, calendar_id, website.id, calendar_feed, _countdown=3)
                    logging.info('Deferred initial sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, calendar.user))
                    
        deferred.defer('update_calendar_wait', calendar_id, _update_calendar_wait, calendar_id, _countdown=60)
        
        logging.info('Deferred sync of calendar "%s" for user %s"' % (calendar, calendar.user))

    except gdata.service.RequestError, e:
        if e.args[0]['status'] in [401, 302] and calendar.errors < 15:
            calendar.errors += 1
            calendar.save()
            raise deferred.Error(e)
        elif e.args[0]['status'] in [401, 403]:
            calendar.enabled = False
            calendar.running = False
            calendar.status = 'Error: %s' % _parse_request_error(e.args[0])
            calendar.errors = 0
            calendar.save()
            raise deferred.PermanentTaskFailure(e)
        else:
            calendar.running = False
            calendar.status = 'Error: %s' % _parse_request_error(e.args[0])
            calendar.errors = 0
            calendar.save()
            raise deferred.PermanentTaskFailure(e)
            
    except gdata.service.NonAuthSubToken, e:
        calendar.enabled = False
        calendar.running = False
        calendar.status = 'Error: NonAuthSubToken'
        calendar.errors = 0
        calendar.save()
        raise deferred.PermanentTaskFailure(e)

    except Calendar.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

def _update_calendar_sync(calendar_id, website_id, calendar_feed, cursor=None, limit=5):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
        website = Website.objects.get(calendar=calendar, id=website_id)
        
        website.running = True
        website.status = 'Syncing calendar'
        website.errors = 0
        website.save()
        
        logging.info('Syncing %d events after cursor "%s" of calendar "%s" and website "%s" for "%s"' % (limit, cursor, calendar, website, calendar.user))
            
        calendar_service = run_on_django(gdata.calendar.service.CalendarService())
        calendar_service.token_store.user = calendar.user
        calendar_service.AuthSubTokenInfo()
        
        websites = calendar.websites.count()
        batch = gdata.calendar.CalendarEventFeed()
        
        requests = {}
        timeout = datetime.datetime.now()-datetime.timedelta(days=1)
        events = website.events
        if cursor:
            events = events.filter(dtstart__gt=cursor)
        for event in events[:limit]:
            if event.href and (event.synced < event.parsed or event.synced < timeout):
                try:
                    entry = calendar_service.GetCalendarEventEntry(event.href)
                except gdata.service.RequestError, e:
                    if e.args[0]['status'] in [401, 403, 404]:
                        event.href = None
            
            if not event.href and website.enabled:            
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

            elif event.synced < event.parsed:
                if not event.deleted and website.enabled:
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
        
        if requests:
            logging.info('Fetching event feed')
            calendar_events = calendar_service.GetCalendarEventFeed(calendar_feed)
            logging.info('Executing batch request')
            result = calendar_service.ExecuteBatch(batch, calendar_events.GetBatchLink().href)
            logging.info('Executed batch request')
            
            sync_datetime = datetime.datetime.now()
            
            for entry in result.entry:
                if entry.batch_id and entry.batch_id.text in requests:
                    if entry.batch_status.code in ['200', '201']:
                        logging.info('%s %s %s' % (entry.batch_id.text, entry.batch_status.code, entry.batch_status.reason))
                        event = requests[entry.batch_id.text]
                        if entry.batch_operation.type == gdata.BATCH_DELETE:
                            if event.deleted:
                                event.delete()
                            else:
                                event.href = None
                                event.synced = sync_datetime
                                event.save()
                        else:
                            event.href = entry.id.text
                            event.synced = sync_datetime
                            event.save()
                    elif entry.batch_status.code == '400':
                        event.href = None
                        event.save()
                    elif not entry.batch_status.code == '409':
                        logging.error(entry)
                else:
                    logging.warning(entry)
        
        if events.count() > limit:
            deferred.defer('update_calendar_sync', website_id, _update_calendar_sync, calendar_id, website_id, calendar_feed, events[limit].dtstart, limit, _countdown=1)
            logging.info('Deferred additional sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, calendar.user))
        else:
            website.running = False
            website.status = 'Finished syncing website'
            website.save()
            logging.info('Finished sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, calendar.user))
            
    except gdata.service.RequestError, e:
        if e.args[0]['status'] in [401, 302] and website.errors < 15:
            website.errors += 1
            website.save()
            raise deferred.Error(e)
        elif e.args[0]['status'] in [401, 403]:
            website.enabled = False
            website.running = False
            website.status = 'Error: %s' % _parse_request_error(e.args[0])
            website.errors = 0
            website.save()
            raise deferred.PermanentTaskFailure(e)
        else:
            website.running = False
            website.errors = 0
            website.status = 'Error: %s' % _parse_request_error(e.args[0])
            website.save()
            raise deferred.PermanentTaskFailure(e)
            
    except gdata.service.NonAuthSubToken, e:
        website.enabled = False
        website.running = False
        website.status = 'Error: NonAuthSubToken'
        website.errors = 0
        website.save()
        raise deferred.PermanentTaskFailure(e)

    except Calendar.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

    except Website.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

def _update_calendar_wait(calendar_id):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
        
        if not calendar.websites.filter(running=True).count():
            calendar.running = False
            calendar.updated = datetime.datetime.now()
            calendar.status = 'Finished syncing calendar'
            calendar.save()
            logging.info('Finished sync of calendar "%s" for user "%s"' % (calendar, calendar.user))
            
        else:
            deferred.defer('update_calendar_wait', calendar_id, _update_calendar_wait, calendar_id, _countdown=60)
        
    except Calendar.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

def _update_website_wait(calendar_id):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
        
        if not calendar.enabled:
            return
            
        if not calendar.websites.filter(running=True).count():
            deferred.defer('update_calendar', calendar_id, _update_calendar, calendar_id, _countdown=3)
            logging.info('Deferred sync of calendar "%s" for user "%s"' % (calendar, calendar.user))
            
        else:
            deferred.defer('update_website_wait', calendar_id, _update_website_wait, calendar_id, _countdown=60)
        
    except Calendar.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

def _parse_website(calendar_id, website_id, limit=20):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
        website = Website.objects.get(calendar=calendar, id=website_id)
        
        if not website.enabled:
            return
            
        website.running = True
        website.status = 'Parsing website'
        website.save()
        
        logging.info('Parsing website "%s" for user "%s"' % (website, calendar.user))
        
        parse_id = random.randint(0, 1000000)
        
        website_html = urllib2.urlopen(urllib2.Request(website.href, headers={'User-agent': 'WebGCal'})).read()
        for calendar_data in hcalendar.hCalendar(website_html):
            for event_index in range(0, len(calendar_data), limit):
                event_html = ''.join(map(str, calendar_data[event_index:event_index+limit]))
                deferred.defer('parse_website_event', website_id, _parse_website_event, calendar_id, website_id, parse_id, event_html)
        
        deferred.defer('parse_website_wait', website_id, _parse_website_wait, calendar_id, website_id, parse_id, _countdown=30)
        
        logging.info('Deferred event parsing of website "%s" for user %s"' % (website, calendar.user))
        
    except urllib2.URLError, e:
        website.enabled = False
        website.running = False
        website.status = 'Error: %s' % e.reason
        website.save()
        raise deferred.PermanentTaskFailure(e)
        
    except Calendar.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)
        
    except Website.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

def _parse_website_event(calendar_id, website_id, parse_id, event_html):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
        website = Website.objects.get(calendar=calendar, id=website_id)
        
        logging.info('Parsing events of website %s for user "%s"' % (website, calendar.user))
        
        parse_datetime = datetime.datetime.now()
        
        for calendar_data in hcalendar.hCalendar(event_html):
            for event_data in calendar_data:
                if event_data.summary and event_data.dtstart:
                    try:
                        event = Event.objects.get(website=website, summary=event_data.summary, dtstart=event_data.dtstart)
                        event.parse = parse_id
                        #event.parsed = parse_datetime # This should only be updated if fields change
                        event.save()
                    except Event.DoesNotExist:
                        event = Event.objects.create(website=website, summary=event_data.summary, dtstart=event_data.dtstart, parse=parse_id, parsed=parse_datetime)
        
    except Calendar.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)
        
    except Website.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

def _parse_website_wait(calendar_id, website_id, parse_id):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
        website = Website.objects.get(calendar=calendar, id=website_id)
        
        if not deferred.deferred(name='parse_website_event', reference_id=website_id):
            logging.info('Deleting missing events of website "%s" for user "%s"' % (website, calendar.user))
            
            for event in Event.objects.filter(website=website).exclude(parse=parse_id):
                event.deleted = True
                event.save()
                
            logging.info('Deleted missing events of website "%s" for user "%s"' % (website, calendar.user))
            
            website.running = False
            website.updated = datetime.datetime.now()
            website.status = 'Finished parsing website'
            website.save()
            logging.info('Parsed all events of website "%s" for user "%s"' % (website, calendar.user))
                            
        else:
            deferred.defer('parse_website_wait', website_id, _parse_website_wait, calendar_id, website_id, parse_id, _countdown=30)
        
    except Calendar.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)
        
    except Website.DoesNotExist, e:
        raise deferred.PermanentTaskFailure(e)

def _parse_request_error(error):
    if 'body' in error:
        return hcalendar.BeautifulSoup.BeautifulSoup(error['body']).find('title').string.decode('utf-8')
