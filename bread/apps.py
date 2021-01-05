from django.apps import AppConfig


class BreadConfig(AppConfig):

    name = "bread"
    verbose_name = "Bread Engine"

    def ready(self):
        from django.utils.module_loading import autodiscover_modules

        autodiscover_modules("layouts")
        autodiscover_modules("views")
