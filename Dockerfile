FROM mback2k/ubuntu:bionic

RUN adduser --disabled-password --disabled-login --system --group \
        --uid 999 --home /app django

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-dev python3-pip python3-mysqldb && \
    apt-get install -y --no-install-recommends \
        build-essential && \
    apt-get clean

RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install --upgrade rollbar

RUN mkdir -p /app
WORKDIR /app

ADD requirements.txt /app/requirements.txt
RUN pip3 install --upgrade --requirement requirements.txt

ADD . /app
RUN python3 -m compileall /app

ENV DJANGO_SETTINGS_MODULE=webgcal.settings.docker

RUN python3 manage.py collectstatic --noinput
RUN python3 manage.py compress --force

USER django
EXPOSE 8000

ADD docker-entrypoint.d/ /run/docker-entrypoint.d/

CMD ["/usr/bin/python3", "manage.py", "runserver", "0.0.0.0:8000"]
