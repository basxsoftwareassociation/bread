from django.apps import AppConfig
from django.contrib.messages.constants import DEFAULT_TAGS
from django.utils.translation import gettext as _


class BasxBreadConfig(AppConfig):
    name = "basxbread"
    verbose_name = "basx BREAD Engine"

    def ready(self):
        # trigger translation of message tags
        [_(tag.capitalize()) for tag in DEFAULT_TAGS.values()]
        patch_django_filters_verbose_name_func()


def patch_django_filters_verbose_name_func():
    # django filters verbose_field_name function is not great at using the
    # verbose names on related fields, patching this here
    from django_filters import utils
    from django_filters.utils import ForeignObjectRel, force_str, get_field_parts

    def improved_verbose_field_name_func(model, field_name):
        if field_name is None:
            return "[invalid name]"

        parts = get_field_parts(model, field_name)
        if not parts:
            return "[invalid name]"

        names = []
        for part in parts:
            if isinstance(part, ForeignObjectRel):
                if hasattr(part, "related_model"):
                    names.append(force_str(part.related_model._meta.verbose_name))
                else:
                    return "[invalid name]"
            else:
                names.append(force_str(part.verbose_name))

        return " ".join(names)

    utils.verbose_field_name = improved_verbose_field_name_func
