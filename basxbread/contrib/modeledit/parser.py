import ast

import astor
import black
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_identifier(value):
    if not value.isidentifier():
        raise ValidationError(
            _("%(value)s is not a valid Python identifier"), params={"value": value}
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
        strip=True,
    )


class FieldForm(forms.Form):
    pass
    # Formset form "Field"
    # name: identifier
    # type_: Selection
    # null: bool
    # blank: bool
    # choice: JSON
    # default: literal
    # editable: bool
    # help_text: string
    # primary_key: bool
    # unique: bool
    # verbose_name: string
    #
    # Special, depending on field:
    # max_length: int (BinaryField, CharField, EmailField, FileField)
    # auto_now: bool (DateField, DateTimeField)
    # auto_now_add: bool (DateField, DateTimeField)
    # max_digits: int (DecimalField)
    # decimal_places: int (DecimalField)
    # upload_to: path (FileField)


def parse(model):
    module = ast.parse(model)
    for stm in module.body:
        if isinstance(stm, ast.ClassDef):
            stm.name = stm.name + "Modified"

    return black.format_file_contents(
        astor.to_source(module), fast=True, mode=black.FileMode()
    )


def main(modelfile):
    with open(modelfile) as f:
        print(parse(f.read()))


if __name__ == "__main__":
    import sys

    main(*sys.argv[1:])
