# -*- coding: utf-8 -*-
from celery.task import task
from django.utils import timezone
from django.db import transaction
from ..models import User, Website, Event
from .calendar import task_sync_calendar
import hcalendar
import logging
import urllib
import pytz

logging = logging.getLogger('celery.task')

@task(bind=True, ignore_result=True, retry_backoff=60, retry_jitter=True, max_retries=5)
def task_parse_website(self, user_id, website_id):
    user = User.objects.get(id=user_id, is_active=True)
    website = Website.objects.get(calendar__user=user, id=website_id, enabled=True)
    website.status = 'Parsing website'
    website.save()

    try:
        try:
            parse_website(user, website)

        except urllib.request.URLError as e:
            raise self.retry(exc=e)

    except Exception as e:
        logging.exception(e)
        website.enabled = False
        website.status = 'Error: Unable to parse website'
        website.save()

    if website.calendar.enabled and not website.calendar.has_running_task and not website.calendar.websites.exclude(id=website.id).with_running_tasks().exists():
        args = (user.id, website.calendar.id)
        task_id = 'sync-calendar-%d-%d' % args
        website.calendar.apply_async(task_sync_calendar, args=args, task_id=task_id, countdown=10)

        logging.info('Deferred sync of calendar "%s" for user "%s"' % (website.calendar, user))

@transaction.atomic
def parse_website(user, website):
    logging.info('Parsing website "%s" for user "%s"' % (website, user))

    website_tz = pytz.timezone(website.timezone)
    website_req = urllib.request.Request(website.href, headers={'User-agent': 'WebGCal/0.1'})
    website_file = urllib.request.urlopen(website_req)

    events_data = {}
    for calendar_data in hcalendar.hCalendar(website_file):
        for event_data in calendar_data:
            for attr in ('dtstart', 'dtend', 'dtstamp', 'last_modified'):
                value = getattr(event_data, attr)
                if value and not timezone.is_aware(value):
                    setattr(event_data, attr, timezone.make_aware(value, website_tz))
            if event_data.summary and event_data.dtstart:
                if event_data.uid:
                    events_data[event_data.uid] = event_data
                else:
                    events_data[hash(event_data.summary)^hash(event_data.dtstart)] = event_data

    logging.info('Parsed website "%s" for user "%s"' % (website, user))

    events = {}
    for event in website.events.all():
        if event.uid:
            events[event.uid] = event
        else:
            events[hash(event.summary)^hash(event.dtstart)] = event

    logging.info('Updating events of website "%s" for user "%s"' % (website, user))

    for key, event_data in events_data.items():
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

    for key, event in events.items():
        if not key in events_data:
            event.deleted = True
            event.save()

    website.updated = timezone.now()
    website.status = 'Finished parsing website'
    website.save()

    logging.info('Parsed all events of website "%s" for user "%s"' % (website, user))
