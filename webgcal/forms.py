# -*- coding: utf-8 -*-
from django import forms
from webgcal.models import Calendar

class CalendarForm(forms.ModelForm):
    name = forms.CharField(required=True,
        label='Name', help_text='Type in a calendar name.')

    class Meta:
        model = Calendar
        fields = ['name']
