# -*- coding: utf-8 -*-
import pytz
from django import forms
from webgcal.models import Calendar, Website

class CalendarForm(forms.ModelForm):
    name = forms.CharField(required=True,
        label='Name', help_text='Type in a calendar name.')

    class Meta:
        model = Calendar
        fields = ['name']

class WebsiteForm(forms.ModelForm):
    name = forms.CharField(required=True,
        label='Name', help_text='Type in a website name.')
    href = forms.URLField(required=True,
        label='Link', help_text='Type in a website link.')
    timezone = forms.ChoiceField(required=True,
        label='Timezone', help_text='Select default timezone.',
        choices=map(lambda x: (x, x), pytz.common_timezones),
        initial='UTC')

    class Meta:
        model = Website
        fields = ['name', 'href', 'timezone']
