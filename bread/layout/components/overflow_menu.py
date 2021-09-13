import htmlgenerator as hg

from .icon import Icon
from .modal import modal_with_generated_trigger


def overflow_button_wrapper(context):
    link = context["link"]
    if link.modal:
        # TODO Pascal Wiesmann: for some reason this does not work yet. the popup opens only after the overflow button
        # is clicked for the second time.
        return modal_with_generated_trigger(
            link.modal(), lambda attributes: overflow_button(link, **attributes)
        )
    else:
        return overflow_button(link)


def overflow_button(link, **kwargs):
    return hg.A(
        hg.DIV(
            hg.If(
                link.iconname,
                Icon(link.iconname, size=16),
            ),
            link.label,
            _class="bx--overflow-menu-options__option-content",
        ),
        _class="bx--overflow-menu-options__btn",
        role="menuitem",
        title=link.label,
        href=link.href,
        **link.attributes,
        **kwargs,
    )


class OverflowMenu(hg.DIV):
    """Implements https://www.carbondesignsystem.com/components/overflow-menu/usage"""

    MENUID_TEMPLATE = "overflow-menu-%s"

    def __init__(
        self,
        links,
        menuiconname="overflow-menu--vertical",
        menuname=None,
        direction="bottom",
        flip=False,
        item_attributes={},
        **attributes,
    ):
        attributes["data-overflow-menu"] = True
        attributes["_class"] = attributes.get("_class", "") + " bx--overflow-menu"
        item_attributes["_class"] = (
            item_attributes.get("_class", "") + " bx--overflow-menu-options__option"
        )

        menuid = hg.F(
            lambda c: OverflowMenu.MENUID_TEMPLATE % hg.html_id(c.get("row", self))
        )
        triggerid = hg.F(
            lambda c: (OverflowMenu.MENUID_TEMPLATE % hg.html_id(c.get("row", self)))
            + "-trigger"
        )

        super().__init__(
            hg.BUTTON(
                Icon(menuiconname, size=16),
                _class="bx--overflow-menu__trigger"
                + (
                    " bx--tooltip__trigger bx--tooltip--a11y bx--tooltip--right bx--tooltip--align-start"
                    if menuname is not None
                    else ""
                ),
                aria_haspopup="true",
                aria_expanded="false",
                aria_controls=menuid,
                type="button",
                id=triggerid,
            ),
            hg.DIV(
                hg.UL(
                    hg.Iterator(
                        links,
                        "link",
                        hg.LI(
                            hg.F(overflow_button_wrapper),
                            **item_attributes,
                        ),
                    ),
                    _class="bx--overflow-menu-options__content",
                ),
                _class="bx--overflow-menu-options"
                + (" bx--overflow-menu--flip" if flip else ""),
                tabindex="-1",
                role="menu",
                aria_labelledby=triggerid,
                data_floating_menu_direction=direction,
                id=menuid,
            ),
            **attributes,
        )
        if menuname is not None:
            self[0].insert(0, hg.SPAN(menuname, _class="bx--assistive-text"))
