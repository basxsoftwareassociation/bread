import pkg_resources
from django.conf.global_settings import DATETIME_INPUT_FORMATS
from easy_thumbnails.conf import Settings as thumbnail_settings

__breadapps = []
for entrypoint in pkg_resources.iter_entry_points(group="breadapp", name="appconfig"):
    for dependency in entrypoint.load().bread_dependencies:
        if dependency not in __breadapps:
            __breadapps.append(dependency)

_third_party_apps = [
    "crispy_forms",
    "ckeditor",
    "ckeditor_uploader",
    "guardian",
    "dynamic_preferences",
    "dynamic_preferences.users.apps.UserPreferencesConfig",
    "compressor",
    "easy_thumbnails",
    "image_cropping",
    "djmoney",
    "djmoney.contrib.exchange",
    "django_celery_results",
    "django_celery_beat",
    "django_markdown2",
    "django_filters",
    "django_extensions",
]
_django_apps = [
    "django.forms",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
]

for basedependency in _third_party_apps + _django_apps:
    if basedependency in __breadapps:
        __breadapps.remove(basedependency)

# apps which are required for bread to work, order is important
BREAD_DEPENDENCIES = (
    ["django.contrib.admin"]
    + __breadapps
    + ["bread.apps.BreadConfig"]
    + _third_party_apps
    + _django_apps
)

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
# required to compile sass theme
COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

# required to make crispyforms working with our materaialize frontend
CRISPY_ALLOWED_TEMPLATE_PACKS = ["materialize_forms", "carbon_design"]
CRISPY_TEMPLATE_PACK = CRISPY_ALLOWED_TEMPLATE_PACKS[0]

# required for the materialize datetime widget
DATETIME_INPUT_FORMATS += ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]

# not sure why we need this
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "login"

# required for compressor (which is the base of the sass compiler)
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
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "bread.middleware.RequireAuthenticationMiddleware",
]
SITE_ID = 1

BREAD_PUBLIC_FILES_PREFIX = "public/"

IMAGE_CROPPING_BACKEND = "image_cropping.backends.easy_thumbs.EasyThumbnailsBackend"
IMAGE_CROPPING_BACKEND_PARAMS = {}
THUMBNAIL_PROCESSORS = (
    "image_cropping.thumbnail_processors.crop_corners",
) + thumbnail_settings.THUMBNAIL_PROCESSORS

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

DATETIME_FORMAT = "Y-m-d h:M:s"
DATE_FORMAT = "Y-m-d"

COMPRESS_OFFLINE_CONTEXT = "bread.context_processors.compress_offline_context"
CARBON_DESIGN_CONTEXT = {
    "prefix": "bx",
    "header": {
        "name": "PRODUCT_NAME",
        "company": "COMPANY_NAME",
        "platform": "PLATFORM_NAME",
        "actions": [{"title": "ACTION_1", "switcher": None}],
    },
}

DEFAULT_PAGINATION = 1000
DEFAULT_PAGINATION_CHOICES = [10, 100, 1000]
