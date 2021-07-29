import subprocess

import htmlgenerator as hg

from ..utils import aslayout


@aslayout
def systeminformation(request):
    git_status = ""
    try:
        git_status = subprocess.run(
            ["git", "log", "-n", "5", "--oneline"], capture_output=True, check=True
        ).stdout.decode()
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
    pip_status = ""
    try:
        pip_status = subprocess.run(
            ["pip", "freeze"], capture_output=True, check=True
        ).stdout.decode()
    except subprocess.SubprocessError as e:
        pip_status = hg.BaseElement(
            "ERROR",
            hg.BR(),
            str(e),
            hg.BR(),
            getattr(e, "stdout", b"").decode(),
            hg.BR(),
            getattr(e, "stderr", b"").decode(),
        )

    return hg.BaseElement(
        hg.H3("System information"),
        hg.H4("Git log"),
        hg.PRE(hg.CODE(git_status)),
        hg.H4("PIP packages", style="margin-top: 2rem"),
        hg.PRE(hg.CODE(pip_status)),
    )
