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
    updated = models.DateTimeField(_('date updated'), blank=True, null=True)
    enabled = models.BooleanField(_('enabled'), default=True)
    running = models.BooleanField(_('running'), default=False)
    status = models.TextField(_('status'), blank=True, null=True)
    errors = models.IntegerField(_('errors'), default=0)
    
    def __unicode__(self):
        return self.name
        
    @cache_property
    def events(self):
        return self.event_set.order_by('dtstart')

class Event(models.Model):
    website = models.ForeignKey(Website)
    href = models.URLField(_('link'), verify_exists=False)
    parse = models.IntegerField(_('parse reference'), default=0)
    parsed = models.DateTimeField(_('date parsed'), default=datetime.date.min)
    synced = models.DateTimeField(_('date synced'), default=datetime.date.min)
    deleted = models.BooleanField(_('deleted'), default=False)
    
    summary = models.CharField(_('summary'), max_length=250)
    dtstart = models.DateTimeField(_('dtstart'))

    def __unicode__(self):
        return self.summary
