# -*- coding: utf-8 -*-
from googleapiclient.errors import HttpError
from celery.task import task
from django.db.models import Q, F
from django.utils import timezone
from django.db import transaction
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.core.cache import cache
from ..models import User, Calendar, Website, Event
from ..google import require_calendar_access
import datetime
import logging

logging = logging.getLogger('celery.task')

@task(ignore_result=True, default_retry_delay=120, max_retries=5)
def task_sync_website(user_id, calendar_id, website_id, cursor=None, limit=500):
    user = User.objects.get(id=user_id, is_active=True)
    calendar = Calendar.objects.get(user=user, id=calendar_id, enabled=True)
    website = Website.objects.get(calendar__user=user, calendar=calendar, id=website_id)
    website.status = 'Syncing website (%d/%d)' % (website.events.filter(id__lt=cursor).count() if cursor else 0, website.events.count())
    website.save()

    try:
        sync_website(user, calendar, website, cursor, limit)

    except HttpError as e:
        logging.exception(e)
        website.enabled = website.enabled and e.resp.status in (403, 503)
        website.status = 'HTTP: %s' % e.resp.reason
        website.save()
        mail_user_website(user, website, website.status)

    except Exception as e:
        logging.exception(e)
        website.enabled = False
        website.status = 'Error: Fatal error'
        website.save()
        mail_user_website(user, website, website.status)

    if not calendar.websites.exclude(id=website.id).with_running_tasks().exists():
        calendar.updated = timezone.now()
        calendar.status = 'Finished syncing calendar'
        calendar.save()

        logging.info('Finished sync of calendar "%s" for user "%s"' % (calendar, user))

@require_calendar_access
def sync_website(user, social_auth, service, session, calendar, website, cursor=None, limit=500):
    logging.info('Syncing %d events after cursor "%s" of calendar "%s" and website "%s" for "%s"' % (limit, cursor, calendar, website, user))

    sync_datetime = timezone.now()
    sync_timeout = sync_datetime - datetime.timedelta(days=1)

    events = website.events.filter(Q(google_id=None) | Q(deleted=True) | Q(synced__lt=F('parsed')) | Q(synced__lt=sync_timeout))
    if cursor:
        events = events.filter(id__gte=cursor)


    if events.exclude(google_id=None).exists():
        batch = service.new_batch_http_request(callback=query_event)
        operations = 0

        for event in events.exclude(google_id=None)[:limit]:
            batch.add(service.events().get(calendarId=calendar.google_id, eventId=event.google_id), request_id=hex(event.id))
            operations += 1

        if operations:
            logging.info('Executing batch query request')
            with transaction.atomic():
                batch.execute(http=session)
            logging.info('Executed batch query request')


    if events.filter(google_id=None).exists():
        batch = service.new_batch_http_request(callback=verify_event)
        operations = 0

        for event in events.filter(google_id=None)[:limit]:
            batch.add(service.events().list(calendarId=calendar.google_id, iCalUID='webgcal-%d' % event.id), request_id=hex(event.id))
            operations += 1

        if operations:
            logging.info('Executing batch verify request')
            with transaction.atomic():
                batch.execute(http=session)
            logging.info('Executed batch verify request')


    if events.exists():
        batch = service.new_batch_http_request(callback=update_event)
        operations = 0

        with transaction.atomic():
            for event in events[:limit]:
                eventBody = cache.get('event-%d' % event.id)
                if not event.google_id:
                    if not event.deleted and website.enabled:
                        eventBody = make_event_body(calendar, website, event)

                        batch.add(service.events().insert(calendarId=calendar.google_id, body=eventBody), request_id=hex(event.id))
                        operations += 1

                    else:
                        event.delete()

                elif eventBody and (event.deleted or event.synced < event.parsed):
                    if not event.deleted and website.enabled:
                        eventBody = make_event_body(calendar, website, event, eventBody)

                        batch.add(service.events().update(calendarId=calendar.google_id, eventId=event.google_id, body=eventBody), request_id=hex(event.id))
                        operations += 1

                    else:
                        batch.add(service.events().delete(calendarId=calendar.google_id, eventId=event.google_id), request_id=hex(event.id))
                        operations += 1

                elif event.synced < sync_timeout:
                    event.synced = sync_datetime
                    event.save()

        if operations:
            logging.info('Executing batch update request')
            with transaction.atomic():
                batch.execute(http=session)
            logging.info('Executed batch update request')


    if events.count() > limit:
        args = (user.id, calendar.id, website.id, events[limit].id, limit)
        task_id = 'sync-website-%d-%d-%d-%d-%d' % args
        website.apply_async(task_sync_website, args=args, task_id=task_id, countdown=10)

        logging.info('Deferred additional sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, user))

    else:
        website.status = 'Finished syncing website'
        website.save()

        logging.info('Finished sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, user))

@transaction.atomic
def query_event(request_id, response, exception):
    event_id = int(request_id, 16)
    event = Event.objects.get(id=event_id)

    if exception:
        if isinstance(exception, HttpError):
            if exception.resp.status == 404: # notFound
                if event.deleted:
                    return event.delete()
                else:
                    event.google_id = None
                    return event.save()
            elif exception.resp.status == 410: # deleted
                return event.delete()
            else:
                logging.exception(exception)
        else:
            logging.exception(exception)

    elif response and 'kind' in response and response['kind'] == 'calendar#event':
        cache.set('event-%d' % event.id, response, None)

@transaction.atomic
def verify_event(request_id, response, exception):
    event_id = int(request_id, 16)
    event = Event.objects.get(id=event_id)

    if exception:
        logging.exception(exception)

    elif response and 'kind' in response and response['kind'] == 'calendar#events':
        if 'items' in response and len(response['items']) == 1:
            event.google_id = response['items'][0]['id']
            event.save()
        elif event.deleted:
            event.delete()

@transaction.atomic
def update_event(request_id, response, exception):
    event_id = int(request_id, 16)
    event = Event.objects.get(id=event_id)

    if exception:
        if isinstance(exception, HttpError):
            if exception.resp.status == 404: # notFound
                if event.deleted:
                    return event.delete()
                else:
                    event.google_id = None
                    return event.save()
            elif exception.resp.status == 409: # duplicate
                event.deleted = True
                return event.save()
            elif exception.resp.status == 410: # deleted
                return event.delete()
            else:
                logging.exception(exception)
        else:
            logging.exception(exception)

    elif response and 'kind' in response and response['kind'] == 'calendar#event':
        event.google_id = response['id']
        event.synced = timezone.now()
        event.save()

def make_event_body(calendar, website, event, eventBody = {}):
    if calendar.websites.count() > 1:
        eventBody['summary'] = '%s: %s' % (website.name, event.summary)
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
        eventBody['status'] = event.status.lower()
    else:
        eventBody['status'] = 'confirmed'
    if event.description:
        eventBody['description'] = event.description
    eventBody['transparency'] = 'transparent'
    eventBody['iCalUID'] = 'webgcal-%d' % event.id
    return eventBody

def mail_user_website(user, website, message):
    current_site = Site.objects.get_current()
    kwargs = {'calendar_id': website.calendar.id, 'website_id': website.id}
    edit_website = 'https://%s%s' % (current_site.domain, reverse('webgcal:edit_website', kwargs=kwargs))

    user.email_user('WebGCal - Sync failure for %s - Action required!' % user,
                    'WebGCal tried to sync your website "%s", but failed to do so, because of the following error:\n\n' \
                    '%s\n\n' \
                    'Please go to %s and check your website!' % (website, message, edit_website))
