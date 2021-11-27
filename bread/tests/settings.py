from bread.settings.required import *  # noqa

INSTALLED_APPS = BREAD_DEPENDENCIES + ["django.contrib.admin"]  # noqa
SECRET_KEY = "test"  # nosec because this is only used to run tests
ROOT_URLCONF = "bread.tests.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
    },
}
STATIC_URL = "static/"
