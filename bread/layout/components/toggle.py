import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .helpers import REQUIRED_LABEL, ErrorListElement, HelpTextElement


class Toggle(hg.DIV):
    def __init__(
        self,
        label,
        offlabel=_("Off"),
        onlabel=_("On"),
        help_text=None,
        errors=None,
        disabled=None,
        required=None,
        widgetattributes={},
        **attributes,
    ):
        attributes["_class"] = attributes.get("_class", "") + " bx--form-item"
        widgetattributes["_class"] = (
            widgetattributes.get("_class", "") + " bx--toggle-input"
        )
        widgetattributes["type"] = "checkbox"
        widgetattributes["id"] = widgetattributes.get("id", None) or hg.html_id(self)
        self.input = hg.INPUT(**widgetattributes)
        self.label = hg.LABEL(
            label,
            hg.If(required, REQUIRED_LABEL),
            hg.SPAN(
                hg.SPAN(offlabel, _class="bx--toggle__text--off", aria_hidden="true"),
                hg.SPAN(onlabel, _class="bx--toggle__text--on", aria_hidden="true"),
                _class="bx--toggle__switch",
            ),
            _class=hg.BaseElement(
                "bx--label bx--toggle-input__label",
                hg.If(disabled, " bx--label--disabled"),
            ),
            _for=widgetattributes["id"],
        )
        super().__init__(
            self.input,
            self.label,
            HelpTextElement(help_text),
            ErrorListElement(errors),
            **attributes,
        )
