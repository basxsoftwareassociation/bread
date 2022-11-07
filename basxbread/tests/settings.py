from ..settings.required import *  # noqa

INSTALLED_APPS = BASXBREAD_DEPENDENCIES + [  # noqa
    "django.contrib.admin",
    "basxbread.contrib.reports",
    "basxbread.contrib.triggers",
    "basxbread.contrib.document_templates",
    "basxbread.contrib.languages",
    "basxbread.contrib.publicurls",
    "basxbread.contrib.taxonomy",
    "basxbread.contrib.customforms",
]

SECRET_KEY = "test"  # nosec because this is only used to run tests
ROOT_URLCONF = "basxbread.tests.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
    },
}
STATIC_URL = "static/"
