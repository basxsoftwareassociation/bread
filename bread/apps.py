from django.apps import AppConfig


class BreadConfig(AppConfig):

    name = "bread"
    verbose_name = "Bread Engine"

    def ready(self):
        from . import admin
        from django.utils.module_loading import autodiscover_modules

        autodiscover_modules("views")
        autodiscover_modules("bread")
        admin.site.register_menus()
