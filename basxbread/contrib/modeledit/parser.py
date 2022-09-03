import ast

import astor
import black
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Field
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
        strip=True,
        validators=[validate_literal, valid_ordering],
    )


def fieldtypes():
    return {
        f"{fieldtype.__module__}.{fieldtype.__qualname__}": fieldtype
        for fieldtype in get_all_subclasses(Field)
    }


def typechoices():
    return tuple(fieldtypes().items())


def typecoerce(value):
    return fieldtypes().get(value, None)


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
    default = forms.CharField(
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


def serialize(ast_module):
    return black.format_file_contents(
        astor.to_source(ast_module), fast=True, mode=black.FileMode()
    )


def field_ast2formdata(astfieldnode):
    pass


def is_variable_assignment(statement, name):
    return (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and statement.targets[0].id == name
    )


def is_single_param_call(statement):
    return (
        isinstance(statement, ast.Call)
        and len(statement.args) == 1
        and isinstance(statement.args[0], ast.Constant)
    )


def model_ast2formdata(astclassnode):
    modelname = astclassnode.name.lower()
    data = {"name": astclassnode.name}
    for statement in astclassnode.body:
        if isinstance(statement, ast.ClassDef) and statement.name == "Meta":
            for substatement in statement.body:
                if is_variable_assignment(substatement, "verbose_name"):
                    if is_single_param_call(substatement.value):
                        data["verbose_name"] = substatement.value.args[0].value
                    else:
                        data["verbose_name"] = substatement.value.value
                elif is_variable_assignment(substatement, "verbose_name_plural"):
                    if is_single_param_call(substatement.value):
                        data["verbose_name_plural"] = substatement.value.args[0].value
                    else:
                        data["verbose_name_plural"] = substatement.value.value
                elif is_variable_assignment(substatement, "ordering"):
                    data["ordering"] = astor.to_source(substatement.value).strip()

    return modelname, data


def parse(modelfilecontent):
    ret = {}
    module = ast.parse(modelfilecontent)
    for statement in module.body:
        if isinstance(statement, ast.ClassDef):
            modelname, data = model_ast2formdata(statement)
            ret[modelname] = data
    return ret
