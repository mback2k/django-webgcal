# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
import traceback
import json
import sys

class Error(models.Model):
    exc_type = models.CharField(max_length=250)
    exc_value = models.TextField()
    exc_traceback = models.TextField()
    exc_timestamp = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    @classmethod
    def assign(cls, content_object):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return cls(exc_type=exc_type.__name__,
                   exc_value=unicode(exc_value),
                   exc_traceback=json.dumps(traceback.extract_tb(exc_traceback)),
                   content_object=content_object)

    def __unicode__(self):
        return u'%s: %s' % (self.exc_timestamp, self.exc_type)
