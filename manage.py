#!/usr/bin/env python

import sys

import django
from django.conf import settings

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "guardian",
    "bread",
    "bread.contrib.reports",
    "bread.contrib.workflows",
]

settings.configure(  # nosec because this is only for local development
    DEBUG=True,
    USE_TZ=True,
    USE_I18N=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    MIDDLEWARE_CLASSES=(),
    SITE_ID=1,
    INSTALLED_APPS=INSTALLED_APPS,
    AUTHENTICATION_BACKENDS=(
        "django.contrib.auth.backends.ModelBackend",
        "guardian.backends.ObjectPermissionBackend",
    ),
    SECRET_KEY="SECRET_KEY_FOR_TESTING",
    STATIC_URL="static/",
)

django.setup()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
