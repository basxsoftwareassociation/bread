import ast
import inspect
import re

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Field, fields
from django.utils.translation import gettext_lazy as _

from basxbread.utils import get_all_subclasses


def validate_choices(value):
    val = ast.literal_eval(value)
    if not isinstance(val, (tuple, list)):
        raise ValidationError(
            _("%(value)s is not a list or tuple"), params={"value": value}
        )
    for i in val:
        if len(i) != 2:
            raise ValidationError(
                _("%(value)s does not only contain 2-tuples"), params={"value": value}
            )


def valid_ordering(value):
    val = ast.literal_eval(value)
    for i in val:
        if not isinstance(i, str):
            raise ValidationError(
                _("%(value)s does not only contain list of fields"),
                params={"value": value},
            )
        i = i[1:] if i.startswith("-") else i
        if not i.isidentifier():
            raise ValidationError(
                _("%(value)s does not only contain list of fields"),
                params={"value": value},
            )


def validate_identifier(value):
    if not value.isidentifier():
        raise ValidationError(
            _("%(value)s is not a valid Python identifier"), params={"value": value}
        )


def validate_literal(value):
    try:
        ast.literal_eval(value)
    except Exception:
        raise ValidationError(
            _("%(value)s is not a valid Python literal"), params={"value": value}
        )


class ModelForm(forms.Form):
    name = forms.CharField(
        label=_("Model name"),
        help_text=_(
            "Python identifier for the model (no spaces and special characters). Only used internally."
        ),
        required=True,
        max_length=255,
        strip=True,
        validators=[validate_identifier],
    )
    verbose_name = forms.CharField(
        label=_("Verbose name"),
        help_text=_("Name that will be used as label for the model."),
        required=True,
        max_length=255,
        strip=True,
    )
    verbose_name_plural = forms.CharField(
        label=_("Verbose name plural"),
        help_text=_("Name that will be used as label for the model in plural form."),
        required=True,
        max_length=255,
        strip=True,
    )
    ordering = forms.CharField(
        label=_("Ordering"),
        help_text=_(
            "List of space separated fields that determine the default ordering for the objects of this model type"
        ),
        max_length=1024,
        initial="[]",
        required=False,
        strip=True,
        validators=[validate_literal, valid_ordering],
    )
    order_with_respect_to = forms.CharField(
        label=_("Order with respect to"),
        help_text=_("Order with respect to foreign key field"),
        max_length=1024,
        required=False,
        strip=True,
        validators=[validate_literal],
    )

    def apply_changes(self, model):
        filename = inspect.getfile(model)
        with open(filename) as modelfile:
            source = modelfile.read()
            sourcelines = source.splitlines()
            a = ast.parse(source, filename=filename)
            for node in ast.walk(a):
                if isinstance(node, ast.ClassDef) and node.name == model.__name__:
                    classsource = sourcelines[node.lineno - 1][
                        node.col_offset : node.end_col_offset
                    ]
                    print(
                        re.sub(
                            rf"class {model.__name__}\((.*)\):",
                            rf"class {self.cleaned_data['name']}(\1)",
                            classsource,
                        )
                    )


def fieldtypename(fieldtype):
    return f"{fieldtype.__module__}.{fieldtype.__qualname__}"


def fieldtypes():
    return {
        fieldtypename(fieldtype): fieldtype for fieldtype in get_all_subclasses(Field)
    }


def typechoices():
    return tuple((value, type.__name__) for value, type in fieldtypes().items())


def typecoerce(value):
    if isinstance(value, str):
        return fieldtypes().get(value, None)
    return value


class DefaultField(forms.CharField):
    def _coerce(self, value):
        if isinstance(value, str):
            if value == "":
                return fields.NOT_PROVIDED
        return value

    def clean(self, value):
        value = super().clean(value)
        return self._coerce(value)


class FieldForm(forms.Form):
    name = forms.CharField(
        label=_("Field name"),
        help_text=_(
            "Python identifier for the field (no spaces and special characters). Only used internally."
        ),
        required=True,
        max_length=255,
        strip=True,
        validators=[validate_identifier],
    )
    type = forms.TypedChoiceField(
        choices=typechoices, coerce=typecoerce, empty_value=None
    )
    verbose_name = forms.CharField(
        label=_("Verbose name"),
        help_text=_("Name that will be used as label for the field."),
        required=False,
        max_length=255,
        strip=True,
    )
    null = forms.BooleanField(
        label=_("Null"),
        help_text=_("Allo this field to be null (not same as empty string)"),
        initial=False,
        required=False,
    )
    blank = forms.BooleanField(
        label=_("Blank"),
        help_text=_("Do not require this field to be filled out on forms"),
        initial=False,
        required=False,
    )
    editable = forms.BooleanField(
        label=_("Editable"),
        help_text=_("Allow this field to be edited via forms"),
        initial=True,
        required=False,
    )
    primary_key = forms.BooleanField(
        label=_("Primary key"),
        help_text=_("Make this field the primary key"),
        initial=False,
        required=False,
    )
    unique = forms.BooleanField(
        label=_("Unique"),
        help_text=_("Ensure this field is unique over all instances of the model"),
        initial=False,
        required=False,
    )
    help_text = forms.CharField(
        label=_("Help text"),
        help_text=_("Additional text to be displayed with the field"),
        max_length=1024,
        required=False,
    )
    default = DefaultField(
        label=_("Default"),
        help_text=_("Default value for this field, must be a Python literal"),
        required=False,
        max_length=1024,
        validators=[validate_literal],
    )
    choices = forms.CharField(
        label=_("Choices"),
        help_text=_(
            "Iterable of 2-tuples with (value, label) literals, generates a select input"
        ),
        required=False,
        max_length=1024,
        validators=[validate_literal, validate_choices],
    )

    # Special, depending on field:
    # max_length: int (BinaryField, CharField, EmailField, FileField)
    # auto_now: bool (DateField, DateTimeField)
    # auto_now_add: bool (DateField, DateTimeField)
    # max_digits: int (DecimalField)
    # decimal_places: int (DecimalField)
    # upload_to: path (FileField)

    def apply_changes(self, model):
        pass


def model2formdata(model):
    return {
        "name": model.__name__,
        "verbose_name": getattr(model._meta, "verbose_name"),
        "verbose_name_plural": getattr(model._meta, "verbose_name_plural"),
        "ordering": getattr(model._meta, "ordering") or "",
        "order_with_respect_to": getattr(model._meta, "order_with_respect_to"),
    }


def field2formdata(field):
    default = getattr(field, "default")
    return {
        "type": fieldtypename(type(field)),
        "name": getattr(field, "name"),
        "verbose_name": getattr(field, "verbose_name"),
        "null": getattr(field, "null"),
        "blank": getattr(field, "blank"),
        "editable": getattr(field, "editable"),
        "primary_key": getattr(field, "primary_key"),
        "unique": getattr(field, "unique"),
        "help_text": getattr(field, "help_text"),
        "default": "" if default == fields.NOT_PROVIDED else default,
        "choices": getattr(field, "choices"),
    }


def parse():
    return None
