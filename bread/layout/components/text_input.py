import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .button import Button
from .form import ErrorList, HelperText
from .icon import Icon


class TextInput(hg.DIV):
    def __init__(
        self,
        fieldname,
        light=False,
        widgetattributes={},
        **attributes,
    ):
        self.fieldname = fieldname
        attributes["_class"] = (
            attributes.get("_class", "") + " bx--form-item bx--text-input-wrapper"
        )
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "")
            + f" bx--text-input {'bx--text-input--light' if light else ''}"
        )

        super().__init__(
            hg.LABEL(_class="bx--label"),
            hg.DIV(
                hg.INPUT(**widgetattributes),
                _class="bx--text-input__field-wrapper",
            ),
            **attributes,
        )
        # for easier reference in the render method:
        self.label = self[0]
        self.input = self[1][0]

    def render(self, context):
        if self.boundfield.field.disabled:
            self.label.attributes["_class"] += " bx--label--disabled"
            self.input.attributes["disabled"] = True
        if self.boundfield is not None:
            self.label.attributes["_for"] = self.boundfield.id_for_label
            self.label.append(self.boundfield.label)
            if self.boundfield.field.required:
                self.label.append(_(" (required)"))
            if self.boundfield.help_text:
                self.append(HelperText(self.boundfield.help_text))
            if self.boundfield.errors:
                self[1].attributes["data-invalid"] = True
                self[1].append(
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--text-input__invalid-icon",
                    )
                )
                self.append(ErrorList(self.boundfield.errors))
        return super().render(context)


class PasswordInput(TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attributes["data-text-input"] = True
        self.attributes["_class"] += " bx--password-input-wrapper"
        self.input.attributes["type"] = "password"
        self.input.attributes["data-toggle-password-visibility"] = True
        self.input.attributes["_class"] += " bx--password-input"
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
        self[1].append(showhidebtn)


class TextInputElement(hg.DIV):
    def __init__(
        self,
        label=None,
        id=None,
        help_text=None,
        required=None,
        light=False,
        errors=None,
        widgetattributes=None,
        **attributes,
    ):
        widgetattributes = widgetattributes or {}
        widgetattributes["_class"] = hg.BaseElement(
            widgetattributes.get("_class", ""),
            "bx--text-input",
            hg.If(light, " bx--text-input--light"),
            hg.If(errors, " bx--text-input--invalid"),
        )

        super().__init__(
            hg.ValueProvider(
                id or hg.html_id(self),
                hg.DIV(
                    LabelElement(
                        label,
                        hg.ValueProvider.Binding()(hg.ATTR("value")),
                        required,
                        disabled=widgetattributes.get("disabled", False),
                    ),
                    hg.If(
                        errors,
                        Icon(
                            "warning--filled",
                            size=16,
                            _class="bx--text-input__invalid-icon",
                        ),
                    ),
                    hg.INPUT(
                        id=hg.ValueProvider.Binding()(hg.ATTR("value")),
                        type="text",
                        **widgetattributes,
                    ),
                    _class="bx--text-input__field-wrapper",
                    data_invalid=hg.If(errors, True),
                ),
                HelpTextElement(
                    help_text, disabled=widgetattributes.get("disabled", False)
                ),
                ErrorListElement(errors),
            ),
            _class="bx--text-input-wrapper",
        )

    @classmethod
    def from_formfieldcontext(
        cls, fieldcontext, light=False, widgetattributes=None, **attributes
    ):
        "fieldcontext: adds an attribute 'boundfield' to bound elements"
        return cls(
            label=fieldcontext.Binding(hg.ATTR("boundfield.label")),
            id=fieldcontext.Binding(hg.ATTR("boundfield.auto_id")),
            help_text=fieldcontext.Binding(hg.ATTR("boundfield.help_text")),
            required=fieldcontext.Binding(hg.ATTR("boundfield.field.required")),
            light=light,
            errors=fieldcontext.Binding(hg.ATTR("boundfield.errors")),
            widgetattributes=widgetattributes,
            **attributes,
        )


class LabelElement(hg.If):
    def __init__(self, label, _for, required, disabled=False):
        super().__init__(
            label,
            hg.LABEL(
                label,
                hg.If(required, _(" (required)")),
                _for=_for,
                _class=hg.BaseElement(
                    "bx--label",
                    hg.If(disabled, " bx--label--disabled"),
                ),
            ),
        )


class HelpTextElement(hg.If):
    def __init__(self, helptext, disabled=False):
        super().__init__(
            helptext,
            hg.DIV(
                helptext,
                _class=hg.BaseElement(
                    "bx--form__helper-text",
                    hg.If(disabled, " bx--form__helper-text--disabled"),
                ),
            ),
        )


class ErrorListElement(hg.If):
    def __init__(self, errors):
        super().__init__(
            errors,
            hg.DIV(
                hg.UL(
                    hg.Iterator(
                        errors or (), hg.ValueProvider.Binding(hg.LI)(hg.ATTR("value"))
                    )
                ),
                _class="bx--form-requirement",
            ),
        )
