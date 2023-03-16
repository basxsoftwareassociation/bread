from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReportsConfig(AppConfig):
    name = "basxbread.contrib.reports"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Reports")
