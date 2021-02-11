import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .button import Button
from .helpers import (
    REQUIRED_LABEL,
    ErrorList,
    ErrorListElement,
    HelperText,
    HelpTextElement,
    Label,
    LabelElement,
)
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
            Label(),
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
                self.label.append(REQUIRED_LABEL)
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


# TEST IMPLEMENTATION ACCORDING TO helpers.py TODO comment, not currently used
# The nice thing here is that we do not need to overwrite the render method
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

        id = (id or hg.html_id(self),)

        super().__init__(
            hg.DIV(
                LabelElement(
                    label,
                    id,
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
                    id=id,
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
            _class="bx--text-input-wrapper",
        )

    @classmethod
    def from_formfieldcontext(
        cls, fieldcontext, light=False, widgetattributes=None, **attributes
    ):
        # TODO: this implementation still stems from the context/value provider implementation of
        # htmlgenerator, it should be changed to use context variables, e.g. hg.C
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
