# -*- coding: utf-8 -*-
from apiclient.errors import HttpError
from celery.task import task
from ....libs.keeperr.models import Error
from ..models import User, Calendar
from .. import google
from .event import task_sync_website
import logging

@task(default_retry_delay=120, max_retries=5)
def task_sync_calendar(user_id, calendar_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    try:
        calendar = Calendar.objects.get(user=user, id=calendar_id)
    except Calendar.DoesNotExist:
        return

    if not calendar.enabled:
        return

    calendar.running = True
    calendar.status = 'Syncing calendar'
    calendar.save()

    logging.info('Starting sync of calendar "%s" for "%s"' % (calendar, user))

    try:
        social_auth = google.get_social_auth(user)
        if not social_auth:
            return

        credentials = google.get_credentials(social_auth)
        session = google.get_session(credentials)
        service = google.get_calendar_service(session)
        if not google.check_calendar_access(service):
            return

        if calendar.google_id:
            try:
                calendarItem = service.calendars().get(calendarId=calendar.google_id).execute()
            except HttpError:
                calendarItem = None
        else:
            calendarItem = None

        if not calendarItem:
            calendarBody = make_calendar_body(calendar)
            calendarItem = service.calendars().insert(body=calendarBody).execute()

            calendar.google_id = calendarItem['id']
            calendar.save()

            logging.info('Inserted calendar "%s" for user "%s"' % (calendar.name, user))

        if calendar.google_id:
            for website in calendar.websites.all():
                task_sync_website.apply_async(args=[user.id, calendar.id, website.id], task_id='sync-website-%d-%d-%d' % (user.id, calendar.id, website.id))

                logging.info('Deferred initial sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, user))

    except HttpError, e:
        logging.exception(e)
        Error.assign(calendar).save()
        calendar.enabled = e.resp.status == 403
        calendar.running = False
        calendar.status = u'HTTP: %s' % e.resp.reason
        calendar.save()

    except Exception, e:
        logging.exception(e)
        Error.assign(calendar).save()
        calendar.enabled = False
        calendar.running = False
        calendar.status = 'Error: Fatal error'
        calendar.save()


def make_calendar_body(calendar, calendarBody = {}):
    calendarBody['summary'] = calendar.name
    calendarBody['description'] = u'%s generated by WebGCal' % calendar.name
    calendarBody['timeZone'] = 'UTC'
    return calendarBody