import htmlgenerator as hg
from django.conf import settings

from . import layout


def bread_context(request):
    from bread import menu

    ret = {
        "page": hg.BaseElement(
            layout.shell_header.ShellHeader(
                hg.C("PLATFORMNAME"),
                hg.C("COMPANYNAME"),
            ),
            hg.If(
                hg.C("request.user.is_authenticated"), layout.sidenav.SideNav(menu.main)
            ),
            hg.DIV(
                hg.Iterator(
                    hg.C("messages"),
                    "message",
                    layout.notification.ToastNotification(
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
            hg.DIV(hg.C("layout"), _class="bx--content"),
        )
    }
    return ret


def compress_offline_context():
    yield {"STATIC_URL": settings.STATIC_URL, **bread_context(None)}
