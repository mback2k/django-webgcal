# -*- coding: utf-8 -*-
from apiclient.errors import HttpError
from celery.task import task
from django.db import transaction
from ....libs.keeperr.models import Error
from ..models import User, Website
from .. import google
from .website import task_parse_website
import logging

@task()
def task_check_user(user_id):
    user = User.objects.get(id=user_id, is_active=True)

    try:
        check_user(user)

    except HttpError, e:
        logging.exception(e)
        Error.assign(user).save()
        return

    for website in Website.objects.filter(calendar__user=user):
        website.task_id = 'parse-website-%d-%d' % (user.id, website.id)
        website.save()

        task_parse_website.apply_async(args=[user.id, website.id], task_id=website.task_id)

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
