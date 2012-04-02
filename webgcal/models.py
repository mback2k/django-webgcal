# -*- coding: utf-8 -*-
import datetime
from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User
from webgcal.decorators import cache_property
from django.utils.translation import ugettext_lazy as _

class Calendar(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(_('name'), max_length=100)
    href = models.URLField(_('link'), verify_exists=False)
    feed = models.URLField(_('link'), verify_exists=False)
    updated = models.DateTimeField(_('date updated'), blank=True, null=True)
    enabled = models.BooleanField(_('enabled'), default=True)
    running = models.BooleanField(_('running'), default=False)
    status = models.TextField(_('status'), blank=True, null=True)
    errors = models.IntegerField(_('errors'), default=0)
    
    def __unicode__(self):
        return self.name
        
    @cache_property
    def websites(self):
        return self.website_set.order_by('name')
        
class Website(models.Model):
    calendar = models.ForeignKey(Calendar)
    name = models.CharField(_('name'), max_length=100)
    href = models.URLField(_('link'), verify_exists=False)
    timezone = models.CharField(_('timezone'), max_length=50, default='UTC')
    updated = models.DateTimeField(_('date updated'), blank=True, null=True)
    enabled = models.BooleanField(_('enabled'), default=True)
    running = models.BooleanField(_('running'), default=False)
    status = models.TextField(_('status'), blank=True, null=True)
    errors = models.IntegerField(_('errors'), default=0)
    
    def __unicode__(self):
        return self.name
        
    @cache_property
    def events(self):
        return self.event_set.order_by('id')

class Event(models.Model):
    website = models.ForeignKey(Website)
    href = models.URLField(_('link'), verify_exists=False)
    parsed = models.DateTimeField(_('date parsed'), default=datetime.date.min)
    synced = models.DateTimeField(_('date synced'), default=datetime.date.min)
    deleted = models.BooleanField(_('deleted'), default=False)

    uid = models.TextField(_('uid'), blank=True, null=True)
    summary = models.TextField(_('summary'))
    description = models.TextField(_('description'), blank=True, null=True)
    location = models.TextField(_('location'), blank=True, null=True)
    category = models.TextField(_('category'), blank=True, null=True)
    status = models.TextField(_('status'), blank=True, null=True)
    dtstart = models.DateTimeField(_('dtstart'))
    dtend = models.DateTimeField(_('dtend'), blank=True, null=True)
    dtstamp = models.DateTimeField(_('dtstamp'), blank=True, null=True)

    def __unicode__(self):
        return self.summary
