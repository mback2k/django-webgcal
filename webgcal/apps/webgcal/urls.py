# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from . import views

urlpatterns = (
    url(r'^$', views.show_home, name='show_home'),
    url(r'^dashboard/$', views.show_dashboard, name='show_dashboard'),
    url(r'^dashboard/calendar/create/$', views.create_calendar, name='create_calendar'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/$', views.show_calendar, name='show_calendar'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/edit/$', views.edit_calendar, name='edit_calendar'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/switch/$', views.switch_calendar, name='switch_calendar'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/delete/$', views.delete_calendar, name='delete_calendar'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/delete/ask/$', views.delete_calendar_ask, name='delete_calendar_ask'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/sync/now/$', views.sync_calendar_now, name='sync_calendar_now'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/website/create/$', views.create_website, name='create_website'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/website/(?P<website_id>\d+)/edit/$', views.edit_website, name='edit_website'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/website/(?P<website_id>\d+)/switch/$', views.switch_website, name='switch_website'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/website/(?P<website_id>\d+)/delete/$', views.delete_website, name='delete_website'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/website/(?P<website_id>\d+)/delete/ask/$', views.delete_website_ask, name='delete_website_ask'),
    url(r'^dashboard/calendar/(?P<calendar_id>\d+)/website/(?P<website_id>\d+)/parse/now/$', views.parse_website_now, name='parse_website_now'),
    url(r'^login/$', views.redirect_login, name='redirect_login')
)
