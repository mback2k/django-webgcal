# -*- coding: utf-8 -*-
from celery.task import task
from django.utils import timezone
from ....libs.keeperr.models import Error
from ..models import User, Website, Event
from .calendar import task_sync_calendar
import hcalendar
import logging
import urllib2
import pytz

@task(default_retry_delay=120, max_retries=5)
def task_parse_website(user_id, website_id):
    user = User.objects.get(id=user_id, is_active=True)
    website = Website.objects.get(calendar__user=user, id=website_id, enabled=True, running=False)
    website.running = True
    website.status = 'Parsing website'
    website.save()

    logging.info('Parsing website "%s" for user "%s"' % (website, user))

    try:
        events_data = {}
        website_tz = pytz.timezone(website.timezone)
        website_req = urllib2.Request(website.href, headers={'User-agent': 'WebGCal/0.1'})
        website_file = urllib2.urlopen(website_req)

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

        logging.info('Parsed website "%s" for user "%s"' % (website, user))

        events = {}
        for event in website.events.all():
            if event.uid:
                events[event.uid] = event
            else:
                events[hash(event.summary)^hash(event.dtstart)] = event

        logging.info('Updating events of website "%s" for user "%s"' % (website, user))

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

        logging.info('Deleting events of website "%s" for user "%s"' % (website, user))

        for key, event in events.iteritems():
            if not key in events_data:
                event.deleted = True
                event.save()

        website.running = False
        website.updated = timezone.now()
        website.status = 'Finished parsing website'
        website.save()

        logging.info('Parsed all events of website "%s" for user "%s"' % (website, user))

    except urllib2.URLError, e:
        raise task_parse_website.retry(exc=e)

    except Exception, e:
        logging.exception(e)
        Error.assign(website).save()
        website.enabled = False
        website.running = False
        website.status = 'Error: Unable to parse website'
        website.save()

    if not website.calendar.running and not website.calendar.websites.filter(running=True).count():
        task_sync_calendar.apply_async(args=[user.id, website.calendar.id], task_id='sync-calendar-%d-%d' % (user.id, website.calendar.id))

        logging.info('Deferred sync of calendar "%s" for user "%s"' % (website.calendar, user))
