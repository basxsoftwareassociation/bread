import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.utils import reverse

from .icon import Icon


class ShellHeader(hg.HEADER):
    def __init__(self, platform, company, actions=(), *args, **kwargs):
        from django.contrib.staticfiles.storage import staticfiles_storage

        super().__init__(
            hg.If(
                hg.F(
                    lambda c, e: c["request"].user.is_authenticated
                    and hasattr(c["request"].user, "preferences")
                    and c["request"].user.preferences.get(
                        "user_interface__navigation_menu_extended", True
                    )
                ),
                hg.A(
                    hg.SPAN(platform, _class="bx--header__name--prefix"),
                    hg.SPAN(company, style="position: absolute; left: 17rem"),
                    _class="bx--header__name",
                    style="font-weight: 400",  # override carbon design
                    href="/",
                ),
                hg.A(
                    hg.IMG(
                        src=staticfiles_storage.url("logo.png"),
                        _class="bx--header__name--prefix",
                        style="width: 1.7rem; height; 1.7rem",
                    ),
                    hg.SPAN(company, style="position: absolute; left: 4rem"),
                    _class="bx--header__name",
                    style="font-weight: 400",  # override carbon design
                    href="/",
                ),
            ),
            hg.DIV(
                hg.If(
                    hg.F(lambda c, e: c["request"].user.is_authenticated),
                    hg.A(
                        hg.SPAN(
                            hg.C("request.user.get_username"),
                            _class="bx--header__name--prefix",
                        ),
                        _class="bx--header__name",
                        href="#",
                        title=hg.C("request.user.get_username"),
                        style="padding: 0; margin-right: 1rem",
                    ),
                ),
                hg.If(
                    hg.F(lambda c, e: c["request"].user.is_authenticated),
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
            role="banner",
            aria_label="{{ branding.platform }}",
            data_header=True,
        )
