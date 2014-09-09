# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Error

class ErrorAdmin(admin.ModelAdmin):
    list_display = ('exc_type', 'exc_value', 'exc_timestamp', 'content_object')
    search_fields = ('exc_type', 'exc_value')
    ordering = ('-exc_timestamp',)

admin.site.register(Error, ErrorAdmin)
