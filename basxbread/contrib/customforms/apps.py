from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomForms(AppConfig):
    name = "basxbread.contrib.customforms"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Custom forms")
