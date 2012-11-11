import bs4
import pytz
import urllib2
import logging
import datetime
import hcalendar
from apiclient.http import BatchHttpRequest
from celery.schedules import crontab
from celery.task import task, periodic_task
from django.utils import timezone
from django.db.models import Q, F
from webgcal.models import Calendar, Website, Event
from webgcal import google

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

        social_auth = google.get_social_auth(calendar.user)
        if not social_auth:
            return

        credentials = google.get_credentials(social_auth)
        session = google.get_session(credentials)
        service = google.get_calendar_service(session)
        if not google.check_calendar_access(service):
            return

        if calendar.google_id:
            calendarItem = service.calendars().get(calendarId=calendar.google_id).execute()
        else:
            calendarItem = None

        if not calendarItem:
            calendarBody = {
                'summary': calendar.name,
                'description': u'%s generated by WebGCal' % calendar.name,
                'timeZone': 'UTC',
            }
            calendarItem = service.calendars().insert(body=calendarBody).execute()

            calendar.google_id = calendarItem['id']
            calendar.save()

            logging.info('Inserted calendar "%s" for user "%s"' % (calendar.name, calendar.user))

        if calendar.google_id:
            for website in calendar.websites.all():
                task_update_calendar_sync.apply_async(args=[calendar_id, website.id], countdown=3)

                logging.info('Deferred initial sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, calendar.user))

        task_update_calendar_wait.apply_async(args=[calendar_id], countdown=60)

        logging.info('Deferred sync of calendar "%s" for user %s"' % (calendar, calendar.user))

    except Calendar.DoesNotExist, e:
        pass

    except Exception, e:
        logging.exception(e)
        calendar.enabled = False
        calendar.running = False
        calendar.status = 'Error: Fatal error'
        calendar.errors = 0
        calendar.save()


@task(default_retry_delay=60, max_retries=15)
def task_update_calendar_sync(calendar_id, website_id, cursor=None, limit=500):
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

        social_auth = google.get_social_auth(calendar.user)
        if not social_auth:
            return

        credentials = google.get_credentials(social_auth)
        session = google.get_session(credentials)
        service = google.get_calendar_service(session)
        if not google.check_calendar_access(service):
            return

        sync_datetime = timezone.now()
        sync_timeout = sync_datetime - datetime.timedelta(days=1)

        events = website.events.filter(Q(google_id=None) | Q(deleted=True) | Q(synced__lt=F('parsed')) | Q(synced__lt=sync_timeout))
        if cursor:
            events = events.filter(id__gte=cursor)


        entries = {}

        def query_event(request_id, response, exception):
            if exception:
                return logging.exception(exception)

            request_id = long(request_id, 16)
            if not response:
                event = Event.objects.get(id=request_id)
                if event.deleted:
                    event.delete()
                else:
                    event.google_id = None
                    event.save()
            elif 'error' in response and response['error']['code'] == 404:
                event = Event.objects.get(id=request_id)
                event.google_id = None
                event.save()
            elif 'kind' in response and response['kind'] == 'calendar#event':
                entries[request_id] = response
            else:
                logging.debug('query %s: %s' % (request_id, response))

        batch = BatchHttpRequest(callback=query_event)

        for event in events[:limit]:
            if event.google_id:
                batch.add(service.events().get(calendarId=calendar.google_id, eventId=event.google_id), request_id=hex(event.id))

        logging.info('Executing batch request')
        batch.execute(http=session)
        logging.info('Executed batch request')


        def update_event(request_id, response, exception):
            if exception:
                return logging.exception(exception)

            request_id = long(request_id, 16)
            if not response:
                event = Event.objects.get(id=request_id)
                if event.deleted:
                    event.delete()
                else:
                    event.google_id = None
                    event.save()
            elif 'error' in response and response['error']['code'] == 404:
                event = Event.objects.get(id=request_id)
                event.google_id = None
                event.save()
            elif 'kind' in response and response['kind'] == 'calendar#event':
                event = Event.objects.get(id=request_id)
                event.google_id = response['id']
                event.synced = sync_datetime
                event.save()
            else:
                logging.debug('update %s: %s' % (request_id, response))

        batch = BatchHttpRequest(callback=update_event)

        for event in events[:limit]:
            if not event.google_id:
                if not event.deleted and website.enabled:
                    eventBody = make_event_body(calendar, website, event)

                    batch.add(service.events().insert(calendarId=calendar.google_id, body=eventBody), request_id=hex(event.id))

                else:
                    event.delete()

            elif event.id in entries and (event.deleted or event.synced < event.parsed):
                eventBody = entries[event.id]
                if not event.deleted and website.enabled:
                    eventBody = make_event_body(calendar, website, event, eventBody)

                    batch.add(service.events().update(calendarId=calendar.google_id, eventId=event.google_id, body=eventBody), request_id=hex(event.id))

                else:
                    batch.add(service.events().delete(calendarId=calendar.google_id, eventId=event.google_id), request_id=hex(event.id))

            elif event.synced < sync_timeout:
                event.synced = sync_datetime
                event.save()

        logging.info('Executing batch request')
        batch.execute(http=session)
        logging.info('Executed batch request')


        if events.count() > limit:
            task_update_calendar_sync.apply_async(args=[calendar_id, website_id, events[limit].id, limit], countdown=2)

            logging.info('Deferred additional sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, calendar.user))

        else:
            website.running = False
            website.status = 'Finished syncing website'
            website.errors = 0
            website.save()
            logging.info('Finished sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, calendar.user))

    except Calendar.DoesNotExist, e:
        pass

    except Website.DoesNotExist, e:
        pass

    except Exception, e:
        logging.exception(e)
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
        website_file = urllib2.urlopen(urllib2.Request(website.href, headers={'User-agent': 'WebGCal/0.1'}))
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
        for event in website.events.all():
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
        logging.exception(e)
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


def make_event_body(calendar, website, event, eventBody = {}):
    if calendar.websites.count() > 1:
        eventBody['summary'] = u'%s: %s' % (website.name, event.summary)
    else:
        eventBody['summary'] = event.summary
    if event.dtstart.hour == 0 and event.dtstart.minute == 0 and event.dtstart.second == 0 and not event.dtend:
        eventBody['start'] = {'date': event.dtstart.strftime('%Y-%m-%d')}
        eventBody['end'] = {'date': (event.dtstart + datetime.timedelta(days=1)).strftime('%Y-%m-%d')}
    elif event.dtstart.hour == 0 and event.dtstart.minute == 0 and event.dtstart.second == 0 and event.dtend.hour == 0  and event.dtend.minute == 0 and event.dtend.second == 0:
        eventBody['start'] = {'date': event.dtstart.strftime('%Y-%m-%d')}
        eventBody['end'] = {'date': (event.dtend + datetime.timedelta(days=1)).strftime('%Y-%m-%d')}
    elif event.dtend:
        eventBody['start'] = {'dateTime': event.dtstart.isoformat()}
        eventBody['end'] = {'dateTime': event.dtend.isoformat()}
    else:
        eventBody['start'] = {'dateTime': event.dtstart.isoformat()}
    if event.location:
        eventBody['location'] = event.location
    if event.status:
        eventBody['status'] = event.status
    else:
        eventBody['status'] = 'confirmed'
    if event.description:
        eventBody['description'] = event.description
    eventBody['transparency'] = 'transparent'
    eventBody['iCalUID'] = 'webgcal-%d' % event.id
    return eventBody
