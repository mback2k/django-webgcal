# -*- coding: utf-8 -*-
from swampdragon import route_handler
from swampdragon.route_handler import ModelRouter
from .models import Calendar, Website
from .serializers import CalendarSerializer, WebsiteSerializer

class CalendarRouter(ModelRouter):
    route_name = 'calendar'
    serializer_class = CalendarSerializer
    model = Calendar

    def get_object(self, **kwargs):
        return self.model.objects.filter(user=self.connection.user).get(id=kwargs['id'])

    def get_query_set(self, **kwargs):
        return self.model.objects.filter(user=self.connection.user).filter(id=kwargs['id'])

class WebsiteRouter(ModelRouter):
    route_name = 'website'
    serializer_class = WebsiteSerializer
    model = Website

    def get_object(self, **kwargs):
        return self.model.objects.filter(calendar__user=self.connection.user).get(id=kwargs['id'])

    def get_query_set(self, **kwargs):
        return self.model.objects.filter(calendar__user=self.connection.user).filter(id=kwargs['id'])

route_handler.register(CalendarRouter)
route_handler.register(WebsiteRouter)
