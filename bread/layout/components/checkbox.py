import htmlgenerator as hg

from .helpers import REQUIRED_LABEL, ErrorListElement, HelpTextElement


class Checkbox(hg.DIV):
    def __init__(
        self,
        label=None,
        help_text=None,
        errors=None,
        disabled=None,
        required=None,
        widgetattributes={},
        **attributes,
    ):
        attributes["_class"] = (
            attributes.get("_class", "") + " bx--form-item bx--checkbox-wrapper"
        )
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--checkbox"
        )
        widgetattributes["type"] = "checkbox"
        self.input = hg.INPUT(**widgetattributes)
        self.label = hg.LABEL(
            self.input,
            label,
            hg.If(required, REQUIRED_LABEL),
            _class=hg.BaseElement(
                "bx--checkbox-label",
                hg.If(disabled, " bx--label--disabled"),
            ),
            data_contained_checkbox_state="true"
            if widgetattributes.get("checked", False)
            else "false",
        )
        super().__init__(
            self.label,
            HelpTextElement(help_text),
            ErrorListElement(errors),
            **attributes,
        )
