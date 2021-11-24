#!/usr/bin/env python

import sys

import django
from django.conf import settings

INSTALLED_APPS = [
    "django_extensions",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "guardian",
    "bread",
    "bread.contrib.reports",
    "bread.contrib.workflows",
    "django_celery_results",
]

settings.configure(  # nosec because this is only for local development
    DEBUG=True,
    USE_TZ=True,
    USE_I18N=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    MIDDLEWARE=(
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "bread.middleware.RequireAuthenticationMiddleware",
    ),
    SITE_ID=1,
    INSTALLED_APPS=INSTALLED_APPS,
    AUTHENTICATION_BACKENDS=(
        "django.contrib.auth.backends.ModelBackend",
        "guardian.backends.ObjectPermissionBackend",
    ),
    SECRET_KEY="SECRET_KEY_FOR_TESTING",
    STATIC_URL="static/",
    ROOT_URLCONF="bread.tests.urls",
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                    "dynamic_preferences.processors.global_preferences",
                    "bread.context_processors.bread_context",
                ]
            },
        }
    ],
)

django.setup()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
