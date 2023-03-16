from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TaxonomyConfig(AppConfig):
    name = "basxbread.contrib.taxonomy"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Taxonomies")
