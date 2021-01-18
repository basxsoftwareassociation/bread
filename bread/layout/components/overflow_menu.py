import htmlgenerator as hg

from .icon import Icon


class OverflowMenuItem(hg.LI):
    def __init__(self, menucontext, **attributes):
        icon = hg.ATTR("action.icon", self)
        label = hg.ATTR("action.label", self)
        js = hg.ATTR("action.js", self)
        attributes["_class"] = (
            attributes.get("_class", "") + " bx--overflow-menu-options__option"
        )
        buttonclass = hg.BUTTON
        if menucontext:
            buttonclass = menucontext.Binding(buttonclass)
        super().__init__(
            buttonclass(
                hg.DIV(
                    Icon(icon, size=16),
                    label,
                    _class="bx--overflow-menu-options__option-content",
                ),
                _class="bx--overflow-menu-options__btn",
                role="menuitem",
                type="button",
                title=label,
                onclick=js,
            ),
            **attributes,
        )


class OverflowMenu(hg.DIV):
    """Implements https://www.carbondesignsystem.com/components/overflow-menu/usage"""

    MENUID_TEMPLATE = "overflow-menu-%s"
    TRIGGERID_TEMPLATE = "%s-trigger"

    def __init__(
        self,
        actions,
        menuname=None,
        menucontext=None,
        direction="bottom",
        flip=False,
        item_attributes={},
        **attributes,
    ):
        parents = (hg.ValueProvider,)
        if menucontext:
            parents = (menucontext.Binding(), hg.ValueProvider)

        ActionProvider = type("ActionProvider", parents, {"attributename": "action"})

        """actions: an iterable which contains bread.menu.Action objects where the onclick value is what will be passed to the onclick attribute of the menu-item (and therefore should be javascript, e.g. "window.location.href='/home'").
       """
        attributes["data-overflow-menu"] = True
        attributes["_class"] = attributes.get("_class", "") + " bx--overflow-menu"

        self.menucounter = 0
        menuid, triggerid = self.nextmenuid()

        super().__init__(
            hg.BUTTON(
                Icon("overflow-menu--vertical", size=16),
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
                        ActionProvider.Binding(OverflowMenuItem)(
                            menucontext, **item_attributes
                        ),
                        ActionProvider,
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

    def nextmenuid(self):
        # because we need unique menu-ids, need to update this in render in case were are inside an loop and render this element multiple times
        self.menucounter += 1
        menuid = OverflowMenu.MENUID_TEMPLATE % self.menucounter
        return menuid, OverflowMenu.TRIGGERID_TEMPLATE % menuid

    def render(self, context):
        menuid, triggerid = self.nextmenuid()
        self[0].attributes["id"] = triggerid
        self[0].attributes["aria_controls"] = menuid
        self[1].attributes["id"] = menuid
        self[1].attributes["aria_labelledby"] = triggerid
        return super().render(context)
