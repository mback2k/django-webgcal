#!/bin/sh
set -e

if [ "${DJANGO_PERFORM_SETUP}" = "yes" ]; then
    /usr/bin/python3 manage.py migrate --run-syncdb
fi

exit 0