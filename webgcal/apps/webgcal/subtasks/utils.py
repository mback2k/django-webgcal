# -*- coding: utf-8 -*-
from celery.result import BaseAsyncResult

def clean_task_result(task_id):
    task = BaseAsyncResult(task_id)
    if task and task.ready():
        task.forget()
