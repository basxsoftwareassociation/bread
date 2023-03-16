from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ModelEditConfig(AppConfig):
    name = "basxbread.contrib.modeledit"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Model editing (WIP)")
