#!/bin/sh
set -e

if [ "${DJANGO_PERFORM_SETUP}" = "yes" ]; then
if [ "${DJANGO_SETTINGS_MODULE}" = "webgcal.settings.docker" ]; then
    /usr/bin/python3 manage.py loaddata docker-fixture.json
fi
fi

exit 0