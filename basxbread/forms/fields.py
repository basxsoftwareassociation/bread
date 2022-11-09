from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags


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


class BoundFormsetField(forms.BoundField):
    @property
    def formset(self):
        prefix = self.field.formsetclass.get_default_prefix()
        if self.form.prefix:
            prefix = f"{self.form.prefix}-{prefix}"
        return self.field.formsetclass(
            self.form.data if self.form.is_bound else None,
            self.form.files if self.form.is_bound else None,
            instance=self.field.parent_instance,
            prefix=prefix,
            initial=self.field.initial,
            **(self.field.formsetargs or {}),
        )

    @property
    def data(self):
        return self.formset


class FormsetField(forms.Field):
    def __init__(
        self, formsetclass, parent_instance, formsetargs=None, *args, **kwargs
    ):
        self.widget = FormsetWidget(formsetclass, parent_instance, formsetargs)
        self.formsetclass = formsetclass
        self.parent_instance = parent_instance
        self.formsetargs = formsetargs
        kwargs["required"] = False
        kwargs.setdefault("label", formsetclass.model._meta.verbose_name_plural)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, self.formsetclass):
            return value
        return self.formsetclass(**value)

    def validate(self, value):
        super().validate(value)
        if not value.is_valid():
            for formerrors in value.errors:
                for field, errorlist in formerrors.items():
                    for error in errorlist:
                        if isinstance(error, str):
                            error = ValidationError(error)
                        raise error

    def get_bound_field(self, form, field_name):
        return BoundFormsetField(form, self, field_name)


class FormsetWidget(forms.Widget):
    def __init__(
        self, formsetclass, parent_instance, *args, formsetargs=None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.formsetclass = formsetclass
        self.formsetargs = formsetargs
        self.parent_instance = parent_instance
        self.needs_multipart_form = self.formsetclass().is_multipart()
        self.template_name = "django/forms/widgets/text.html"  # we set this in order to prevent __str__ on the parent form to fail

    def value_from_datadict(self, data, files, name):
        return {
            "data": data,
            "files": files,
            "instance": self.parent_instance,
            "prefix": name,
            **(self.formsetargs or {}),
        }
