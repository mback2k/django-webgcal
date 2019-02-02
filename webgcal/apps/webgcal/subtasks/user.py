# -*- coding: utf-8 -*-
from googleapiclient.errors import HttpError
from celery.task import task
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from ..models import User, Website
from ..google import require_calendar_access
from .website import task_parse_website
import logging

logging = logging.getLogger('celery.task')

@task(ignore_result=True)
def task_check_user(user_id):
    user = User.objects.get(id=user_id, is_active=True)

    if not user.calendars.filter(enabled=True).exists():
        logging.info('User "%s" has not enabled calendars, skipping.' % user)
        return

    try:
        parse_websites(user)

    except HttpError as e:
        logging.exception(e)

    except RuntimeWarning as e:
        logging.warning(e)
        for calendar in user.calendars.filter(enabled=True):
            calendar.enabled = False
            calendar.status = 'Warning: No Google access'
            calendar.save()
        mail_user(user, e)

@require_calendar_access
def parse_websites(user, social_auth, service):
    for website in Website.objects.filter(calendar__user=user, calendar__enabled=True, enabled=True).without_running_tasks():
        args = (user.id, website.id)
        task_id = 'parse-website-%d-%d' % args
        website.apply_async(task_parse_website, args=args, task_id=task_id, countdown=5)

        logging.info('Deferred parsing of website "%s" for user "%s"' % (website, user))

def mail_user(user, message):
    current_site = Site.objects.get_current()
    show_dashboard = 'https://%s%s' % (current_site.domain, reverse('webgcal:show_dashboard'))

    user.email_user('WebGCal - Account failure for %s - Action required!' % user,
                    'WebGCal tried to update your calendars, but failed to do so, because of the following error:\n\n' \
                    '%s\n\n' \
                    'Please go to %s and refresh your Google access!' % (message, show_dashboard))
