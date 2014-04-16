# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from djcelery_model.models import TaskMixin
import datetime

class Calendar(models.Model, TaskMixin):
    user = models.ForeignKey(User, related_name='calendars')
    name = models.CharField(_('Name'), max_length=100)
    google_id = models.CharField(_('Google ID'), max_length=200, blank=True, null=True)
    updated = models.DateTimeField(_('Date updated'), blank=True, null=True)
    enabled = models.BooleanField(_('Enabled'), default=True)
    status = models.TextField(_('Status'), blank=True, null=True)
    
    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return self.name

    @property
    def running(self):
        self.clear_task_results()
        return self.has_running_task

class Website(models.Model, TaskMixin):
    calendar = models.ForeignKey(Calendar, related_name='websites')
    name = models.CharField(_('Name'), max_length=100)
    href = models.URLField(_('Link'))
    timezone = models.CharField(_('Timezone'), max_length=50, default='UTC')
    updated = models.DateTimeField(_('Date updated'), blank=True, null=True)
    enabled = models.BooleanField(_('Enabled'), default=True)
    status = models.TextField(_('Status'), blank=True, null=True)
    
    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return self.name

    @property
    def running(self):
        self.clear_task_results()
        return self.has_running_task

class Event(models.Model):
    website = models.ForeignKey(Website, related_name='events')
    google_id = models.CharField(_('Google ID'), max_length=200, blank=True, null=True)
    parsed = models.DateTimeField(_('Date parsed'), default=datetime.date.min)
    synced = models.DateTimeField(_('Date synced'), default=datetime.date.min)
    deleted = models.BooleanField(_('Deleted'), default=False)

    uid = models.TextField(_('UID'), blank=True, null=True)
    summary = models.TextField(_('Summary'))
    description = models.TextField(_('Description'), blank=True, null=True)
    location = models.TextField(_('Location'), blank=True, null=True)
    category = models.TextField(_('Category'), blank=True, null=True)
    status = models.TextField(_('Status'), blank=True, null=True)
    dtstart = models.DateTimeField(_('DTStart'))
    dtend = models.DateTimeField(_('DTEnd'), blank=True, null=True)
    dtstamp = models.DateTimeField(_('DTStamp'), blank=True, null=True)
    last_modified = models.DateTimeField(_('Last modified'), blank=True, null=True)

    def __unicode__(self):
        return self.summary
