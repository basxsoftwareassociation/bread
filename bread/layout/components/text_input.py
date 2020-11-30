import htmlgenerator
from django.utils.translation import gettext as _

from .button import Button
from .form import ErrorList, HelperText
from .icon import Icon


class TextInput(htmlgenerator.DIV):
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
            htmlgenerator.LABEL(_class="bx--label"),
            htmlgenerator.DIV(
                htmlgenerator.INPUT(**widgetattributes),
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
            if not self.boundfield.field.required:
                self.label.append(_(" (optional)"))
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
