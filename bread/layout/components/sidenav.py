import htmlgenerator as hg

import bread

from ..utils import HasBreadCookieValue
from .icon import Icon


def isactive(itemaccessor):
    return hg.F(lambda c: c[itemaccessor].active(c["request"]))


class SideNav(hg.ASIDE):
    def __init__(self, menu: "bread.menu.Menu", **kwargs):
        kwargs["_class"] = hg.BaseElement(
            kwargs.get("_class", ""),
            " bx--side-nav bx--side-nav--rail",
            hg.If(
                HasBreadCookieValue("sidenav-hidden", "true"),
                "",
                " bx--side-nav--expanded",
            ),
        )
        kwargs["data_side_nav"] = True
        super().__init__(
            hg.NAV(
                hg.UL(
                    hg.Iterator(
                        hg.F(
                            lambda c: (
                                i
                                for i in sorted(
                                    hg.resolve_lazy(menu, c)._registry.values()
                                )
                                if i.has_permission(c["request"])
                            )
                        ),
                        "menugroup",
                        hg.LI(
                            hg.If(
                                hg.F(lambda c: len(c["menugroup"].items) > 1),
                                hg.BaseElement(
                                    hg.BUTTON(
                                        hg.DIV(
                                            Icon(hg.C("menugroup.iconname"), size=16),
                                            _class="bx--side-nav__icon",
                                        ),
                                        hg.SPAN(
                                            hg.C("menugroup.label"),
                                            _class="bx--side-nav__submenu-title",
                                        ),
                                        hg.DIV(
                                            Icon("chevron--down", size=16),
                                            _class="bx--side-nav__icon bx--side-nav__submenu-chevron",
                                        ),
                                        _class="bx--side-nav__submenu",
                                        type="button",
                                        aria_haspopup="true",
                                        aria_expanded=hg.If(
                                            isactive("menugroup"), "true"
                                        ),
                                    ),
                                    hg.UL(
                                        hg.Iterator(
                                            hg.F(
                                                lambda c: (
                                                    i
                                                    for i in sorted(
                                                        c["menugroup"].items
                                                    )
                                                    if i.has_permission(c["request"])
                                                )
                                            ),
                                            "menuitem",
                                            hg.LI(
                                                hg.A(
                                                    hg.SPAN(
                                                        hg.C("menuitem.link.label"),
                                                        _class="bx--side-nav__link-text",
                                                    ),
                                                    _class=hg.BaseElement(
                                                        "bx--side-nav__link",
                                                        hg.If(
                                                            isactive("menuitem"),
                                                            " bx--side-nav__link--current",
                                                        ),
                                                    ),
                                                    href=hg.C("menuitem.link.href"),
                                                ),
                                                _class=hg.BaseElement(
                                                    "bx--side-nav__menu-item",
                                                    hg.If(
                                                        isactive("menuitem"),
                                                        " bx--side-nav__menu-item--current",
                                                    ),
                                                ),
                                            ),
                                        ),
                                        _class="bx--side-nav__menu",
                                    ),
                                ),
                                hg.A(
                                    hg.DIV(
                                        Icon(
                                            hg.C("menugroup.items.0.link.iconname"),
                                            size=16,
                                        ),
                                        _class="bx--side-nav__icon",
                                    ),
                                    hg.SPAN(
                                        hg.C("menugroup.items.0.link.label"),
                                        _class="bx--side-nav__link-text",
                                    ),
                                    _class=hg.BaseElement(
                                        "bx--side-nav__link",
                                        hg.If(
                                            isactive("menugroup"),
                                            " bx--side-nav__link--current",
                                        ),
                                    ),
                                    href=hg.C("menugroup.items.0.link.href"),
                                ),
                            ),
                            _class=hg.BaseElement(
                                "bx--side-nav__item",
                                hg.If(
                                    isactive("menugroup"), " bx--side-nav__item--active"
                                ),
                            ),
                        ),
                    ),
                    _class="bx--side-nav__items",
                ),
                hg.FOOTER(
                    hg.BUTTON(
                        hg.DIV(
                            Icon(
                                "close",
                                size=20,
                                _class="bx--side-nav__icon--collapse bx--side-nav-collapse-icon",
                                aria_hidden="true",
                            ),
                            Icon(
                                "chevron--right",
                                size=20,
                                _class="bx--side-nav__icon--expand bx--side-nav-expand-icon",
                                aria_hidden="true",
                            ),
                            _class="bx--side-nav__icon",
                        ),
                        hg.SPAN(
                            "Toggle the expansion state of the navigation",
                            _class="bx--assistive-text",
                        ),
                        _class="bx--side-nav__toggle",
                        onclick="setBreadCookie('sidenav-hidden', getBreadCookie('sidenav-hidden', 'false') != 'true');",
                    ),
                    _class="bx--side-nav__footer",
                ),
                _class="bx--side-nav__navigation",
            ),
            **kwargs,
        )
