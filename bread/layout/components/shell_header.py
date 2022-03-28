import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.utils import reverse

from ..utils import HasBreadCookieValue
from .icon import Icon


class ShellHeader(hg.HEADER):
    def __init__(self, platform, company, searchbar, actions=(), *args, **kwargs):
        super().__init__(
            hg.If(
                HasBreadCookieValue("sidenav-hidden", "true"),
                variable_size_header_part(hg.BaseElement(), company, searchbar, "5rem"),
                variable_size_header_part(
                    hg.SPAN(platform, _class="bx--header__name--prefix"),
                    company,
                    searchbar,
                    "18rem",
                ),
            ),
            hg.DIV(
                hg.If(
                    hg.F(lambda c: c["request"].user.is_authenticated),
                    hg.A(
                        hg.SPAN(
                            hg.C("request.user.get_username"),
                            _class="bx--header__name--prefix",
                        ),
                        _class="bx--header__name",
                        href=reverse("userprofile"),
                        title=hg.C("request.user.get_username"),
                        style="padding: 0; margin-right: 1rem",
                    ),
                ),
                hg.If(
                    hg.F(lambda c: c["request"].user.is_authenticated),
                    hg.BUTTON(
                        Icon(
                            "logout",
                            size=20,
                            _class="bx--navigation-menu-panel-expand-icon",
                            aria_hidden="true",
                        ),
                        Icon(
                            "logout",
                            size=20,
                            _class="bx--navigation-menu-panel-collapse-icon",
                            aria_hidden="true",
                        ),
                        _class="bx--header__menu-trigger bx--header__action",
                        title=_("Logout"),
                        data_navigation_menu_panel_label_expand=_("Logout"),
                        data_navigation_menu_panel_label_collapse=_("Close"),
                        onclick=f"document.location = '{reverse('logout')}'",
                    ),
                ),
                _class="bx--header__global",
            ),
            _class="bx--header",
            data_header=True,
        )


def logo():
    from django.contrib.staticfiles.storage import staticfiles_storage

    return hg.IMG(
        src=staticfiles_storage.url("logo.png"),
        _class="bx--header__name--prefix",
        style="width: 1.7rem; height: 1.7rem; margin-right: 0.5rem",
    )


def variable_size_header_part(platform, company, searchbar, searchbar_position):
    return hg.BaseElement(
        hg.A(
            logo(),
            platform,
            _class="bx--header__name",
            style="font-weight: 400",  # override carbon design
            href=hg.F(lambda c: c["request"].META["SCRIPT_NAME"] or "/"),
        ),
        hg.If(
            searchbar,
            hg.SPAN(
                searchbar,
                style=f"position: absolute; left: {searchbar_position}",
                _class="theme-gray-100",
            ),
            "",
        ),
        hg.A(
            hg.SPAN(
                company,
                style=hg.format(
                    "position: absolute; left: {}",
                    hg.If(searchbar, "50%", searchbar_position),
                ),
            ),
            _class="bx--header__name",
            style="font-weight: 400",  # override carbon design
            href=hg.F(lambda c: c["request"].META["SCRIPT_NAME"] or "/"),
        ),
    )
