from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PublicURLs(AppConfig):
    name = "basxbread.contrib.publicurls"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Public URLs")
