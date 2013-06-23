# -*- coding: utf-8 -*-
from apiclient.errors import HttpError
from celery.task import task
from ....libs.keeperr.models import Error
from ..models import User, Website
from .. import google
from .website import task_parse_website
import logging

@task()
def task_check_user(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    try:
        social_auth = google.get_social_auth(user)
        if not social_auth:
            return

        credentials = google.get_credentials(social_auth)
        session = google.get_session(credentials)
        service = google.get_calendar_service(session)
        if not google.check_calendar_access(service):
            return
    except HttpError, e:
        logging.exception(e)
        Error.assign(user).save()
        return

    for website in Website.objects.filter(calendar__user=user):
        task_parse_website.apply_async(args=[user.id, website.id], task_id='parse-website-%d-%d' % (user.id, website.id))
