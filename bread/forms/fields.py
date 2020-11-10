import re

from ckeditor_uploader.fields import RichTextUploadingFormField
from crispy_forms.utils import TEMPLATE_PACK
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from dynamic_preferences.types import StringPreference


class GenericForeignKeyField(forms.TypedChoiceField):
    @classmethod
    def object_to_choice(cls, obj):
        return (
            f"{ContentType.objects.get_for_model(obj).pk},{obj.pk}",
            f"{obj._meta.verbose_name.title()}: {strip_tags(str(obj))}",
        )

    @classmethod
    def objects_to_choices(cls, objects, required=True):
        yield None, "---"
        for obj in objects:
            yield GenericForeignKeyField.object_to_choice(obj)

    def __init__(self, **kwargs):
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


class FormsetField(forms.Field):
    def __init__(self, formsetclass, parent_instance, *args, **kwargs):
        self.widget = FormsetWidget(formsetclass, parent_instance)
        self.formsetclass = formsetclass
        self.parent_instance = parent_instance
        kwargs["required"] = False
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        return self.formsetclass(**(value or {"instance": self.parent_instance}))

    def validate(self, value):
        super().validate(value)
        if not value.is_valid():
            for formerrors in value.errors:
                for field, errorlist in formerrors.items():
                    for error in errorlist:
                        if isinstance(error, str):
                            error = ValidationError("A Form has errors")
                        raise error

    def _coerce(self, value):
        if isinstance(value, dict):
            ret = self.formsetclass(instance=value["instance"]).queryset.all()
        elif isinstance(value, self.formsetclass):
            ret = value.queryset.all()
        return list(ret)


class FormsetWidget(forms.Widget):
    def __init__(self, formsetclass, parent_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formsetclass = formsetclass
        self.parent_instance = parent_instance
        self.prefix = self.formsetclass.get_default_prefix()

    def render(self, name, value, attrs=None, renderer=None):
        return render_to_string(
            f"{TEMPLATE_PACK}/inline_formset.html",
            {
                "formset": self.formsetclass(**(value or {})),
                "form_show_errors": True,
                "form_show_labels": True,
            },
        )

    def value_from_datadict(self, data, files, name):
        # return all form data in order to allow populating the formset
        return {
            "data": data,
            "files": files,
            "instance": self.parent_instance,
        }
