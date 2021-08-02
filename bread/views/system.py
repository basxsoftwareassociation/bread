import subprocess  # nosec because we covered everything

import htmlgenerator as hg
import pkg_resources
from django.utils.translation import gettext_lazy as _

from ..utils import aslayout


@aslayout
def systeminformation(request):
    git_status = ""
    try:
        git_status = (
            subprocess.run(  # nosec because we have no user input to subprocess
                ["git", "log", "-n", "5", "--oneline"], capture_output=True, check=True
            ).stdout.decode()
        )
    except subprocess.SubprocessError as e:
        git_status = hg.BaseElement(
            "ERROR",
            hg.BR(),
            str(e),
            hg.BR(),
            getattr(e, "stdout", b"").decode(),
            hg.BR(),
            getattr(e, "stderr", b"").decode(),
        )

    return hg.BaseElement(
        hg.H3(_("System information")),
        hg.H4("Git log"),
        hg.PRE(hg.CODE(git_status)),
        hg.H4("PIP packages", style="margin-top: 2rem"),
        hg.UL(
            hg.Iterator(
                sorted(
                    ["%s==%s" % (i.key, i.version) for i in pkg_resources.working_set]
                ),
                "package",
                hg.LI(hg.C("package")),
            )
        ),
    )
