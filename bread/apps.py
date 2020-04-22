from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class BreadConfig(AppConfig):

    name = "bread"
    verbose_name = "Bread Engine"

    def ready(self):
        autodiscover_modules("bread")
