_third_party_apps = [
    "django_extensions",  # for developer friendliness
    "guardian",  # per-object permissions
    "compressor",  # asset handling
    "simple_history",  # versioning
    # some additional form fields
    "ckeditor",
    "ckeditor_uploader",
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
    "django_celery_beat",
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

# apps which are required for bread to work, order is important
BREAD_DEPENDENCIES = ["bread.apps.BreadConfig"] + _third_party_apps + _django_apps

# required to make per-object-permissions work
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

# required for CK editor to work properly
CKEDITOR_UPLOAD_PATH = "ckeditor/"
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "full",
        "extraPlugins": ",".join(["placeholder"]),
        "width": "100%",
    },
    "richtext-plugin": {
        "toolbar": "Custom",
        "format_tags": "h1;h2;h3;p;pre",
        "toolbar_Custom": [
            [
                "Format",
                "RemoveFormat",
                "-",
                "Bold",
                "Italic",
                "Subscript",
                "Superscript",
                "-",
                "NumberedList",
                "BulletedList",
                "-",
                "Anchor",
                "Link",
                "Unlink",
                "-",
                "HorizontalRule",
                "SpecialChar",
                "-",
                "Source",
            ]
        ],
    },
}
COMPRESS_OFFLINE_CONTEXT = "bread.context_processors.compress_offline_context"
COMPRESS_FILTERS = {
    "css": [
        "compressor.filters.css_default.CssAbsoluteFilter",
        "compressor.filters.cssmin.CSSCompressorFilter",
    ],
    "js": ["compressor.filters.jsmin.JSMinFilter"],
}

# not sure why we need this
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
# named urlpattern to redirect to if login is required
LOGIN_URL = "login"

# required for compressor
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

# celery related settings
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "bread.middleware.RequireAuthenticationMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

BREAD_PUBLIC_FILES_PREFIX = "public/"

# from default django config
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
                "bread.context_processors.bread_context",
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

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

DEFAULT_PAGINATION_CHOICES = [
    25,
    50,
    100,
]  # Defines what the default options for pagination are

HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"

# This one should only be activated in production or in dev environments with celery ready to run
# HAYSTACK_SIGNAL_PROCESSOR = "celery_haystack.signals.CelerySignalProcessor"

SIMPLE_HISTORY_FILEFIELD_TO_CHARFIELD = True
