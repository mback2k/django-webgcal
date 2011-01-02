from google.appengine.ext.deferred import Error, PermanentTaskFailure, defer as _defer
from django.db import models

class DeferredTask(models.Model):
    name = models.CharField(max_length=500)
    reference_id = models.IntegerField()

def run_task(*args, **kwargs):
    task_id = kwargs.pop('_task_id')
    task_obj = kwargs.pop('_task_obj')
    try:
        task_obj(*args, **kwargs)
    except PermanentTaskFailure, e:
        DeferredTask.objects.filter(id=task_id).delete()
        raise e
    else:
        DeferredTask.objects.filter(id=task_id).delete()

def defer(name, reference_id, task_obj, *args, **kwargs):
    task = DeferredTask.objects.create(name=name, reference_id=reference_id)
    task_id = task.id
    kwargs['_task_id'] = task_id
    kwargs['_task_obj'] = task_obj
    if not '_name' in kwargs:
        kwargs['_name'] = 'DeferredTask%d' % task_id
    _defer(run_task, *args, **kwargs)

def deferred(**kwargs):
    if 'name' in kwargs or 'reference_id' in kwargs:
        return DeferredTask.objects.filter(**kwargs).count()
