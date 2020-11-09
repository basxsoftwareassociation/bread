import django_filters
from django import forms
from django.utils.translation import gettext as _

import plisplate

from .button import Button
from .notification import InlineNotification
from .select import Select
from .text_input import PasswordInput, TextInput

FORM_NAME_SCOPED = "__plispate_form__"


class Form(plisplate.FORM):
    @classmethod
    def from_fieldnames(cls, fieldnames, **kwargs):
        return Form.wrap_with_form(
            *[FormField(fieldname) for fieldname in fieldnames], **kwargs
        )

    @classmethod
    def wrap_with_form(cls, *elements, **kwargs):
        submit = Button(_("Submit"))
        submit.attributes["type"] = "submit"
        return Form(*elements, plisplate.DIV(submit, _class="bx--form-item"), **kwargs)

    def __init__(self, *children, formname="form", use_csrf=True, **attributes):
        self.formname = formname
        defaults = {"method": "POST", "autocomplete": "off"}
        defaults.update(attributes)
        if defaults["method"].upper() == "POST" and use_csrf is not False:
            children = (CsrfToken(),) + children
        super().__init__(*children, **defaults)

    def render(self, context):
        c = dict(context)
        form = c[self.formname]
        c[FORM_NAME_SCOPED] = form
        if form.non_field_errors():
            for error in form.non_field_errors():
                self.insert(0, InlineNotification(_("Form error"), error, kind="error"))
        for hidden in form.hidden_fields():
            for error in hidden.errors:
                self.insert(
                    0,
                    InlineNotification(
                        _("Form error: "), hidden.name, error, kind="error"
                    ),
                )
        if form.is_multipart() and "enctype" not in self.attributes:
            self.attributes["enctype"] = "multipart/form-data"
        return super().render(c)


class FormField(plisplate.BaseElement):
    """Dynamic element which will resolve the field with the given name
and return the correct HTML, based on the widget of the form field or on the passed argument 'fieldtype'"""

    def __init__(self, fieldname, fieldtype=None):
        self.fieldname = fieldname
        self.fieldtype = fieldtype

    def render(self, context):
        return _mapfield(
            context[FORM_NAME_SCOPED][self.fieldname], self.fieldtype
        ).render(context)

    def __repr__(self):
        return f"FormField({self.fieldname})"


class FormSetField(plisplate.Iterator):
    def __init__(self, fieldname, variablename, *children, **formset_kwargs):
        super().__init__(fieldname, FORM_NAME_SCOPED, *children)
        self.formset_kwargs = formset_kwargs

    def __repr__(self):
        return f"FormField({self.fieldname}, {self.formset_kwargs})"


class HiddenInput(plisplate.INPUT):
    def __init__(self, fieldname):
        self.fieldname = fieldname
        super().__init__(type="hidden")

    def render(self, context):
        boundfield = context[FORM_NAME_SCOPED][self.fieldname]
        self.attributes["required"] = False
        if boundfield is not None:
            self.attributes["name"] = boundfield.html_name
            if boundfield.value() is not None:
                self.attributes["value"] = boundfield.value()
        return super().render(context)


class CsrfToken(plisplate.INPUT):
    def __init__(self):
        super().__init__(type="hidden")

    def render(self, context):
        self.attributes["name"] = "csrfmiddlewaretoken"
        self.attributes["value"] = context["csrf_token"]
        return super().render(context)


def _mapfield(field, fieldtype):
    WIDGET_MAPPING = {
        forms.TextInput: TextInput,
        forms.NumberInput: TextInput,  # TODO
        forms.EmailInput: TextInput,  # TODO
        forms.URLInput: TextInput,  # TODO
        forms.PasswordInput: PasswordInput,
        forms.HiddenInput: HiddenInput,
        forms.DateInput: TextInput,  # TODO
        forms.DateTimeInput: TextInput,  # TODO
        forms.TimeInput: TextInput,  # TODO
        forms.Textarea: TextInput,  # TODO
        forms.CheckboxInput: TextInput,  # TODO
        forms.Select: Select,
        forms.NullBooleanSelect: TextInput,  # TODO
        forms.SelectMultiple: TextInput,  # TODO
        forms.RadioSelect: TextInput,  # TODO
        forms.CheckboxSelectMultiple: TextInput,  # TODO
        forms.FileInput: TextInput,  # TODO
        forms.ClearableFileInput: TextInput,  # TODO
        forms.MultipleHiddenInput: TextInput,  # TODO
        forms.SplitDateTimeWidget: TextInput,  # TODO
        forms.SplitHiddenDateTimeWidget: TextInput,  # TODO
        forms.SelectDateWidget: TextInput,  # TODO
        django_filters.widgets.DateRangeWidget: TextInput,  # TODO
    }
    if fieldtype:
        return fieldtype(fieldname=field.name, **field.field.widget.attrs)
    return WIDGET_MAPPING[type(field.field.widget)](
        fieldname=field.name, **field.field.widget.attrs
    )
