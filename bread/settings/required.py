import pkg_resources

from django.conf.global_settings import DATETIME_INPUT_FORMATS

__breadapps = set()
for entrypoint in pkg_resources.iter_entry_points(
    group="breadapp", name="installed_apps"
):
    __breadapps.update(entrypoint.load())

__third_party_apps = set(
    [
        "crispy_forms",
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

__breadapps -= __third_party_apps

# apps which are required for bread to work
BREAD_DEPENDENCIES = (
    ["django.contrib.admin"]
    + list(__breadapps)
    + ["bread.apps.BreadConfig"]
    + list(__third_party_apps)
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
    }
}
# required to compile sass theme
COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

# required to make crispyforms working with our materaialize frontend
CRISPY_TEMPLATE_PACK = "materialize"
CRISPY_ALLOWED_TEMPLATE_PACKS = [CRISPY_TEMPLATE_PACK]

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
