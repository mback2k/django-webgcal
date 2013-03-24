# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url

urlpatterns = patterns('webgcal.views',
    (r'^$', 'show_home'),
    (r'^dashboard/$', 'show_dashboard'),
    (r'^dashboard/calendar/create/$', 'create_calendar'),
    (r'^dashboard/calendar/(?P<calendar_id>\d+)/$', 'show_calendar'),
    (r'^dashboard/calendar/(?P<calendar_id>\d+)/edit/$', 'edit_calendar'),
    (r'^dashboard/calendar/(?P<calendar_id>\d+)/switch/$', 'switch_calendar'),
    (r'^dashboard/calendar/(?P<calendar_id>\d+)/delete/$', 'delete_calendar'),
    (r'^dashboard/calendar/(?P<calendar_id>\d+)/delete/ask/$', 'delete_calendar_ask'),
    (r'^dashboard/calendar/(?P<calendar_id>\d+)/website/create/$', 'create_website'),
    (r'^dashboard/calendar/(?P<calendar_id>\d+)/website/(?P<website_id>\d+)/edit/$', 'edit_website'),
    (r'^dashboard/calendar/(?P<calendar_id>\d+)/website/(?P<website_id>\d+)/switch/$', 'switch_website'),
    (r'^dashboard/calendar/(?P<calendar_id>\d+)/website/(?P<website_id>\d+)/delete/$', 'delete_website'),
    (r'^dashboard/calendar/(?P<calendar_id>\d+)/website/(?P<website_id>\d+)/delete/ask/$', 'delete_website_ask'),
    (r'^login/$', 'redirect_login')
)
