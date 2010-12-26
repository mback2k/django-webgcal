# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

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
    (r'^authsub/request/$', 'authsub_request'),
    (r'^authsub/response/$', 'authsub_response'),
)

urlpatterns += patterns('webgcal.methods',
    (r'^cron/worker/start/$', 'start_worker'),
    (r'^taskqueue/calendar/(?P<calendar_id>\d+)/update/$', 'update_calendar'),
    (r'^taskqueue/calendar/(?P<calendar_id>\d+)/website/(?P<website_id>\d+)/parse/$', 'parse_website'),
)
