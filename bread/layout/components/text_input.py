import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .button import Button
from .helpers import ErrorListElement, HelpTextElement, LabelElement
from .icon import Icon


class TextInput(hg.DIV):
    def __init__(
        self,
        light=False,
        widgetattributes=None,
        label=None,
        help_text=None,
        errors=None,
        required=None,
        disabled=None,
        icon=None,
        **attributes,
    ):
        # Pop these attributes because "attributes" should be passed
        # as HTML attributes to the parent __init__ and they do not render
        # properly sometimes (e.g. boundfield will render the fields HTML
        # inside the attribute
        # TODO: Define and implement a better interface for components which can
        # be instantiated in bread.layout.component._mapwidget
        # See https://github.com/basxsoftwareassociation/bread/issues/16
        attributes.pop("boundfield")
        attributes.pop("fieldname")
        attributes["_class"] = (
            attributes.get("_class", "") + " bx--text-input-wrapper bx--form-item"
        )
        widgetattributes = widgetattributes or {}
        widgetattributes["_class"] = hg.BaseElement(
            widgetattributes.get("_class", ""),
            " bx--text-input",
            hg.If(light, " bx--text-input--light"),
            hg.If(errors, " bx--text-input--invalid"),
        )

        super().__init__(
            LabelElement(
                label,
                widgetattributes.get("id"),
                required=required,
                disabled=disabled,
            ),
            hg.DIV(
                hg.If(
                    errors,
                    Icon(
                        "warning--filled",
                        size=16,
                        _class="bx--text-input__invalid-icon",
                    ),
                ),
                hg.INPUT(
                    type="text",
                    **widgetattributes,
                ),
                hg.If(
                    icon,
                    Icon(
                        icon,
                        size=16,
                        _class="text-input-icon",
                    ),
                ),
                _class=(
                    "bx--text-input__field-wrapper"
                    + (" text-input-with-icon" if icon is not None else "")
                ),
                data_invalid=hg.If(errors, True),
            ),
            HelpTextElement(
                help_text, disabled=widgetattributes.get("disabled", False)
            ),
            ErrorListElement(errors),
            **attributes,
        )


class PasswordInput(TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attributes["data-text-input"] = True
        self.attributes["_class"] += " bx--password-input-wrapper"
        inputElement = self[1][1]
        inputElement.attributes["type"] = "password"
        inputElement.attributes["data-toggle-password-visibility"] = True
        inputElement.attributes["_class"] += " bx--password-input"
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
