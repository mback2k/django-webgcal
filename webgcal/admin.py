from django.contrib import admin
from webgcal.models import Calendar, Website, Event

class CalendarAdmin(admin.ModelAdmin):
    fields = ('user', 'name', 'href')
    list_display = ('user', 'name', 'crdate', 'tstamp')
    ordering = ('crdate',)

class WebsiteAdmin(admin.ModelAdmin):
    fields = ('calendar', 'name', 'href')
    list_display = ('calendar', 'name', 'crdate', 'tstamp')
    ordering = ('crdate',)

class EventAdmin(admin.ModelAdmin):
    fields = ('website', 'summary', 'dtstart')
    list_display = ('website', 'summary', 'dtstart', 'crdate', 'tstamp')
    ordering = ('crdate',)

admin.site.register(Calendar, CalendarAdmin)
admin.site.register(Website, WebsiteAdmin)
admin.site.register(Event, EventAdmin)
