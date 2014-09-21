# -*- coding: utf-8 -*-
from swampdragon.serializers.model_serializer import ModelSerializer

class CalendarSerializer(ModelSerializer):
    class Meta:
        model = 'webgcal.Calendar'
        publish_fields = ('name', 'updated', 'enabled', 'status')

class WebsiteSerializer(ModelSerializer):
    class Meta:
        model = 'webgcal.Website'
        publish_fields = ('name', 'updated', 'enabled', 'status')
