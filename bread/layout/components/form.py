import htmlgenerator as hg
from django import forms
from django.utils.html import mark_safe
from django.utils.translation import gettext as _

from .button import Button
from .email_input import EmailInput
from .notification import InlineNotification
from .phone_number_input import PhoneNumberInput
from .url_input import UrlInput


class Form(hg.FORM):
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
                hg.DIV(
                    Button(submit_label or _("Save"), type="submit"),
                    _class="bx--form-item",
                    style="margin-top: 2rem",
                ),
            )
        return Form(form, *elements, **kwargs)

    def __init__(self, form, *children, use_csrf=True, standalone=True, **attributes):
        """
        form: lazy evaluated value which should resolve to the form object
        children: any child elements, can be formfields or other
        use_csrf: add a CSRF input, but only for POST submission and standalone forms
        standalone: if true, will add a CSRF token and will render enclosing FORM-element
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
        form = hg.resolve_lazy(self.form, context, self)
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


class FormField(FormChild, hg.BaseElement):
    """Dynamic element which will resolve the field with the given name
    and return the correct HTML, based on the widget of the form field or on the passed argument 'fieldtype'"""

    def __init__(
        self,
        fieldname,
        fieldtype=None,
        hidelabel=False,
        elementattributes=None,
        widgetattributes=None,
    ):
        self.fieldname = fieldname
        self.fieldtype = fieldtype
        self.widgetattributes = widgetattributes or {}
        self.elementattributes = elementattributes or {}
        self.form = None  # will be set by the render method of the parent method
        self.hidelabel = hidelabel

    def render(self, context):
        element = _mapwidget(
            self.form[self.fieldname],
            self.fieldtype,
            self.elementattributes,
            self.widgetattributes,
        )
        if self.hidelabel:
            element._replace(
                lambda e, ancestors: isinstance(e, hg.LABEL), None, all=True
            )
        return element.render(context)

    def __repr__(self):
        return f"FormField({self.fieldname})"


class FormsetField(FormChild, hg.BaseElement):
    def __init__(
        self,
        fieldname,
        *children,
        containertag=hg.DIV,
        formsetinitial=None,
        **formsetfactory_kwargs,
    ):
        super().__init__(*children)
        self.fieldname = fieldname
        self.formsetfactory_kwargs = formsetfactory_kwargs
        self.formsetinitial = formsetinitial
        self.containertag = containertag

    def render(self, context):
        formset = self.form[self.fieldname].formset
        # Detect internal fields like the delete-checkbox, the order-widget, id fields, etc and add their
        # HTML representations. But we never show the "delete" checkbox, it should be manually added via InlineDeleteButton
        declared_fields = [
            f.fieldname
            for f in self.filter(lambda e, ancestors: isinstance(e, FormField))
        ]
        internal_fields = [
            field
            for field in formset.empty_form.fields
            if field not in declared_fields
            and field != forms.formsets.DELETION_FIELD_NAME
        ]

        for field in internal_fields:
            self.append(FormField(field))

        skeleton = hg.DIV(
            Form.from_django_form(formset.management_form, standalone=False),
            self.containertag(
                hg.Iterator(
                    formset,
                    loopvariable="formset_form",
                    content=Form(hg.C("formset_form"), *self, standalone=False),
                ),
                id=f"formset_{formset.prefix}_container",
            ),
            hg.DIV(
                Form(formset.empty_form, *self, standalone=False),
                id=f"empty_{ formset.prefix }_form",
                _class="template-form",
                style="display:none;",
            ),
            hg.SCRIPT(
                mark_safe(
                    f"""document.addEventListener("DOMContentLoaded", e => init_formset("{ formset.prefix }"));"""
                )
            ),
        )
        yield from skeleton.render(context)

    def __repr__(self):
        return f"Formset({self.fieldname}, {self.formsetfactory_kwargs})"


class FormsetAddButton(FormChild, Button):
    def __init__(self, fieldname, label=_("Add"), **kwargs):
        defaults = {
            "icon": "add",
            "notext": True,
            "buttontype": "tertiary",
        }
        defaults.update(kwargs)
        self.fieldname = fieldname
        super().__init__(label, **defaults)

    def render(self, context):
        formset = self.form[self.fieldname].formset
        self.attributes["id"] = f"add_{formset.prefix}_button"
        self.attributes[
            "onclick"
        ] = f"formset_add('{ formset.prefix }', '#formset_{ formset.prefix }_container');"
        return super().render(context)


class InlineDeleteButton(FormChild, Button):
    def __init__(self, parentcontainerselector, label=_("Delete"), **kwargs):
        """
        Show a delete button for the current inline form. This element needs to be inside a FormsetField
        parentcontainerselector: CSS-selector which will be passed to element.closest in order to select the parent container which should be hidden on delete
        """
        defaults = {
            "notext": True,
            "small": True,
            "icon": "trash-can",
            "buttontype": "ghost",
            "onclick": f"delete_inline_element(this.querySelector('input[type=checkbox]'), this.closest('{parentcontainerselector}'))",
        }
        defaults.update(kwargs)
        super().__init__(
            label,
            FormField(
                forms.formsets.DELETION_FIELD_NAME,
                elementattributes={"style": "display: none"},
            ),
            **defaults,
        )


class HiddenInput(FormChild, hg.INPUT):
    def __init__(self, fieldname, widgetattributes, boundfield=None, **attributes):
        self.fieldname = fieldname
        super().__init__(type="hidden", **{**widgetattributes, **attributes})

        self.attributes["id"] = boundfield.auto_id
        if boundfield is not None:
            self.attributes["name"] = boundfield.html_name
            if boundfield.value() is not None:
                self.attributes["value"] = boundfield.value()


class CsrfToken(FormChild, hg.INPUT):
    def __init__(self):
        super().__init__(type="hidden")

    def render(self, context):
        self.attributes["name"] = "csrfmiddlewaretoken"
        self.attributes["value"] = context["csrf_token"]
        return super().render(context)


def _mapwidget(
    field, fieldtype, elementattributes=None, widgetattributes=None, only_initial=False
):
    from .checkbox import Checkbox
    from .date_picker import DatePicker
    from .file_uploader import FileUploader
    from .multiselect import MultiSelect
    from .select import Select
    from .text_area import TextArea
    from .text_input import PasswordInput, TextInput

    WIDGET_MAPPING = {
        forms.TextInput: TextInput,
        # Attention: NumberInput is not the widget that is used for phone numbers. See below for handling of phone numbers
        forms.NumberInput: TextInput,
        forms.EmailInput: EmailInput,
        forms.URLInput: UrlInput,
        forms.PasswordInput: PasswordInput,
        forms.HiddenInput: HiddenInput,
        forms.DateInput: DatePicker,
        forms.DateTimeInput: TextInput,  # TODO
        forms.TimeInput: TextInput,  # TODO HIGH
        forms.Textarea: TextArea,
        forms.CheckboxInput: Checkbox,
        forms.NullBooleanSelect: Select,
        forms.SelectMultiple: MultiSelect,  # TODO HIGH
        forms.RadioSelect: TextInput,  # TODO HIGH
        forms.FileInput: FileUploader,
        forms.ClearableFileInput: FileUploader,  # TODO HIGH
        forms.MultipleHiddenInput: TextInput,  # TODO
        forms.SplitDateTimeWidget: TextInput,  # TODO
        forms.SplitHiddenDateTimeWidget: TextInput,  # TODO
        forms.SelectDateWidget: TextInput,  # TODO
    }

    widgetattributes = update_widgetattributes(field, only_initial, widgetattributes)
    elementattributes = {
        "label": field.label,
        "help_text": field.help_text,
        "errors": field.errors,
        "disabled": field.field.disabled,
        "required": field.field.required,
        **getattr(field.field, "layout_kwargs", {}),
        **(elementattributes or {}),
    }

    if isinstance(field.field.widget, forms.CheckboxInput):
        widgetattributes["checked"] = field.value()
        return hg.DIV(
            Checkbox(
                widgetattributes=widgetattributes,
                **elementattributes,
            ),
            _class="bx--form-item",
        )

    if isinstance(field.field.widget, forms.CheckboxSelectMultiple):
        del elementattributes["required"]

        return hg.DIV(
            *[
                Checkbox(
                    **elementattributes,
                    label=widget.data["label"],
                    widgetattributes={
                        **widgetattributes,
                        "name": widget.data["name"],
                        "value": widget.data["value"],
                        "checked": widget.data["selected"],
                        **widget.data["attrs"],
                    },
                )
                for widget in field.subwidgets
            ],
            _class="bx--form-item",
        )

    if isinstance(field.field.widget, forms.Select):
        if isinstance(field.field.widget, forms.SelectMultiple):
            return hg.DIV(
                MultiSelect(
                    field.field.widget.optgroups(
                        field.name,
                        field.field.widget.get_context(field.name, field.value(), {})[
                            "widget"
                        ]["value"],
                    ),
                    widgetattributes=widgetattributes,
                    **elementattributes,
                ),
                _class="bx--form-item",
            )
        return hg.DIV(
            Select(
                field.field.widget.optgroups(
                    field.name,
                    field.field.widget.get_context(field.name, field.value(), {})[
                        "widget"
                    ]["value"],
                ),
                widgetattributes=widgetattributes,
                **elementattributes,
            ),
            _class="bx--form-item",
        )

    fieldtype = (
        fieldtype
        or getattr(field.field, "layout", None)
        # needs to be above the WIDGET_MAPPING, because the field.field.widget is a forms.TextInput which would match
        or (
            PhoneNumberInput
            if hasattr(field.field.widget, "input_type")
            and field.field.widget.input_type == "tel"
            else None
        )
        or WIDGET_MAPPING[type(field.field.widget)]
    )
    if isinstance(fieldtype, type) and issubclass(fieldtype, hg.BaseElement):
        ret = fieldtype(
            fieldname=field.name,
            widgetattributes=widgetattributes,
            boundfield=field,
            **elementattributes,
        )
    else:
        ret = hg.DIV(f"Field {field.name}")

    if (
        field.field.show_hidden_initial and fieldtype != HiddenInput
    ):  # special case, prevent infinte recursion
        return hg.BaseElement(
            ret,
            _mapwidget(field, HiddenInput, only_initial=True),
        )

    return ret


def update_widgetattributes(field, only_initial, widgetattributes):
    # TODO: This can be simplified, and improved
    widgetattributes = widgetattributes or {}
    attrs = dict(field.field.widget.attrs)
    attrs.update(widgetattributes)
    attrs = field.build_widget_attrs(attrs)
    if getattr(field.field.widget, "allow_multiple_selected", False):
        attrs["multiple"] = True
    if field.auto_id and "id" not in field.field.widget.attrs:
        attrs.setdefault("id", field.html_initial_id if only_initial else field.auto_id)
    if "name" not in attrs:
        attrs["name"] = field.html_initial_name if only_initial else field.html_name
    value = field.field.widget.format_value(field.value())
    if value is not None and "value" not in attrs:
        attrs["value"] = value
    return attrs
