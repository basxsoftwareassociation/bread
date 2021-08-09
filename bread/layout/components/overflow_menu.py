import htmlgenerator as hg

from .icon import Icon


class OverflowMenu(hg.DIV):
    """Implements https://www.carbondesignsystem.com/components/overflow-menu/usage"""

    MENUID_TEMPLATE = "overflow-menu-%s"

    def __init__(
        self,
        actions,
        menuiconname="overflow-menu--vertical",
        menuname=None,
        direction="bottom",
        flip=False,
        item_attributes={},
        **attributes,
    ):
        """actions: an iterable which contains bread.menu.Action objects where the onclick value is what will be passed to the onclick attribute of the menu-item (and therefore should be javascript, e.g. "window.location.href='/home'")."""
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
                        actions,
                        "action",
                        hg.LI(
                            hg.BUTTON(
                                hg.DIV(
                                    hg.If(
                                        hg.C("action.icon"),
                                        Icon(hg.C("action.icon"), size=16),
                                    ),
                                    hg.C("action.label"),
                                    _class="bx--overflow-menu-options__option-content",
                                ),
                                _class="bx--overflow-menu-options__btn",
                                role="menuitem",
                                type="button",
                                title=hg.C("action.label"),
                                onclick=hg.C("action.js"),
                            ),
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
