from typing import Union

import htmlgenerator as hg

from bread.layout.components.button import Button
from bread.utils import Link, aslayout


@aslayout
def error_layout(
    request,
    status_code: int,
    status_title: str,
    description: Union[str, hg.BaseElement],
    exception_detail: str = None,
    redirect_link: Link = None,
):
    return hg.BaseElement(
        hg.H1(f"{status_code}: {status_title}", style="margin-bottom: 1rem;"),
        hg.P(
            description,
            style="margin-bottom: 1rem;",
        ),
        hg.If(
            exception_detail,
            hg.BaseElement(
                hg.H4("Detail", style="margin-bottom: 1rem;"),
                hg.DIV(
                    exception_detail,
                    style=(
                        "border: 1px solid grey;"
                        "padding: 1rem;"
                        "font-family: monospace;"
                        "margin-bottom: 1rem;"
                    ),
                ),
            ),
        ),
        Button.fromlink(Link(label="Back to homepage", href="/")),
    )
