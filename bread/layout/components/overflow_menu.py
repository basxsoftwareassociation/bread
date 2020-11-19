import htmlgenerator

from .icon import Icon


class OverflowMenuItem(htmlgenerator.LI):
    def __init__(self, itemvalueproviderclass, **attributes):
        attributes["_class"] = (
            attributes.get("_class", "") + " bx--overflow-menu-options__option"
        )
        super().__init__(
            htmlgenerator.BUTTON(
                itemvalueproviderclass.Binding(htmlgenerator.DIV)(
                    htmlgenerator.F(
                        lambda e, c: htmlgenerator.BaseElement(
                            Icon(e.item.icon, size=16), e.item.label
                        )
                        if e.item.icon
                        else e.item.label
                    ),
                    _class="bx--overflow-menu-options__option-content",
                ),
                _class="bx--overflow-menu-options__btn",
                role="menuitem",
            ),
            **attributes,
        )

    def render(self, context):
        self[0].attributes["title"] = self.item.label
        self[0].attributes["onclick"] = self.item.js
        self[0].attributes["disabled"] = not self.item.has_permission(
            context["request"]
        )
        return super().render(context)


class OverflowMenu(htmlgenerator.DIV):
    """Implements https://www.carbondesignsystem.com/components/overflow-menu/usage"""

    def __init__(
        self,
        item_iterator,
        iteratorclass=htmlgenerator.Iterator,
        menuname=None,
        direction="bottom",
        flip=False,
        item_attributes={},
        **attributes,
    ):
        # making the class inline seems better, I think we can enforce scoping the type to this instance of OverflowMenu
        class MenuItemValueProvider(htmlgenerator.ValueProvider):
            attributename = "item"

        """item_iterator: an iterable which contains bread.menu.Action objects where the onclick value is what will be passed to the onclick attribute of the menu-item (and therefore should be javascript, e.g. "window.location.href='/home'"). All three item_iterator in the tuple can be lazy objects
        iteratorclass: If the Iterator needs additional values in order to generate item_iterator it can be customized and passed here"""
        attributes["data-overflow-menu"] = True
        attributes["_class"] = attributes.get("_class", "") + " bx--overflow-menu"
        menuid = f"overflow-menu-{hash(id(self))}"
        super().__init__(
            htmlgenerator.BUTTON(
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
                _id=f"{menuid}-trigger",
            ),
            htmlgenerator.DIV(
                htmlgenerator.UL(
                    iteratorclass(
                        item_iterator,
                        MenuItemValueProvider,
                        MenuItemValueProvider.Binding(OverflowMenuItem)(
                            MenuItemValueProvider, **item_attributes
                        ),
                    ),
                    _class="bx--overflow-menu-options__content",
                ),
                _class="bx--overflow-menu-options"
                + (" bx--overflow-menu--flip" if flip else ""),
                tabindex="-1",
                role="menu",
                aria_labelledby=f"{menuid}-trigger",
                data_floating_menu_direction=direction,
                id=menuid,
            ),
            **attributes,
        )
        if menuname is not None:
            self[0].insert(0, htmlgenerator.SPAN(menuname, _class="bx--assistive-text"))
