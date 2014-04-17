# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Calendar, Website, Event

class CalendarAdmin(admin.ModelAdmin):
    fields = ('name', 'user', 'google_id')
    list_display = ('name', 'user', 'updated', 'status', 'tasks', 'has_running_task', 'enabled')
    ordering = ('name',)

class WebsiteAdmin(admin.ModelAdmin):
    fields = ('name', 'calendar', 'href')
    list_display = ('name', 'calendar', 'updated', 'status', 'tasks', 'has_running_task', 'enabled')
    ordering = ('name',)

class EventAdmin(admin.ModelAdmin):
    fields = ('summary', 'website', 'google_id', 'dtstart', 'dtend')
    list_display = ('summary', 'website', 'parsed', 'synced')

admin.site.register(Calendar, CalendarAdmin)
admin.site.register(Website, WebsiteAdmin)
admin.site.register(Event, EventAdmin)
