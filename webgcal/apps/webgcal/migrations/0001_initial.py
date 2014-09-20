# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Calendar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('google_id', models.CharField(max_length=200, null=True, verbose_name='Google ID', blank=True)),
                ('updated', models.DateTimeField(null=True, verbose_name='Date updated', blank=True)),
                ('enabled', models.BooleanField(default=True, verbose_name='Enabled')),
                ('status', models.TextField(null=True, verbose_name='Status', blank=True)),
                ('user', models.ForeignKey(related_name=b'calendars', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('google_id', models.CharField(max_length=200, null=True, verbose_name='Google ID', blank=True)),
                ('parsed', models.DateTimeField(default=datetime.date(1, 1, 1), verbose_name='Date parsed')),
                ('synced', models.DateTimeField(default=datetime.date(1, 1, 1), verbose_name='Date synced')),
                ('deleted', models.BooleanField(default=False, verbose_name='Deleted')),
                ('uid', models.TextField(null=True, verbose_name='UID', blank=True)),
                ('summary', models.TextField(verbose_name='Summary')),
                ('description', models.TextField(null=True, verbose_name='Description', blank=True)),
                ('location', models.TextField(null=True, verbose_name='Location', blank=True)),
                ('category', models.TextField(null=True, verbose_name='Category', blank=True)),
                ('status', models.TextField(null=True, verbose_name='Status', blank=True)),
                ('dtstart', models.DateTimeField(verbose_name='DTStart')),
                ('dtend', models.DateTimeField(null=True, verbose_name='DTEnd', blank=True)),
                ('dtstamp', models.DateTimeField(null=True, verbose_name='DTStamp', blank=True)),
                ('last_modified', models.DateTimeField(null=True, verbose_name='Last modified', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Website',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('href', models.URLField(verbose_name='Link')),
                ('timezone', models.CharField(default=b'UTC', max_length=50, verbose_name='Timezone')),
                ('updated', models.DateTimeField(null=True, verbose_name='Date updated', blank=True)),
                ('enabled', models.BooleanField(default=True, verbose_name='Enabled')),
                ('status', models.TextField(null=True, verbose_name='Status', blank=True)),
                ('calendar', models.ForeignKey(related_name=b'websites', to='webgcal.Calendar')),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='event',
            name='website',
            field=models.ForeignKey(related_name=b'events', to='webgcal.Website'),
            preserve_default=True,
        ),
    ]
