import htmlgenerator as hg
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.html import strip_tags
from django.utils.translation import get_language

from .components.notification import ToastNotification
from .components.shell_header import ShellHeader
from .components.sidenav import SideNav

_static = staticfiles_storage.url


def default_page_layout(menu, *content):
    return hg.HTML(
        hg.HEAD(
            hg.META(charset="utf-8"),
            hg.META(name="viewport", content="width=device-width, initial-scale=1"),
            hg.TITLE(
                hg.F(
                    lambda c, e: strip_tags(c.get("pagetitle", c.get("PLATFORMNAME")))
                    + " | "
                    + strip_tags(c.get("PLATFORMNAME"))
                )
            ),
            hg.LINK(rel="shortcut icon", href=_static("logo.png")),
            hg.LINK(
                rel="stylesheet",
                type="text/css",
                href=_static("css/bread-main.css"),
                media="all",
            ),
            hg.LINK(
                rel="stylesheet",
                type="text/css",
                href=_static("djangoql/css/completion.css"),
            ),
        ),
        hg.BODY(
            ShellHeader(
                hg.C("PLATFORMNAME"),
                hg.C("COMPANYNAME"),
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
                        message=hg.C("message.tags.capitalize"),
                        details=hg.C("message.message"),
                        kind=hg.C("message.level_tag"),
                        hidetimestamp=True,
                        style=hg.BaseElement(
                            "opacity: 0; animation: ",
                            hg.F(lambda c, e: 4 + 3 * c["message_index"]),
                            "s ease-in-out notification",
                        ),
                        onload=hg.BaseElement(
                            "setTimeout(() => this.style.display = 'None', ",
                            hg.F(lambda c, e: (4 + 3 * c["message_index"]) * 1000),
                            ")",
                        ),
                    ),
                ),
                style="position: fixed; right: 0; z-index: 999",
            ),
            hg.DIV(*content, _class="bx--content"),
            hg.SCRIPT(src=_static("js/main.js")),
            hg.SCRIPT(src=_static("js/bliss.min.js")),
            hg.SCRIPT(src=_static("js/htmx.min.js")),
            hg.SCRIPT(src=_static("design/carbon_design/js/carbon-components.js")),
            hg.SCRIPT(src=_static("djangoql/js/completion.js")),
            hg.SCRIPT("CarbonComponents.watch(document);"),
        ),
        doctype=True,
        _class="no-js",
        lang=get_language(),
    )
