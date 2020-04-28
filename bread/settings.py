import pkg_resources

from django.conf.global_settings import DATETIME_INPUT_FORMATS
from django.utils.html import mark_safe

breadapps = set(["bread.apps.BreadConfig"])
for entrypoint in pkg_resources.iter_entry_points(
    group="breadapp", name="installed_apps"
):
    breadapps.update(entrypoint.load())

third_party_apps = set(
    [
        "ckeditor",
        "ckeditor_uploader",
        "guardian",
        "dynamic_preferences",
        "compressor",
        "sorl.thumbnail",
        "django_markdown2",
        "django_filters",
        "django_extensions",
        "django.forms",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.humanize",
        "django.contrib.sites",
    ]
)

breadapps -= third_party_apps

BREAD_DEPENDENCIES = ["django.contrib.admin"] + list(breadapps) + list(third_party_apps)


CKEDITOR_UPLOAD_PATH = "ckeditor/"
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "full",
        "extraPlugins": ",".join(["placeholder"]),
        "width": "100%",
    }
}

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

# ISO 8601 datetime format to accept html5 datetime input values
DATETIME_INPUT_FORMATS += ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]

# auth settings
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# compressor settings
COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

HTML_TRUE = mark_safe("&#x2714;")  # ✔
HTML_FALSE = mark_safe("&#x2716;")  # ✖
HTML_NONE = mark_safe('<div class="center">&empty;</div>')  # ∅
