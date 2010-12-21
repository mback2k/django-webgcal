# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('webgcal.views',
    (r'^$', 'show_home'),
    (r'^dashboard/$', 'show_dashboard'),
    (r'^dashboard/create/$', 'create_item'),
    (r'^dashboard/show/(?P<id>\d+)/$', 'show_item'),
    (r'^dashboard/edit/(?P<id>\d+)/$', 'edit_item'),
    (r'^dashboard/delete/(?P<id>\d+)/$', 'delete_item'),
    (r'^dashboard/delete/(?P<id>\d+)/ask/$', 'delete_item_ask'),
)
