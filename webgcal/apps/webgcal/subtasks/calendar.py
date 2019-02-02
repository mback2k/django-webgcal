# -*- coding: utf-8 -*-
from googleapiclient.errors import HttpError
from celery.task import task
from django.db import transaction
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from ..models import User, Calendar
from ..google import require_calendar_access
from .event import task_sync_website
import logging

logging = logging.getLogger('celery.task')

@task(ignore_result=True, default_retry_delay=120, max_retries=5)
def task_sync_calendar(user_id, calendar_id):
    user = User.objects.get(id=user_id, is_active=True)
    calendar = Calendar.objects.get(user=user, id=calendar_id, enabled=True)
    calendar.status = 'Syncing calendar'
    calendar.save()

    try:
        sync_calendar(user, calendar)

    except HttpError as e:
        logging.exception(e)
        calendar.enabled = e.resp.status in (403, 503)
        calendar.status = 'HTTP: %s' % e.resp.reason
        calendar.save()
        mail_user_calendar(user, calendar, calendar.status)

    except Exception as e:
        logging.exception(e)
        calendar.enabled = False
        calendar.status = 'Error: Fatal error'
        calendar.save()
        mail_user_calendar(user, calendar, calendar.status)

    if calendar.enabled and calendar.has_running_task and calendar.google_id:
        if not calendar.websites.with_running_tasks().exists():
            sync_calendar_websites(user, calendar)

@transaction.atomic
@require_calendar_access
def sync_calendar(user, social_auth, service, calendar):
    logging.info('Starting sync of calendar "%s" for "%s"' % (calendar, user))

    try:
        if calendar.google_id:
            calendarItem = service.calendars().get(calendarId=calendar.google_id).execute()
        else:
            calendarItem = None
    except HttpError as e:
        if e.resp.status == 404:
            calendarItem = None
        else:
            raise e

    if not calendarItem:
        calendarBody = make_calendar_body(calendar)
        calendarItem = service.calendars().insert(body=calendarBody).execute()

        calendar.google_id = calendarItem['id']
        calendar.save()

        logging.info('Inserted calendar "%s" for user "%s"' % (calendar.name, user))

@require_calendar_access
def sync_calendar_websites(user, social_auth, service, calendar):
    for website in calendar.websites.all():
        args = (user.id, calendar.id, website.id)
        task_id = 'sync-website-%d-%d-%d' % args
        website.apply_async(task_sync_website, args=args, task_id=task_id, countdown=5)

        logging.info('Deferred initial sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, user))

def make_calendar_body(calendar, calendarBody = {}):
    calendarBody['summary'] = calendar.name
    calendarBody['description'] = u'%s generated by WebGCal' % calendar.name
    calendarBody['timeZone'] = 'UTC'
    return calendarBody

def mail_user_calendar(user, calendar, message):
    current_site = Site.objects.get_current()
    kwargs = {'calendar_id': calendar.id}
    edit_calendar = 'https://%s%s' % (current_site.domain, reverse('webgcal:edit_calendar', kwargs=kwargs))

    user.email_user('WebGCal - Sync failure for %s - Action required!' % user,
                    'WebGCal tried to sync your calendar "%s", but failed to do so, because of the following error:\n\n' \
                    '%s\n\n' \
                    'Please go to %s and check your calendar!' % (calendar, message, edit_calendar))
