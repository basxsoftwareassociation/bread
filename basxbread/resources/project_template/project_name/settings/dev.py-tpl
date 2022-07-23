# flake8: noqa
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# SECURITY WARNING: This should not be empty
AUTH_PASSWORD_VALIDATORS = []


try:
    from .local import *
except ImportError:
    pass
