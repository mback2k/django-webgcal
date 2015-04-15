FROM python:2-wheezy

MAINTAINER Marc Hoersken "info@marc-hoersken.de"

RUN apt-get update
RUN apt-get install -y python-dev python-setuptools python-mysqldb
RUN apt-get clean

RUN useradd --user-group --home /usr/src django
RUN chown django:django -R /usr/src

USER django
RUN mkdir -p /usr/src/env
RUN virtualenv /usr/src/env

RUN /usr/src/env/bin/pip install --upgrade pip
RUN /usr/src/env/bin/pip install mysql-python

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN /usr/src/env/bin/pip install -r requirements.txt

ADD . /usr/src/app

USER root
RUN chown django:django -R /usr/src

USER django
RUN /usr/src/env/bin/python -m compileall /usr/src/app

ENV DJANGO_SETTINGS_MODULE=webgcal.settings.docker
RUN /usr/src/env/bin/python manage.py collectstatic --noinput
RUN /usr/src/env/bin/python manage.py compress --force

EXPOSE 8000
CMD /usr/src/env/bin/python manage.py runserver 0.0.0.0:8000
