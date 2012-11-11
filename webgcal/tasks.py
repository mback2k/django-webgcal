import bs4
import atom
import pytz
import random
import urllib2
import logging
import datetime
import hcalendar
import gdata.service
import gdata.calendar
import gdata.calendar.service
from googledata import run_on_django
from celery.schedules import crontab
from celery.task import task, periodic_task
from django.utils import timezone
from django.db.models import Q, F
from webgcal.models import Calendar, Website, Event

@periodic_task(run_every=crontab(minute=0))
def task_start_worker():
    for calendar in Calendar.objects.filter(enabled=True):
        task_update_website_wait.apply_async(args=[calendar.id], countdown=60)

        for website in calendar.websites.filter(enabled=True):
            task_parse_website.apply_async(args=[calendar.id, website.id])

@task(default_retry_delay=60, max_retries=15)
def task_update_calendar(calendar_id):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
    
        if not calendar.enabled:
            return
            
        calendar.running = True
        calendar.status = 'Syncing calendar'
        calendar.save()
    
        logging.info('Starting sync of calendar "%s" for "%s"' % (calendar, calendar.user))
    
        calendar_service = run_on_django(gdata.calendar.service.CalendarService(), deadline=30)
        calendar_service.token_store.user = calendar.user
        
        calendar_remote = None
        
        if calendar.href:
            calendars = calendar_service.GetOwnCalendarsFeed()
            logging.info('Queried calendars feed for user "%s"' % calendar.user)
            
            for cal in calendars.entry:
                if cal.id.text == calendar.href:
                    calendar_remote = cal
                elif cal.summary and cal.summary.text == u'%s generated by webgcal.appspot.com' % calendar.name:
                    calendar_service.DeleteCalendarEntry(cal.GetEditLink().href)
        
        if not calendar_remote:
            cal = gdata.calendar.CalendarListEntry()
            cal.title = atom.Title(text=calendar.name)
            cal.summary = atom.Summary(text='%s generated by webgcal.appspot.com' % calendar.name)
            cal.hidden = gdata.calendar.Hidden(value='false')
            cal.selected = gdata.calendar.Selected(value='true')
            
            calendar_remote = calendar_service.InsertCalendar(new_calendar=cal)
            calendar.href = calendar_remote.id.text
            calendar.feed = ''
            calendar.save()
            logging.info('Inserted calendar "%s" for user "%s"' % (calendar.name, calendar.user))
        
        if calendar_remote:
            if not calendar.feed:
                for link in calendar_remote.link:
                    if link.rel == 'http://schemas.google.com/gCal/2005#eventFeed':
                        calendar.feed = link.href
                        calendar.save()
                        break
            
            if calendar.feed:
                for website in calendar.websites:
                    task_update_calendar_sync.apply_async(args=[calendar_id, website.id], countdown=3)
                    
                    logging.info('Deferred initial sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, calendar.user))
                    
        task_update_calendar_wait.apply_async(args=[calendar_id], countdown=60)
        
        logging.info('Deferred sync of calendar "%s" for user %s"' % (calendar, calendar.user))

    except gdata.service.RequestError, e:
        if e.args[0]['status'] in [401, 302] and calendar.errors < 15:
            calendar.errors += 1
            calendar.save()
            task_update_calendar.retry(exc=e)

        elif e.args[0]['status'] in [401, 403]:
            calendar.enabled = False
            calendar.running = False
            calendar.status = 'Error: %s' % _parse_request_error(e.args[0])
            calendar.errors = 0
            calendar.save()

        else:
            calendar.running = False
            calendar.status = 'Error: %s' % _parse_request_error(e.args[0])
            calendar.errors = 0
            calendar.save()

    except gdata.service.NonAuthSubToken, e:
        calendar.enabled = False
        calendar.running = False
        calendar.status = 'Error: NonAuthSubToken'
        calendar.errors = 0
        calendar.save()

    except Calendar.DoesNotExist, e:
        pass

    except Exception, e:
        calendar.enabled = False
        calendar.running = False
        calendar.status = 'Error: Fatal error'
        calendar.errors = 0
        calendar.save()

@task(default_retry_delay=60, max_retries=15)
def task_update_calendar_sync(calendar_id, website_id, cursor=None, limit=25):
    try:
        calendar = Calendar.objects.get(id=calendar_id)

        if not calendar.enabled:
            return

        website = Website.objects.get(calendar=calendar, id=website_id)

        if not website.enabled:
            return
        
        website.running = True
        website.status = 'Syncing website (%d/%d)' % (website.events.filter(id__lt=cursor).count() if cursor else 0, website.events.count())
        website.save()
        
        logging.info('Syncing %d events after cursor "%s" of calendar "%s" and website "%s" for "%s"' % (limit, cursor, calendar, website, calendar.user))
            
        calendar_service = run_on_django(gdata.calendar.service.CalendarService(), deadline=30)
        calendar_service.token_store.user = calendar.user
        calendar_events = calendar_service.GetCalendarEventFeed(calendar.feed)
        
        sync_datetime = timezone.now()
        sync_timeout = timezone.now()-datetime.timedelta(days=1)
        
        websites = calendar.websites.count()
        events = website.events.filter(Q(href='') | Q(deleted=True) | Q(synced__lt=F('parsed')) | Q(synced__lt=sync_timeout))

        if cursor:
            events = events.filter(id__gte=cursor)
        try:
            events_user = calendar.feed.split('/')[5]
        except:
            events_user = None

        entries = {}
        requests = {}
        batch = gdata.calendar.CalendarEventFeed()

        for event in events[:limit]:
            if event.href:
                if not events_user or not events_user in event.href:
                    event.href = ''
                    event.save()

                else:
                    batch_id = 'query-request-%d' % event.id
                    batch.AddQuery(url_string=event.href, batch_id_string=batch_id)
                    requests[batch_id] = event
                    logging.info('%s %s' % (batch_id, event.summary))

        if requests:
            logging.info('Executing batch request')
            result = calendar_service.ExecuteBatch(batch, calendar_events.GetBatchLink().href)
            logging.info('Executed batch request')
            
            for entry in result.entry:
                if entry.batch_id and entry.batch_id.text in requests:
                    event = requests[entry.batch_id.text]
                    if int(entry.batch_status.code) == 200:
                        entries[event.id] = entry
                    elif int(entry.batch_status.code) == 404:
                        event.href = ''
                        event.save()
                    elif int(entry.batch_status.code) >= 500:
                        logging.error('Event %d:' % event.id)
                        logging.error(entry)
                else:
                    logging.warning(entry)

        requests = {}
        batch = gdata.calendar.CalendarEventFeed()

        for event in events[:limit]:
            if not event.href:
                if not event.deleted and website.enabled:
                    entry = gdata.calendar.CalendarEventEntry()
                    if websites > 1:
                        entry.title = atom.Title(text=u'%s: %s' % (website.name, event.summary))
                    else:
                        entry.title = atom.Title(text=event.summary)
                    if event.dtstart.hour == 0 and event.dtstart.minute == 0 and event.dtstart.second == 0 and not event.dtend:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.isoformat().split('T')[0], end_time=(event.dtstart+datetime.timedelta(days=1)).isoformat().split('T')[0])]
                    elif event.dtstart.hour == 0 and event.dtstart.minute == 0 and event.dtstart.second == 0 and event.dtend.hour == 0  and event.dtend.minute == 0 and event.dtend.second == 0:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.isoformat().split('T')[0], end_time=(event.dtend+datetime.timedelta(days=1)).isoformat().split('T')[0])]
                    elif event.dtend:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.isoformat(), end_time=event.dtend.isoformat())]
                    else:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.isoformat())]
                    if event.location:
                        entry.where = [gdata.calendar.Where(value_string=event.location)]
                    if event.status:
                        entry.status = gdata.calendar.EventStatus(text=event.status.upper())
                    if event.description:
                        entry.content = atom.Content(text=event.description)
                    entry.transparency = gdata.calendar.Transparency()
                    entry.transparency.value = 'TRANSPARENT'
                    entry.uid = gdata.calendar.UID(value='webgcal-%d' % event.id)
                    entry.batch_id = gdata.BatchId(text='insert-request-%d' % event.id)
                    batch.AddInsert(entry=entry)
                    requests[entry.batch_id.text] = event
                    logging.info('%s %s' % (entry.batch_id.text, event.summary))
                    
                else:
                    event.delete()

            elif event.id in entries and (event.deleted or event.synced < event.parsed):
                entry = entries[event.id]
                if not event.deleted and website.enabled:
                    if websites > 1:
                        entry.title = atom.Title(text=u'%s: %s' % (website.name, event.summary))
                    else:
                        entry.title = atom.Title(text=event.summary)
                    if event.dtstart.hour == 0 and event.dtstart.minute == 0 and event.dtstart.second == 0 and not event.dtend:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.isoformat().split('T')[0], end_time=(event.dtstart+datetime.timedelta(days=1)).isoformat().split('T')[0])]
                    elif event.dtstart.hour == 0 and event.dtstart.minute == 0 and event.dtstart.second == 0 and event.dtend.hour == 0  and event.dtend.minute == 0 and event.dtend.second == 0:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.isoformat().split('T')[0], end_time=(event.dtend+datetime.timedelta(days=1)).isoformat().split('T')[0])]
                    elif event.dtend:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.isoformat(), end_time=event.dtend.isoformat())]
                    else:
                        entry.when = [gdata.calendar.When(start_time=event.dtstart.isoformat())]
                    if event.location:
                        entry.where = [gdata.calendar.Where(value_string=event.location)]
                    if event.status:
                        entry.status = gdata.calendar.EventStatus(text=event.status.upper())
                    if event.description:
                        entry.content = atom.Content(text=event.description)
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
                    
            elif event.synced < sync_timeout:
                event.synced = sync_datetime
                event.save()
        
        if requests:
            logging.info('Executing batch request')
            result = calendar_service.ExecuteBatch(batch, calendar_events.GetBatchLink().href)
            logging.info('Executed batch request')
            
            for entry in result.entry:
                if entry.batch_id and entry.batch_id.text in requests:
                    event = requests[entry.batch_id.text]
                    if int(entry.batch_status.code) in (200, 201):
                        logging.info('%s %s %s' % (entry.batch_id.text, entry.batch_status.code, entry.batch_status.reason))
                        if entry.batch_operation.type == gdata.BATCH_DELETE:
                            if event.deleted:
                                event.delete()
                            else:
                                event.href = ''
                                event.synced = sync_datetime
                                event.save()
                        else:
                            event.href = entry.id.text
                            event.synced = sync_datetime
                            event.save()
                    elif int(entry.batch_status.code) == 404:
                        event.href = ''
                        event.save()
                    elif int(entry.batch_status.code) == 409:
                        event.delete()
                    elif int(entry.batch_status.code) >= 500:
                        logging.error('Event %d:' % event.id)
                        logging.error(entry)
                else:
                    logging.warning(entry)
        
        if events.count() > limit:
            task_update_calendar_sync.apply_async(args=[calendar_id, website_id, events[limit].id, limit], countdown=2)

            logging.info('Deferred additional sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, calendar.user))
            
        else:
            website.running = False
            website.status = 'Finished syncing website'
            website.errors = 0
            website.save()
            logging.info('Finished sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, calendar.user))
            
    except gdata.service.RequestError, e:
        if e.args[0]['status'] in [401, 302] and website.errors < 15:
            website.errors += 1
            website.save()
            task_update_calendar_sync.retry(exc=e)

        elif e.args[0]['status'] in [401, 403]:
            website.enabled = False
            website.running = False
            website.status = 'Error: %s' % _parse_request_error(e.args[0])
            website.errors = 0
            website.save()

        else:
            website.running = False
            website.errors = 0
            website.status = 'Error: %s' % _parse_request_error(e.args[0])
            website.save()
            
    except gdata.service.NonAuthSubToken, e:
        website.enabled = False
        website.running = False
        website.status = 'Error: NonAuthSubToken'
        website.errors = 0
        website.save()

    except Calendar.DoesNotExist, e:
        pass

    except Website.DoesNotExist, e:
        pass

    except Exception, e:
        website.enabled = False
        website.running = False
        website.status = 'Error: Fatal error'
        website.errors = 0
        website.save()

@task(default_retry_delay=30)
def task_update_calendar_wait(calendar_id):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
        
        if not calendar.websites.filter(running=True).count():
            calendar.running = False
            calendar.updated = timezone.now()
            calendar.status = 'Finished syncing calendar'
            calendar.errors = 0
            calendar.save()
            logging.info('Finished sync of calendar "%s" for user "%s"' % (calendar, calendar.user))
            
        else:
            task_update_calendar_wait.apply_async(args=[calendar_id], countdown=60)
        
    except Calendar.DoesNotExist, e:
        pass

@task(default_retry_delay=30)
def task_update_website_wait(calendar_id):
    try:
        calendar = Calendar.objects.get(id=calendar_id)
        
        if not calendar.enabled:
            return
            
        if not calendar.websites.filter(running=True).count():
            task_update_calendar.apply_async(args=[calendar_id], countdown=3)
            
            logging.info('Deferred sync of calendar "%s" for user "%s"' % (calendar, calendar.user))
            
        else:
            task_update_website_wait.apply_async(args=[calendar_id], countdown=60)
        
    except Calendar.DoesNotExist, e:
        pass

@task(default_retry_delay=60, max_retries=15)
def task_parse_website(calendar_id, website_id):
    try:
        calendar = Calendar.objects.get(id=calendar_id)

        if not calendar.enabled:
            return

        website = Website.objects.get(calendar=calendar, id=website_id)
        
        if not website.enabled:
            return
            
        website.running = True
        website.status = 'Parsing website'
        website.save()
        
        logging.info('Parsing website "%s" for user "%s"' % (website, calendar.user))
        
        events_data = {}
        website_tz = pytz.timezone(website.timezone)
        website_file = urllib2.urlopen(urllib2.Request(website.href, headers={'User-agent': 'WebGCal'}))
        for calendar_data in hcalendar.hCalendar(website_file):
            for event_data in calendar_data:
                for attr in ('dtstart', 'dtend', 'dtstamp', 'last_modified'):
                    value = getattr(event_data, attr)
                    if value and not timezone.is_aware(value):
                        setattr(event_data, attr, timezone.make_aware(value, website_tz))
                if event_data.uid:
                    events_data[event_data.uid] = event_data
                elif event_data.summary and event_data.dtstart:
                    events_data[hash(event_data.summary)^hash(event_data.dtstart)] = event_data
        
        logging.info('Parsed website "%s" for user "%s"' % (website, calendar.user))
        
        events = {}
        for event in website.events:
            if event.uid:
                events[event.uid] = event
            else:
                events[hash(event.summary)^hash(event.dtstart)] = event
        
        logging.info('Updating events of website "%s" for user "%s"' % (website, calendar.user))
        
        for key, event_data in events_data.iteritems():
            if not key in events:
                kwargs = {'website': website, 'parsed': timezone.now()}
                for attr in ('uid', 'summary', 'description', 'location', 'category', 'status', 'dtstart', 'dtend', 'dtstamp', 'last_modified'):
                    value = getattr(event_data, attr, None)
                    if value:
                        kwargs[attr] = value
                Event.objects.create(**kwargs)
            else:
                save = False
                event = events[key]
                for attr in ('uid', 'summary', 'description', 'location', 'category', 'status', 'dtstart', 'dtend', 'dtstamp', 'last_modified'):
                    value = getattr(event_data, attr, None)
                    if value != getattr(event, attr, None):
                        setattr(event, attr, value)
                        save = True
                if event.deleted or save:
                    event.deleted = False
                    event.parsed = timezone.now()
                    event.save()
        
        logging.info('Deleting events of website "%s" for user "%s"' % (website, calendar.user))
        
        for key, event in events.iteritems():
            if not key in events_data:
                event.deleted = True
                event.save()
                
        website.running = False
        website.updated = timezone.now()
        website.status = 'Finished parsing website'
        website.save()
        logging.info('Parsed all events of website "%s" for user "%s"' % (website, calendar.user))
        
    except urllib2.URLError, e:
        website.enabled = False
        website.running = False
        website.status = 'Error: %s' % e.reason
        website.save()
        
    except Calendar.DoesNotExist, e:
        pass
        
    except Website.DoesNotExist, e:
        pass
        
    except Exception, e:
        if website.errors < 15:
            website.errors += 1
            website.save()
            task_parse_website.retry(exc=e)

        else:
            website.enabled = False
            website.running = False
            website.status = 'Error: Unable to parse website'
            website.errors = 0
            website.save()

def _parse_request_error(error):
    if not 'body' in error:
        return None

    soup = bs4.BeautifulSoup(error['body'])
    if not soup:
        return None

    title = soup.find('title')
    if not title:
        return None

    return title.string
