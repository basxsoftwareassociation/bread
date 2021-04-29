import htmlgenerator
from django.utils.translation import gettext_lazy as _

from .icon import Icon


class Button(htmlgenerator.BUTTON):
    """buttontype: "primary", "secondary", "tertiary", "danger", "ghost" """

    def __init__(
        self,
        *children,
        buttontype="primary",
        icon=None,
        notext=False,
        small=False,
        islink=False,
        **attributes,
    ):
        if islink:
            self.tag = "a"
        attributes["type"] = attributes.get("type", "button")
        attributes["tabindex"] = attributes.get("tabindex", "0")
        attributes["_class"] = (
            attributes.get("_class", "") + f" bx--btn bx--btn--{buttontype}"
        )
        if small:
            attributes["_class"] += " bx--btn--sm "
        if notext or not children:
            attributes["_class"] += " bx--btn--icon-only"
            if children:
                attributes[
                    "_class"
                ] += " bx--btn--icon-only bx--tooltip__trigger bx--tooltip--a11y bx--tooltip--bottom bx--tooltip--align-center"
                children = (htmlgenerator.SPAN(*children, _class="bx--assistive-text"),)

        if icon is not None:
            if isinstance(icon, str):
                icon = Icon(icon)
            icon.attributes["_class"] = (
                icon.attributes.get("_class", "") + " bx--btn__icon"
            )
            children += (icon,)
        super().__init__(*children, **attributes)

    @staticmethod
    def fromaction(action, **kwargs):
        buttonargs = {
            "icon": action.icon,
            "notext": not action.label,
            "onclick": action.js,
        }
        buttonargs.update(kwargs)
        return Button(*([action.label] if action.label else []), **buttonargs)


class ButtonSet(htmlgenerator.htmltags.DIV):
    def __init__(self, *buttons, **attributes):
        attributes["_class"] = attributes.get("_class", "") + " bx--btn-set"
        super().__init__(*buttons, **attributes)


class PrintPageButton(Button):
    def __init__(self, **attributes):
        if "onclick" not in attributes:
            attributes["onclick"] = "window.print()"
        super().__init__(_("Print"), icon="printer", notext=True, **attributes)
