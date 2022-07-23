"""
These are sane default settings, some of which are required to
run a basxbread application properly out-of-the-box, however all
settings can be overwritten in the project-specific settings module

It is recommended to include these settings via
``from basxbread.settings.required import *`` inside the project
settings file. The ``BASXBREAD_DEPENDENCIES`` variable should be
appended to the ``INSTALLED_APPS`` setting.
"""

from django.utils.html import mark_safe

########################## Django settings ###############################
#
# Mostly for dependencies and sane defaults
#

_third_party_apps = [
    "django_extensions",  # for developer friendliness, adding management commands
    "guardian",  # per-object permissions
    "simple_history",  # versioning
    # some additional form fields
    "djangoql",
    # for handling global and user preferences
    "dynamic_preferences",
    "dynamic_preferences.users.apps.UserPreferencesConfig",
    # very commonly used model fields
    "django_countries",
    "djmoney",
    "djmoney.contrib.exchange",
    # task queue system
    "django_celery_results",
    # search index
    "haystack",
    "celery_haystack",
    "whoosh",
]
_django_apps = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# apps which are required for basxbread to work, order is important
BASXBREAD_DEPENDENCIES = (
    ["basxbread.apps.BasxBreadConfig"] + _third_party_apps + _django_apps
)

# required to make per-object-permissions work
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "basxbread.middleware.RequireAuthenticationMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]


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

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/"

LOGIN_URL = "login"

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

########################## celery settings ###############################

CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"

########################## haystack settings #############################

HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"

# The following should only be activated in production or in dev environments
# with a running celery instance (and an according rabbitmq server)
# HAYSTACK_SIGNAL_PROCESSOR = "celery_haystack.signals.CelerySignalProcessor"

########################## simple_history settings #######################

SIMPLE_HISTORY_FILEFIELD_TO_CHARFIELD = True

########################## BasxBread customization settings ##################
##########################         ALL REQUIRED         #################k

DEFAULT_PAGINATION_CHOICES = [
    25,
    50,
    100,
    -1,
]  # Defines what the default options for pagination are

BASXBREAD_PUBLIC_FILES_PREFIX = (
    "public"  # request starting with this path will not require login
)

AJAX_URLPARAMETER = "asajax"
HIDEMENUS_URLPARAMETER = "hidemenus"
PLATFORMNAME = mark_safe('Basx<span style="font-weight: 600">Bread</span>')


# custom unicode symbols, used for some formatting
HTML_TRUE = mark_safe("&#x2714;")  # ✔
HTML_FALSE = mark_safe("&#x2716;")  # ✖
HTML_NONE = mark_safe("&empty;")  # ∅
