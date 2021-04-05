import htmlgenerator as hg
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from bread.utils import reverse

from .icon import Icon


class ShellHeader(hg.HEADER):
    def __init__(self, platform, company, actions=(), *args, **kwargs):
        super().__init__(
            hg.A(
                hg.SPAN(platform, _class="bx--header__name--prefix"),
                mark_safe("&nbsp;"),
                company,
                _class="bx--header__name",
                href="/",
            ),
            hg.DIV(
                hg.If(
                    hg.F(lambda c, e: c["request"].user.is_authenticated),
                    hg.A(
                        hg.SPAN(
                            hg.C("request.user.get_full_name"),
                            _class="bx--header__name--prefix",
                        ),
                        _class="bx--header__name",
                        href="#",
                        title=hg.C("request.user.get_username"),
                        style="padding: 0",
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
