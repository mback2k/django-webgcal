# -*- coding: utf-8 -*-
from celery.schedules import crontab
from celery.task import periodic_task
from celery import group
from .models import User
from .subtasks.user import task_check_user

@periodic_task(run_every=crontab(minute=0))
def task_start_worker():
    user_id_list = User.objects.filter(is_active=True).values_list('id', flat=True).order_by('id')

    tasks = group(task_check_user.s(user_id) for user_id in user_id_list)
    tasks.apply_async()
