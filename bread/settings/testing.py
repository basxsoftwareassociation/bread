"""This files contains only testing settings in order to easily run manage.py and tests. Never use them in production"""
import os
import tempfile

from bread.settings.required import *  # noqa

SITE_ID = 1

BASE_DIR = tempfile.mkdtemp()


STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

SECRET_KEY = "test"  # nosec
ROOT_URLCONF = "bread.tests.urls_testing"

INSTALLED_APPS = BREAD_DEPENDENCIES  # noqa

DEBUG = True
USE_TZ = True
USE_I18N = True
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
HAYSTACK_CONNECTIONS = {"default": ""}

TEMPLATES = [
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
            ]
        },
    }
]
