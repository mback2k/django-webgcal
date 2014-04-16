WebGCal
=======

Dependencies
------------
- Django             [https://www.djangoproject.com/]
- Celery             [http://www.celeryproject.org/]
- pytz               [http://pytz.sourceforge.net/]
- isodate            [http://pypi.python.org/pypi/isodate/]
- Google API         [https://code.google.com/p/google-api-python-client/]
- Beautiful Soup 4   [http://www.crummy.com/software/BeautifulSoup/]
- django-celery      [https://github.com/ask/django-celery]
- django-celery-model [https://github.com/mback2k/django-celery-model]
- django_compressor  [https://github.com/jezdez/django_compressor]
- django-social-auth [https://github.com/omab/django-social-auth]
- django-appengine-auth [https://github.com/mback2k/django-appengine-auth]
- python-hcalendar   [https://github.com/mback2k/python-hcalendar]

Submodules
----------
- django-jdatetime   [https://github.com/mback2k/django-jdatetime]
- django-yamlcss     [https://github.com/mback2k/django-yamlcss]

Message Broker (during development)
--------------
- Kombu              [http://pypi.python.org/pypi/kombu/]
- django-kombu       [https://github.com/ask/django-kombu]

All Celery supported AMQP message brokers can be used.

Configuration
-------------
In order to use WebGCal the Django project needs to have a complete settings.py.
The following Django settings are required to run WebGCal:

- BROKER_URL and other required message broker settings
- DATABASES
- DEFAULT_FROM_EMAIL
- SECRET_KEY

All other settings are pre-configured inside settings/base.py, which can be imported using the following line in your settings/{env}.py:

    from .base import *

A basic development environment can be launched using the pre-configured settings/dev.py.

Installation
------------
First of all you need to install all the dependencies.
It is recommended to perform the installations using the pip command.

The next step is to get all source from github.com:

    git clone git://github.com/mback2k/django-webgcal.git webgcal
    
    cd webgcal
    
    git submodule init
    git submodule update

After that you need to collect and compress the static files using:

    python manage.py collectstatic --noinput
    python manage.py compress --force

Now you need to setup your webserver to serve the Django project.
Please take a look at the [Django documentation](https://docs.djangoproject.com/en/1.5/topics/install/) for more information.

You can run a development server using the following command:

    python manage.py runserver

Executing Tasks
---------------
Besides running the webserver, you need to run celeryd and celerybeat.
You can do this by executing the following command from your server's shell:

    python manage.py celeryd -B -E

License
-------
* Released under MIT License
* Copyright (c) 2012-2014 Marc Hoersken <info@marc-hoersken.de>
