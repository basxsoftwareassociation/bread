import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from basxbread.utils import reverse

from ..utils import HasBasxBreadCookieValue
from .icon import Icon


class ShellHeader(hg.HEADER):
    def __init__(self, platform, company, searchbar, actions=(), *args, **kwargs):
        super().__init__(
            hg.If(
                HasBasxBreadCookieValue("sidenav-hidden", "true"),
                variable_size_header_part(
                    hg.BaseElement(), company, searchbar, hide=True
                ),
                variable_size_header_part(
                    hg.SPAN(platform, _class="bx--header__name--prefix"),
                    company,
                    searchbar,
                    hide=False,
                ),
            ),
            hg.DIV(
                hg.If(
                    hg.C("request.user.is_authenticated"),
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
                    hg.C("request.user.is_authenticated"),
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

    src = hg.If(
        hg.F(lambda c: c["global_preferences"].get("general__logo")),
        hg.F(lambda c: c["global_preferences"].get("general__logo").url),
        staticfiles_storage.url("logo.png"),
    )

    return hg.IMG(
        src=src,
        _class="bx--header__name--prefix",
        style="width: 1.7rem; height: 1.7rem; margin-right: 0.5rem",
    )


def variable_size_header_part(platform, company, searchbar, hide):
    return hg.BaseElement(
        hg.A(
            logo(),
            platform,
            _class="bx--header__name",
            style="font-weight: 400",  # override carbon design
            href=hg.F(lambda c: c["request"].META["SCRIPT_NAME"] or "/"),
        ),
        None
        if hide
        else hg.A(
            hg.SPAN(company),
            _class="bx--header__name",
            style="font-weight: 400",  # override carbon design
            href=hg.F(lambda c: c["request"].META["SCRIPT_NAME"] or "/"),
        ),
        hg.If(
            searchbar,
            hg.SPAN(searchbar, _class="theme-gray-100", style="padding-left: 0.5rem"),
        ),
    )
