import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .icon import Icon


class Button(hg.BUTTON):
    """buttontype: "primary", "secondary", "tertiary", "danger", "ghost" """

    def __init__(
        self,
        *children,
        buttontype="primary",
        icon=None,
        notext=False,
        small=False,
        **attributes,
    ):
        attributes["type"] = attributes.get("type", "button")
        attributes["tabindex"] = attributes.get("tabindex", "0")
        attributes["_class"] = hg.BaseElement(
            attributes.get("_class", ""),
            f" bx--btn bx--btn--{buttontype}",
            hg.If(
                hg.F(
                    lambda c: hg.resolve_lazy(self.attributes.get("disabled", False), c)
                ),
                " bx--btn--disabled",
            ),
        )
        if small:
            attributes["_class"] += " bx--btn--sm "
        if notext or not children:
            attributes["_class"] += " bx--btn--icon-only"
            if children:
                attributes["_class"] += (
                    " bx--btn--icon-only bx--tooltip__trigger bx--tooltip--a11y "
                    "bx--tooltip--bottom bx--tooltip--align-center"
                )
                children = (hg.SPAN(*children, _class="bx--assistive-text"),)

        if icon is not None:
            if isinstance(icon, str):
                icon = Icon(icon)
            if isinstance(icon, Icon):
                icon.attributes["_class"] = (
                    icon.attributes.get("_class", "") + " bx--btn__icon"
                )
            children += (icon,)
        super().__init__(*children, **attributes)

    @staticmethod
    def from_link(link, **kwargs):
        buttonargs = {
            "icon": link.iconname,
            "notext": not link.label,
            "disabled": hg.F(lambda c: not link.has_permission(c["request"])),
        }
        return Button(
            *([link.label] if link.label else []),
            **{**buttonargs, **link.attributes, **kwargs},
        ).as_href(link.href)

    def as_href(self, href):
        return hg.A(*self, **{**self.attributes, "href": href})


class ButtonSet(hg.DIV):
    def __init__(self, *buttons, **attributes):
        attributes["_class"] = attributes.get("_class", "") + " bx--btn-set"
        super().__init__(*buttons, **attributes)


class PrintPageButton(Button):
    def __init__(self, **attributes):
        if "onclick" not in attributes:
            attributes["onclick"] = "window.print()"
        super().__init__(_("Print"), icon="printer", notext=True, **attributes)
