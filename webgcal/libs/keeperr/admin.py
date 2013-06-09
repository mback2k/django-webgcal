# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Error

class ErrorAdmin(admin.ModelAdmin):
    list_display = ('exc_type', 'exc_value', 'exc_timestamp')
    ordering = ('-exc_timestamp',)

admin.site.register(Error, ErrorAdmin)
