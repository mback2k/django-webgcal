# -*- coding: utf-8 -*-
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
    href = forms.CharField(required=True,
        label='Link', help_text='Type in a website link.')

    class Meta:
        model = Website
        fields = ['name', 'href']
