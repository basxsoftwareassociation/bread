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
        button = Button(
            *([link.label] if link.label else []),
            **{**buttonargs, **link.attributes, **kwargs},
        )
        if link.is_submit:
            return button.as_submit(
                link.href, formfields=link.formfields, confirm_text=link.confirm_text
            )
        else:
            return button.as_href(link.href)

    def as_href(self, href):
        return hg.A(*self, **{**self.attributes, "href": href})

    def as_submit(self, href, formfields={}, confirm_text=None, **kwargs):
        from django.forms import Form as DjangoForm

        from ..utils import slugify
        from .forms import Form
        from .modal import Modal

        confirm_dialog = Modal(
            _("Please confirm"),
            _("Are you sure?") if confirm_text is None else confirm_text,
            buttons=(
                Button(_("No..."), buttontype="ghost", data_modal_close=True),
                Button(_("Yes!"), type="submit"),
            ),
            id=hg.format("modal-{}", slugify(href)),
            size="xs",
        )

        newbutton = self.copy()
        newbutton.attributes = hg.merge_html_attrs(
            newbutton.attributes,
            {
                **confirm_dialog.openerattributes,
                **{"onclick": "event.preventDefault(); return false;"},
            },
        )
        return Form(
            DjangoForm(),
            newbutton,
            *[
                hg.INPUT(type="hidden", name=name, value=value)
                for name, value in formfields.items()
            ],
            confirm_dialog,
            action=href,
            **hg.merge_html_attrs(kwargs, {"style": "display: inline"}),
        )


class ButtonSet(hg.DIV):
    def __init__(self, *buttons, **attributes):
        attributes["_class"] = attributes.get("_class", "") + " bx--btn-set"
        super().__init__(*buttons, **attributes)


class PrintPageButton(Button):
    def __init__(self, **attributes):
        if "onclick" not in attributes:
            attributes["onclick"] = "window.print()"
        super().__init__(_("Print"), icon="printer", notext=True, **attributes)
