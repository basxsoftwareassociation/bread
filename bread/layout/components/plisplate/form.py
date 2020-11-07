from django import forms
from django.utils.translation import gettext as _

import plisplate

from .button import Button
from .icon import Icon
from .notification import InlineNotification

FORM_NAME_SCOPED = "__plispate_form__"


class Form(plisplate.FORM):
    @classmethod
    def from_django_form(cls, form):
        return Form(
            *[_mapfield(field) for field in form],
            plisplate.DIV(Button(_("Submit")), _class="bx--form-item"),
        )

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


def _mapfield(field):
    WIDGET_MAPPING = {
        forms.TextInput: TextInput,
        forms.NumberInput: TextInput,
        forms.EmailInput: TextInput,
        forms.URLInput: TextInput,
        forms.PasswordInput: PasswordInput,
        forms.HiddenInput: HiddenInput,
        forms.DateInput: TextInput,
        forms.DateTimeInput: TextInput,
        forms.TimeInput: TextInput,
        forms.Textarea: TextInput,
        forms.CheckboxInput: TextInput,
        forms.Select: TextInput,
        forms.NullBooleanSelect: TextInput,
        forms.SelectMultiple: TextInput,
        forms.RadioSelect: TextInput,
        forms.CheckboxSelectMultiple: TextInput,
        forms.FileInput: TextInput,
        forms.ClearableFileInput: TextInput,
    }
    return WIDGET_MAPPING[type(field.field.widget)](
        fieldname=field.name, **field.field.widget.attrs
    )


class HiddenInput(plisplate.INPUT):
    def __init__(self, fieldname):
        self.fieldname = fieldname
        super().__init__(type="hidden")

    def render(self, context):
        boundfield = context[FORM_NAME_SCOPED][self.fieldname]
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


class TextInput(plisplate.DIV):
    LABEL = 0
    INPUT = 1

    def __init__(
        self,
        fieldname,
        placeholder="",
        light=False,
        disabled_func=lambda c: False,
        **attributes,
    ):
        self.fieldname = fieldname
        self.disabled_func = disabled_func
        attributes["_class"] = (
            attributes.get("_class", "") + " bx--form-item  bx--text-input-wrapper"
        )
        super().__init__(
            plisplate.LABEL(_class="bx--label"),
            plisplate.DIV(
                plisplate.INPUT(
                    placeholder=placeholder,
                    _class=f"bx--text-input {'bx--text-input--light' if light else ''}",
                ),
                _class="bx--text-input__field-wrapper",
            ),
            **attributes,
        )

    def render(self, context):
        boundfield = context[FORM_NAME_SCOPED][self.fieldname]
        disabled = self.disabled_func(context)

        if disabled:
            self[TextInput.LABEL].attributes["_class"] += " bx--label--disabled"
            self[TextInput.INPUT][0].attributes["disabled"] = True
        if boundfield is not None:
            self[TextInput.LABEL].attributes["_for"] = boundfield.id_for_label
            self[TextInput.LABEL].append(boundfield.label)
            if not boundfield.field.required:
                self[TextInput.LABEL].append(_(" (optional)"))
            if boundfield.auto_id:
                self[TextInput.INPUT][0].attributes["id"] = boundfield.auto_id
            self[TextInput.INPUT][0].attributes["name"] = boundfield.html_name
            if boundfield.value() is not None:
                self[TextInput.INPUT][0].attributes["value"] = boundfield.value()
            if boundfield.help_text:
                self.append(
                    plisplate.DIV(boundfield.help_text, _class="bx--form__helper-text")
                )
            if boundfield.errors:
                self[TextInput.INPUT].append(
                    Icon("warning--filled", _class="bx--text-input__invalid-icon")
                )
                self.append(
                    plisplate.DIV(
                        plisplate.UL(*[plisplate.LI(e) for e in boundfield.errors]),
                        _class="bx--form-requirement",
                    )
                )
        return super().render(context)


class PasswordInput(TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attributes["data-text-input"] = True
        self.attributes["_class"] += " bx--password-input-wrapper"
        self[TextInput.INPUT][0].attributes["type"] = "password"
        self[TextInput.INPUT][0].attributes["data-toggle-password-visibility"] = True
        self[TextInput.INPUT][0].attributes["_class"] += " bx--password-input"
        showhidebtn = Button(_("Show password"), notext=True)
        showhidebtn.attributes[
            "_class"
        ] = "bx--text-input--password__visibility__toggle bx--tooltip__trigger bx--tooltip--a11y bx--tooltip--bottom bx--tooltip--align-center"
        showhidebtn.append(
            Icon(
                "view--off",
                _class="bx--icon--visibility-off",
                hidden="true",
                aria_hidden="true",
            )
        )
        showhidebtn.append(
            Icon("view", _class="bx--icon--visibility-on", aria_hidden="true")
        )
        self[TextInput.INPUT].append(showhidebtn)
