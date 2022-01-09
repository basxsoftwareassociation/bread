from typing import Union

import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.layout.components.button import Button
from bread.utils import Link, aslayout


@aslayout
def error_layout(
    request,
    status_code: int,
    status_title: str,
    description: Union[str, hg.BaseElement],
    exception: BaseException = None,
    exception_detail: str = None,
    redirect_link: Link = None,
):
    ret = hg.BaseElement(
        hg.H1(f"{status_code}: {status_title}", style="margin-bottom: 1rem;"),
        hg.P(
            description,
            style="margin-bottom: 1rem;",
        ),
    )

    if exception or exception_detail:
        ex_msg = ""
        if exception_detail or hasattr(exception, "message"):
            if exception_detail is not None:
                ex_msg = exception_detail
            elif hasattr(exception, "message"):
                ex_msg = exception.message

            ret.append(
                hg.H4("Detail", style="margin-bottom: 1rem;"),
            )
            ret.append(
                hg.DIV(
                    ex_msg,
                    style=(
                        "border: 1px solid grey;"
                        "padding: 1rem;"
                        "font-family: monospace;"
                        "margin-bottom: 1rem;"
                    ),
                ),
            )

    if redirect_link is not None:
        ret.append(
            Button.fromlink(redirect_link),
        )
    else:
        ret.append(
            Button.fromlink(Link(label="Back to homepage", href="/")),
        )

    return ret
