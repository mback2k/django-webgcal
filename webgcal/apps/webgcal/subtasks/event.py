# -*- coding: utf-8 -*-
from apiclient.http import BatchHttpRequest
from apiclient.errors import HttpError
from celery.task import task
from django.db.models import Q, F
from django.utils import timezone
from ....libs.keeperr.models import Error
from ..models import User, Calendar, Website, Event
from .. import google
import datetime
import logging

@task(default_retry_delay=120, max_retries=5)
def task_sync_website(user_id, calendar_id, website_id, cursor=None, limit=500):
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

    try:
        website = Website.objects.get(calendar__user=user, calendar=calendar, id=website_id)
    except Website.DoesNotExist:
        return

    website.running = True
    website.status = 'Syncing website (%d/%d)' % (website.events.filter(id__lt=cursor).count() if cursor else 0, website.events.count())
    website.save()

    logging.info('Syncing %d events after cursor "%s" of calendar "%s" and website "%s" for "%s"' % (limit, cursor, calendar, website, user))

    try:
        social_auth = google.get_social_auth(user)
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
            event_id = long(request_id, 16)
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

                Error.assign(event).save()

            elif response and 'kind' in response and response['kind'] == 'calendar#event':
                entries[event_id] = response

        if events.exclude(google_id=None).exists():
            batch = BatchHttpRequest(callback=query_event)

            for event in events.exclude(google_id=None)[:limit]:
                batch.add(service.events().get(calendarId=calendar.google_id, eventId=event.google_id), request_id=hex(event.id))

            logging.info('Executing batch query request')
            batch.execute(http=session)
            logging.info('Executed batch query request')


        def verify_event(request_id, response, exception):
            event_id = long(request_id, 16)
            event = Event.objects.get(id=event_id)

            if exception:
                Error.assign(event).save()

            elif response and 'kind' in response and response['kind'] == 'calendar#events':
                if 'items' in response and len(response['items']) == 1:
                    event.google_id = response['items'][0]['id']
                    event.save()
                elif event.deleted:
                    event.delete()

        if events.filter(google_id=None).exists():
            batch = BatchHttpRequest(callback=verify_event)

            for event in events.filter(google_id=None)[:limit]:
                batch.add(service.events().list(calendarId=calendar.google_id, iCalUID='webgcal-%d' % event.id), request_id=hex(event.id))

            logging.info('Executing batch verify request')
            batch.execute(http=session)
            logging.info('Executed batch verify request')


        def update_event(request_id, response, exception):
            event_id = long(request_id, 16)
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

                Error.assign(event).save()

            elif response and 'kind' in response and response['kind'] == 'calendar#event':
                event.google_id = response['id']
                event.synced = sync_datetime
                event.save()


        if events.exists():
            batch = BatchHttpRequest(callback=update_event)
            operations = 0

            for event in events[:limit]:
                if not event.google_id:
                    if not event.deleted and website.enabled:
                        eventBody = make_event_body(calendar, website, event)

                        batch.add(service.events().insert(calendarId=calendar.google_id, body=eventBody), request_id=hex(event.id))
                        operations += 1

                    else:
                        event.delete()

                elif event.id in entries and (event.deleted or event.synced < event.parsed):
                    eventBody = entries[event.id]
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
                batch.execute(http=session)
                logging.info('Executed batch update request')


        if events.count() > limit:
            task_sync_website.apply_async(args=[user.id, calendar.id, website.id, events[limit].id, limit], task_id='sync-website-%d-%d-%d-%d-%d' % (user.id, calendar.id, website.id, events[limit].id), countdown=10)

            logging.info('Deferred additional sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, user))

        else:
            website.running = False
            website.status = 'Finished syncing website'
            website.save()

            logging.info('Finished sync of calendar "%s" and website "%s" for user "%s"' % (calendar, website, user))

    except HttpError, e:
        logging.exception(e)
        Error.assign(website).save()
        website.enabled = e.resp.status in (403, 503)
        website.running = False
        website.status = u'HTTP: %s' % e.resp.reason
        website.save()

    except Exception, e:
        logging.exception(e)
        Error.assign(website).save()
        website.enabled = False
        website.running = False
        website.status = 'Error: Fatal error'
        website.save()

    if not calendar.websites.filter(running=True).count():
        calendar.running = False
        calendar.updated = timezone.now()
        calendar.status = 'Finished syncing calendar'
        calendar.save()

        logging.info('Finished sync of calendar "%s" for user "%s"' % (calendar, user))


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
