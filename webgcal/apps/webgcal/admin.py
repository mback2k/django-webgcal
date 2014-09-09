# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Calendar, Website, Event

class CalendarAdmin(admin.ModelAdmin):
    fields = ('name', 'user', 'google_id')
    list_display = ('name', 'user', 'updated', 'status', 'has_running_task', 'has_ready_task', 'enabled')
    search_fields = ('name',)
    ordering = ('name',)

class WebsiteAdmin(admin.ModelAdmin):
    fields = ('name', 'calendar', 'href')
    list_display = ('name', 'calendar', 'updated', 'status', 'has_running_task', 'has_ready_task', 'enabled')
    search_fields = ('name',)
    ordering = ('name',)

class EventAdmin(admin.ModelAdmin):
    readonly_fields = ('parsed', 'synced')
    fieldsets = (
        (None, {
            'fields': ('summary', 'website', 'google_id', 'parsed', 'synced')
        }),
        ('Event Information', {
            'fields': ('uid', 'summary', 'description', 'location', 'category',
                       'status', 'dtstart', 'dtend', 'dtstamp', 'last_modified')
        }),
    )
    list_display = ('summary', 'website', 'parsed', 'synced')
    search_fields = ('uid', 'summary', 'description', 'location', 'category', 'status')

admin.site.register(Calendar, CalendarAdmin)
admin.site.register(Website, WebsiteAdmin)
admin.site.register(Event, EventAdmin)
