# -*- coding: utf-8 -*-
from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User
from webgcal.decorators import cache_property
from django.utils.translation import ugettext_lazy as _

class Calendar(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(_('name'), max_length=100)
    href = models.TextField(_('href'))
    crdate = models.DateTimeField(_('date created'), auto_now_add=True)
    tstamp = models.DateTimeField(_('date edited'), auto_now=True)
    update = models.DateTimeField(_('date updated'), blank=True, null=True)
    enabled = models.BooleanField(_('enabled'), default=True)
    
    def __unicode__(self):
        return self.name
        
    @cache_property
    def websites(self):
        return self.website_set.order_by('name')
        
class Website(models.Model):
    calendar = models.ForeignKey(Calendar)
    name = models.CharField(_('name'), max_length=100)
    href = models.TextField(_('href'))
    crdate = models.DateTimeField(_('date created'), auto_now_add=True)
    tstamp = models.DateTimeField(_('date edited'), auto_now=True)
    update = models.DateTimeField(_('date updated'), blank=True, null=True)
    enabled = models.BooleanField(_('enabled'), default=True)
    
    def __unicode__(self):
        return self.name

class Event(models.Model):
    website = models.ForeignKey(Website)
    summary = models.CharField(_('summary'), max_length=100)
    dtstart = models.DateTimeField(_('dtstart'))
    crdate = models.DateTimeField(_('date created'), auto_now_add=True)
    tstamp = models.DateTimeField(_('date edited'), auto_now=True)

    def __unicode__(self):
        return self.summary
