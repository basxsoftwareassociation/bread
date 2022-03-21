import htmlgenerator as hg
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.html import strip_tags
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from .components.notification import ToastNotification
from .components.shell_header import ShellHeader
from .components.sidenav import SideNav

_static = staticfiles_storage.url


def default_page_layout(menu, *content):
    return hg.HTML(
        hg.HEAD(
            hg.TITLE(
                hg.F(
                    lambda c: strip_tags(c.get("pagetitle", c.get("PLATFORMNAME")))
                    + " | "
                    + strip_tags(c.get("PLATFORMNAME"))
                )
            ),
            hg.LINK(rel="shortcut icon", href=_static("logo.png")),
            hg.LINK(
                rel="stylesheet",
                type="text/css",
                href=hg.If(
                    settings.DEBUG,
                    _static("css/bread-main.css"),  # generate with "make css"
                    _static("css/bread-main.min.css"),  # generate with "make css"
                ),
                media="all",
            ),
        ),
        hg.BODY(
            ShellHeader(
                hg.C("PLATFORMNAME"),
                hg.C("COMPANYNAME"),
                searchbar=hg.If(
                    hg.C("request.user.is_authenticated"),
                    hg.C("SEARCHBAR"),
                    "",
                ),
            ),
            hg.If(
                hg.C("request.user.is_authenticated"),
                SideNav(menu),
            ),
            hg.DIV(
                hg.Iterator(
                    hg.C("messages"),
                    "message",
                    ToastNotification(
                        message=hg.F(lambda c: _(c["message"].tags.capitalize())),
                        details=hg.C("message.message"),
                        kind=hg.C("message.level_tag"),
                        hidetimestamp=True,
                        autoremove=5.0,
                    ),
                ),
                style="position: fixed; right: 0; z-index: 999",
            ),
            hg.DIV(*content, _class="bx--content"),
            hg.If(
                settings.DEBUG,
                hg.BaseElement(
                    hg.SCRIPT(src=_static("js/bliss.js")),
                    hg.SCRIPT(src=_static("js/htmx.js")),
                    hg.SCRIPT(src=_static("js/main.js")),
                    hg.SCRIPT(
                        src=_static("design/carbon_design/js/carbon-components.js")
                    ),
                ),
                hg.SCRIPT(src=_static("js/bread.min.js")),  # generate with "make js"
            ),
            hg.SCRIPT("CarbonComponents.watch(document);"),
        ),
        doctype=True,
        _class="no-js",
        lang=get_language(),
    )
