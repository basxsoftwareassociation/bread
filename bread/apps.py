from django.apps import AppConfig
from django.core.checks import Error, register


class BreadConfig(AppConfig):

    name = "bread"
    verbose_name = "Bread Engine"

    def ready(self):
        from . import admin
        from django.utils.module_loading import autodiscover_modules

        autodiscover_modules("bread")
        admin.site.register_menus()

        register(bread_config_check)


def bread_config_check(app_configs, **kwargs):
    errors = []
    # TODO: check configured fields on views
    if False:
        errors.append(Error("an error", hint="A hint.", obj=None, id="bread.E001",))
    return errors
