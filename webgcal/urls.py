# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('webgcal.views',
    (r'^$', 'show_home'),
    (r'^dashboard/$', 'show_dashboard'),
    (r'^dashboard/create/$', 'create_item'),
    (r'^dashboard/status/(?P<id>\d+)/$', 'show_item'),
    (r'^dashboard/edit/(?P<id>\d+)/$', 'edit_item'),
    (r'^dashboard/switch/(?P<id>\d+)/$', 'switch_item'),
    (r'^dashboard/force/(?P<id>\d+)/$', 'force_item'),
    (r'^dashboard/feed/(?P<id>\d+)/$', 'feed_item'),
    (r'^dashboard/delete/(?P<id>\d+)/$', 'delete_item'),
    (r'^dashboard/delete/(?P<id>\d+)/ask/$', 'delete_item_ask'),
    (r'^feed/status/(?P<key>\w+)/$', 'feed_item_key'),
)
