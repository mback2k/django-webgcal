WebGCal
=======

Dependencies
------------
- Django             [https://www.djangoproject.com/]
- Celery             [http://www.celeryproject.org/]
- isodate            [http://pypi.python.org/pypi/isodate/]
- Google Data API    [https://code.google.com/p/gdata-python-client/]
- Beautiful Soup 4   [http://www.crummy.com/software/BeautifulSoup/]
- django-celery      [https://github.com/ask/django-celery]
- django_compressor  [https://github.com/jezdez/django_compressor]
- django-googleauth  [https://github.com/mback2k/django-googleauth]
- django-googledata  [https://github.com/mback2k/django-googledata]
- django-jdatetime   [https://github.com/mback2k/django-jdatetime]
- django-yamlcss     [https://github.com/mback2k/django-yamlcss]

Message Broker 
--------------
- Kombu              [http://pypi.python.org/pypi/kombu/]
- django-kombu       [https://github.com/ask/django-kombu]

All Celery supported AMQP message broker can be used.

Required Configuration
----------------------
In order to use WebGCal the Django project needs to have a complete settings.py.
The following Django settings are required to run WebGCal:

- BROKER_URL and other required message broker settings
- DATABASES
- DEFAULT_FROM_EMAIL
- SECRET_KEY

All other settings are pre-configured inside basesettings.py, which can be imported using the following line in your settings.py:

    from basesettings import *