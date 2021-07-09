import htmlgenerator as hg
from django.conf import settings

from . import layout


def bread_context(request):
    ret = {
        "headerlayout": layout.shell_header.ShellHeader(
            hg.C("PLATFORMNAME"),
            "",
        ),
    }
    return ret


def compress_offline_context():
    yield {"STATIC_URL": settings.STATIC_URL, **bread_context(None)}
