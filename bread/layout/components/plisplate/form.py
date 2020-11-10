import django_filters
from django import forms
from django.utils.translation import gettext as _
from django_countries.widgets import LazySelect

import plisplate

from .button import Button
from .notification import InlineNotification

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

    def __init__(
        self, fieldname, fieldtype=None, elementattributes={}, widgetattributes={}
    ):
        self.fieldname = fieldname
        self.fieldtype = fieldtype
        self.widgetattributes = widgetattributes
        self.elementattributes = elementattributes

    def render(self, context):
        return _mapwidget(
            context[FORM_NAME_SCOPED][self.fieldname],
            self.fieldtype,
            self.elementattributes,
            self.widgetattributes,
        ).render(context)

    def __repr__(self):
        return f"FormField({self.fieldname})"


class FormSetField(plisplate.Iterator):
    def __init__(self, fieldname, *children, **formset_kwargs):
        super().__init__(
            lambda context: self.get_formset(context), FORM_NAME_SCOPED, *children,
        )
        self.fieldname = fieldname
        self.formset_kwargs = formset_kwargs

    def get_formset(self, context):
        value = context[FORM_NAME_SCOPED][self.fieldname].value() or {}
        value.update(self.formset_kwargs)
        return context[FORM_NAME_SCOPED][self.fieldname].field.formsetclass(**value)

    def render(self, context):
        formset = self.get_formset(context)
        localcontext = dict(context)

        # management form
        localcontext[FORM_NAME_SCOPED] = formset.management_form
        for field in formset.management_form:
            yield from FormField(field.name).render(localcontext)

        # forms, correct form-value for each form item will be set by super().render
        # wrapping things is a bit unfortunate but the quickest way to do it now
        declared_fields = [
            f.fieldname for f in self.filter(lambda e: isinstance(e, FormField))
        ]
        internal_fields = [
            field for field in formset.empty_form.fields if field not in declared_fields
        ]
        for field in internal_fields:
            self.append(FormField(field))

        yield f'<div id="formset_{formset.prefix}_container">'
        for form in formset:
            localcontext[FORM_NAME_SCOPED] = form
            yield from super().render_children(localcontext)
        yield "</div>"

        # empty/template form
        localcontext[FORM_NAME_SCOPED] = formset.empty_form
        yield from plisplate.DIV(
            plisplate.DIV(*[e for e in self]),
            id=f"empty_{ formset.prefix }_form",
            _class="template-form",
            style="display:none;",
        ).render(localcontext)

        # add-new-form button
        yield from plisplate.DIV(
            Button(
                _("Add"),
                id=f"add_{formset.prefix}_button",
                onclick=f"formset_add('{ formset.prefix }', '#formset_{ formset.prefix }_container');",
                icon="add",
                notext=True,
                small=True,
            ),
            _class="bx--form-item",
        ).render(localcontext)
        yield from plisplate.SCRIPT(
            f"""document.addEventListener("DOMContentLoaded", e => init_formset("{ formset.prefix }"));"""
        ).render(localcontext)

    def __repr__(self):
        return f"FormSet({self.fieldname}, {self.formset_kwargs})"


class HiddenInput(plisplate.INPUT):
    def __init__(self, fieldname, widgetattributes, **attributes):
        self.fieldname = fieldname
        super().__init__(type="hidden", **{**widgetattributes, **attributes})

    def render(self, context):
        boundfield = context[FORM_NAME_SCOPED][self.fieldname]
        self.attributes["id"] = boundfield.auto_id
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


def _mapwidget(
    field, fieldtype, elementattributes={}, widgetattributes={}, only_initial=False
):
    from .select import Select
    from .text_input import PasswordInput, TextInput
    from .date_picker import DatePicker
    from .text_area import TextArea
    from .checkbox import Checkbox

    WIDGET_MAPPING = {
        forms.TextInput: TextInput,
        forms.NumberInput: TextInput,  # TODO HIGH
        forms.EmailInput: TextInput,  # TODO
        forms.URLInput: TextInput,  # TODO
        forms.PasswordInput: PasswordInput,
        forms.HiddenInput: HiddenInput,
        forms.DateInput: DatePicker,
        forms.DateTimeInput: TextInput,  # TODO
        forms.TimeInput: TextInput,  # TODO HIGH
        forms.Textarea: TextArea,
        forms.CheckboxInput: Checkbox,
        forms.Select: Select,
        forms.NullBooleanSelect: Select,
        forms.SelectMultiple: TextInput,  # TODO HIGH
        forms.RadioSelect: TextInput,  # TODO HIGH
        forms.CheckboxSelectMultiple: TextInput,  # TODO HIGH
        forms.FileInput: TextInput,  # TODO HIGH
        forms.ClearableFileInput: TextInput,  # TODO HIGH
        forms.MultipleHiddenInput: TextInput,  # TODO
        forms.SplitDateTimeWidget: TextInput,  # TODO
        forms.SplitHiddenDateTimeWidget: TextInput,  # TODO
        forms.SelectDateWidget: TextInput,  # TODO
        # 3rd party widgets
        django_filters.widgets.DateRangeWidget: TextInput,  # TODO
        LazySelect: Select,
    }

    if field.field.localize:
        field.field.widget.is_localized = True
    widgetattributes = field.build_widget_attrs(widgetattributes, field.field.widget)
    if field.auto_id and "id" not in field.field.widget.attrs:
        widgetattributes.setdefault(
            "id", field.html_initial_id if only_initial else field.auto_id
        )
    widgetattributes["name"] = (
        field.html_initial_name if only_initial else field.html_name
    )
    value = field.field.widget.format_value(field.value())
    if value is not None:
        widgetattributes["value"] = value

    if fieldtype is None:
        fieldtype = WIDGET_MAPPING[type(field.field.widget)]
    if (
        field.field.show_hidden_initial and fieldtype != HiddenInput
    ):  # prevent infinte recursion
        return plisplate.BaseElement(
            fieldtype(
                fieldname=field.name,
                widgetattributes=widgetattributes,
                **elementattributes,
            ),
            _mapwidget(field, HiddenInput, only_initial=True),
        )

    return fieldtype(
        fieldname=field.name, widgetattributes=widgetattributes, **elementattributes
    )


class ErrorList(plisplate.DIV):
    def __init__(self, errors):
        super().__init__(
            plisplate.UL(*[plisplate.LI(e) for e in errors]),
            _class="bx--form-requirement",
        )


class HelperText(plisplate.DIV):
    def __init__(self, helpertext):
        super().__init__(helpertext, _class="bx--form__helper-text")
