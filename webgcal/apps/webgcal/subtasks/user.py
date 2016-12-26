# -*- coding: utf-8 -*-
from apiclient.errors import HttpError
from celery.task import task
from django.db import transaction
from ....libs.keeperr.models import Error
from ..models import User, Website
from .. import google
from .website import task_parse_website
import logging

@task(ignore_result=True)
def task_check_user(user_id):
    user = User.objects.get(id=user_id, is_active=True)

    try:
        check_user(user)

    except HttpError as e:
        logging.exception(e)
        Error.assign(user).save()
        return

    for website in Website.objects.filter(calendar__user=user, enabled=True):
        args = (user.id, website.id)
        task_id = 'parse-website-%d-%d' % args
        website.apply_async(task_parse_website, args=args, task_id=task_id, countdown=5)

        logging.info('Deferred parsing of website "%s" for user "%s"' % (website, user))

@transaction.atomic
def check_user(user):
    social_auth = google.get_social_auth(user)
    if not social_auth:
        raise RuntimeWarning('No social auth available for user "%s"' % user)

    credentials = google.get_credentials(social_auth)
    session = google.get_session(credentials)
    service = google.get_calendar_service(session)
    if not google.check_calendar_access(service):
        raise RuntimeWarning('No calendar access available for user "%s"' % user)
