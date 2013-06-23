# -*- coding: utf-8 -*-
from celery.schedules import crontab
from celery.task import periodic_task
from .models import User
from .subtasks.user import task_check_user

@periodic_task(run_every=crontab(minute=0))
def task_start_worker():
    for user in User.objects.filter(is_active=True):
        task_check_user.apply_async(args=[user.id], task_id='check-user-%d' % user.id)
