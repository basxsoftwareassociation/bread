from collections.abc import Iterable

from django.apps import AppConfig
from django.conf import settings
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
    required_settings = {
        "BREAD_PUBLIC_FILES_PREFIX": None,
        "CKEDITOR_UPLOAD_PATH": None,
        "CKEDITOR_CONFIGS": None,
        "STATICFILES_FINDERS": [
            "django.contrib.staticfiles.finders.AppDirectoriesFinder",
            "compressor.finders.CompressorFinder",
        ],
        "AUTHENTICATION_BACKENDS": ["guardian.backends.ObjectPermissionBackend"],
        "DATETIME_INPUT_FORMATS": ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"],
        "COMPRESS_PRECOMPILERS": None,
        "CRISPY_TEMPLATE_PACK": "materialize",
        "CRISPY_ALLOWED_TEMPLATE_PACKS": ["materialize"],
        "LOGIN_URL": None,
        "LOGIN_REDIRECT_URL": None,
        "LOGOUT_REDIRECT_URL": None,
    }
    for setting, required_value in required_settings.items():
        if hasattr(settings, setting):
            if isinstance(required_value, Iterable):
                current_value = getattr(settings, setting)
                if not isinstance(current_value, Iterable):
                    current_value = [current_value]
                diff = set(required_value) - set(current_value)
                if diff:
                    errors.append(
                        Error(
                            f"setting {setting} is missing some entries",
                            hint=f"{setting} must include {list(diff)}",
                            obj=None,
                            id=f"bread.setting_{setting}",
                        )
                    )
            elif required_value is not None:
                if getattr(settings, setting) != required_value:
                    errors.append(
                        Error(
                            f"setting {setting} has wrong value",
                            hint=f"Needs to be set to {required_value}",
                            obj=None,
                            id=f"bread.setting_{setting}",
                        )
                    )
        else:
            hint = ""
            if isinstance(required_value, Iterable):
                hint = f"Must contains the following values: {required_value}"
            elif required_value is not None:
                hint = f"Must be set to: {required_value}"
            errors.append(
                Error(
                    f"setting {setting} is missing",
                    hint=hint,
                    obj=None,
                    id=f"bread.setting_{setting}",
                )
            )
    return errors
