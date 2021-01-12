import django_filters
import htmlgenerator
from django import forms
from django.utils.html import mark_safe
from django.utils.translation import gettext as _
from django_countries.widgets import LazySelect

from .button import Button
from .icon import Icon
from .notification import InlineNotification


class Form(htmlgenerator.FORM):
    @staticmethod
    def from_django_form(form, **kwargs):
        return Form.from_fieldnames(form, form.fields, **kwargs)

    @staticmethod
    def from_fieldnames(form, fieldnames, **kwargs):
        return Form.wrap_with_form(
            form, *[FormField(fieldname) for fieldname in fieldnames], **kwargs
        )

    @staticmethod
    def wrap_with_form(form, *elements, submit_label=None, **kwargs):
        if kwargs.get("standalone", True) is True:
            elements += (
                htmlgenerator.DIV(
                    Button(submit_label or _("Save"), type="submit"),
                    _class="bx--form-item",
                ),
            )
        return Form(form, *elements, **kwargs)

    def __init__(self, form, *children, use_csrf=True, standalone=True, **attributes):
        """
        form: lazy evaluated value which should resolve to the form object
        children: any child elements, can be formfields or other
        use_csrf: add a CSRF input, but only for POST submission and standalone forms
        standalone: if false, will not add CSRF token and will not render enclosing form-tag
        """
        self.form = form
        self.standalone = standalone
        defaults = {"method": "POST", "autocomplete": "off"}
        defaults.update(attributes)
        if (
            defaults["method"].upper() == "POST"
            and use_csrf is not False
            and standalone is True
        ):
            children = (CsrfToken(),) + children
        super().__init__(*children, **defaults)

    def formfieldelements(self):
        return self.filter(
            lambda elem, parents: isinstance(elem, FormChild)
            and not any((isinstance(p, Form) for p in parents[1:]))
        )

    def render(self, context):
        form = htmlgenerator.resolve_lazy(self.form, context, self)
        for formfield in self.formfieldelements():
            formfield.form = form
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
        if self.standalone:
            if form.is_multipart() and "enctype" not in self.attributes:
                self.attributes["enctype"] = "multipart/form-data"
            return super().render(context)
        return super().render_children(context)


class FormChild:
    """Used to mark elements which need the "form" attribute set by the parent form before rendering"""


class FormField(FormChild, htmlgenerator.BaseElement):
    """Dynamic element which will resolve the field with the given name
    and return the correct HTML, based on the widget of the form field or on the passed argument 'fieldtype'"""

    def __init__(
        self, fieldname, fieldtype=None, elementattributes={}, widgetattributes={}
    ):
        self.fieldname = fieldname
        self.fieldtype = fieldtype
        self.widgetattributes = widgetattributes
        self.elementattributes = elementattributes
        self.form = None  # will be set by the render method of the parent method

    def render(self, context):
        return _mapwidget(
            self.form[self.fieldname],
            self.fieldtype,
            self.elementattributes,
            self.widgetattributes,
        ).render(context)

    def __repr__(self):
        return f"FormField({self.fieldname})"


class FormSetField(FormChild, htmlgenerator.BaseElement):
    def __init__(
        self, fieldname, *children, formsetinitial=None, **formsetfactory_kwargs
    ):
        super().__init__(*children)
        self.fieldname = fieldname
        self.formsetfactory_kwargs = formsetfactory_kwargs
        self.formsetinitial = formsetinitial

    def render(self, context):
        formset = self.form[self.fieldname].formset

        # management form
        yield from Form.from_django_form(
            formset.management_form, standalone=False
        ).render(context)

        # detect internal fields like the delete-checkbox or the order-widget etc. and add them
        declared_fields = [
            f.fieldname
            for f in self.filter(lambda e, ancestors: isinstance(e, FormField))
        ]
        internal_fields = [
            field for field in formset.empty_form.fields if field not in declared_fields
        ]
        for field in internal_fields:
            self.append(FormField(field))

        # wrapping things with the div is a bit ugly but the quickest way to do it now
        yield f'<div id="formset_{formset.prefix}_container">'
        for form in formset:
            yield from Form.wrap_with_form(form, *self, standalone=False).render(
                context
            )
        yield "</div>"

        # empty/template form
        yield from htmlgenerator.DIV(
            htmlgenerator.DIV(
                Form.wrap_with_form(formset.empty_form, *self, standalone=False)
            ),
            id=f"empty_{ formset.prefix }_form",
            _class="template-form",
            style="display:none;",
        ).render(context)

        # add-new-form button
        yield from htmlgenerator.DIV(
            Button(
                _("Add"),
                id=f"add_{formset.prefix}_button",
                onclick=f"formset_add('{ formset.prefix }', '#formset_{ formset.prefix }_container');",
                icon=Icon("add"),
                notext=True,
                small=True,
            ),
            _class="bx--form-item",
        ).render(context)
        yield from htmlgenerator.SCRIPT(
            mark_safe(
                f"""document.addEventListener("DOMContentLoaded", e => init_formset("{ formset.prefix }"));"""
            )
        ).render(context)

    def __repr__(self):
        return f"FormSet({self.fieldname}, {self.formsetfactory_kwargs})"


class HiddenInput(FormChild, htmlgenerator.INPUT):
    def __init__(self, fieldname, widgetattributes, **attributes):
        self.fieldname = fieldname
        super().__init__(type="hidden", **{**widgetattributes, **attributes})

    def render(self, context):
        self.attributes["id"] = self.boundfield.auto_id
        if self.boundfield is not None:
            self.attributes["name"] = self.boundfield.html_name
            if self.boundfield.value() is not None:
                self.attributes["value"] = self.boundfield.value()
        return super().render(context)


class CsrfToken(FormChild, htmlgenerator.INPUT):
    def __init__(self):
        super().__init__(type="hidden")

    def render(self, context):
        self.attributes["name"] = "csrfmiddlewaretoken"
        self.attributes["value"] = context["csrf_token"]
        return super().render(context)


def _mapwidget(
    field, fieldtype, elementattributes={}, widgetattributes={}, only_initial=False
):
    from .checkbox import Checkbox
    from .date_picker import DatePicker
    from .select import Select
    from .text_area import TextArea
    from .text_input import PasswordInput, TextInput

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

    # TODO: This can be simplified, and improved
    if field.field.localize:
        field.field.widget.is_localized = True
    attrs = dict(field.field.widget.attrs)
    attrs.update(widgetattributes)
    attrs = field.build_widget_attrs(attrs)
    if field.auto_id and "id" not in field.field.widget.attrs:
        attrs.setdefault("id", field.html_initial_id if only_initial else field.auto_id)
    if "name" not in attrs:
        attrs["name"] = field.html_initial_name if only_initial else field.html_name
    value = field.field.widget.format_value(field.value())
    if value is not None and "value" not in attrs:
        attrs["value"] = value

    if fieldtype is None:
        fieldtype = WIDGET_MAPPING[type(field.field.widget)]

    ret = fieldtype(fieldname=field.name, widgetattributes=attrs, **elementattributes)
    ret.boundfield = field

    if (
        field.field.show_hidden_initial and fieldtype != HiddenInput
    ):  # special case, prevent infinte recursion
        return htmlgenerator.BaseElement(
            ret,
            _mapwidget(field, HiddenInput, only_initial=True),
        )

    return ret


class SubmitButton(htmlgenerator.DIV):
    def __init__(self, *args, **kwargs):
        kwargs["type"] = "submit"
        super().__init__(Button(*args, **kwargs), _class="bx--form-item")


class ErrorList(htmlgenerator.DIV):
    def __init__(self, errors):
        super().__init__(
            htmlgenerator.UL(*[htmlgenerator.LI(e) for e in errors]),
            _class="bx--form-requirement",
        )


class HelperText(htmlgenerator.DIV):
    def __init__(self, helpertext):
        super().__init__(helpertext, _class="bx--form__helper-text")
