import re

from ckeditor_uploader.fields import RichTextUploadingFormField
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.forms import TypedChoiceField
from django.utils.html import strip_tags
from dynamic_preferences.types import StringPreference


class GenericForeignKeyField(TypedChoiceField):
    @classmethod
    def objects_to_choices(cls, objects, required=True):
        if not required:
            yield None, "---"
        for obj in objects:
            yield (
                f"{ContentType.objects.get_for_model(obj).pk},{obj.pk}",
                f"{obj._meta.verbose_name.title()}: {strip_tags(str(obj))}",
            )

    def __init__(self, **kwargs):
        if "initial" in kwargs and kwargs["initial"]:
            obj = kwargs["initial"]
            kwargs["initial"] = f"{ContentType.objects.get_for_model(obj).pk},{obj.pk}"

        def convert(value):
            contentype_id, object_id = map(int, value.split(","))
            return ContentType.objects.get(pk=contentype_id).get_object_for_this_type(
                pk=object_id
            )

        super().__init__(coerce=convert, empty_value=None, **kwargs)


class RichTextTemplateFormField(RichTextUploadingFormField):
    def __init__(self, *args, **kwargs):
        self.placeholders = kwargs.pop("placeholders")
        super().__init__(*args, **kwargs)

    def get_bound_field(self, form, field_name):
        ret = super().get_bound_field(form, field_name)
        ret.no_styling = True
        return ret


class RichTextTemplatePreference(StringPreference):
    brackets_re = re.compile(r"\[\[([^]]+)\]\]")
    field_class = RichTextTemplateFormField

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "placeholders") or not hasattr(
            cls.placeholders, "__iter__"
        ):
            raise TypeError(
                f"{cls.__name__} needs to define 'placeholders' as a list of strings"
            )
        super().__init_subclass__(**kwargs)

    def get_field_kwargs(self):
        ret = super().get_field_kwargs()
        if len(self.placeholders) > 0:
            if ret["help_text"] is None:
                ret["help_text"] = ""
            ret["help_text"] += f"Placeholders: [[{']], [['.join(self.placeholders)}]]"
        ret["placeholders"] = self.placeholders
        return ret

    def validate(self, value):
        super().validate(value)
        for match in re.finditer(RichTextTemplatePreference.brackets_re, value):
            placeholder = match.group()[2:-2]
            if placeholder.strip() not in self.placeholders:
                raise ValidationError(f"'{placeholder}' is not a valid placeholder.")
