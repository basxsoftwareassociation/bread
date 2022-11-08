import sys
from typing import Optional, Union

import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from ..layout.components.button import Button
from ..utils import Link, aslayout


@aslayout
def error_layout(
    request,
    status_code: int,
    status_title: str,
    description: Union[str, hg.BaseElement],
    exception_detail: Optional[str] = None,
):
    if (
        not hasattr(request, "user")
        or request.user is None
        or not request.user.is_authenticated
    ):
        return hg.BaseElement(f"{status_code} {status_title}")
    return hg.BaseElement(
        hg.H1(f"{status_code}: {status_title}", style="margin-bottom: 1rem;"),
        hg.P(
            description,
            style="margin-bottom: 1rem;",
        ),
        hg.If(
            bool(exception_detail),
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
        Button.from_link(
            Link(
                label=_("Back to homepage"),
                href=hg.F(lambda c: c["request"].META["SCRIPT_NAME"] or "/"),
            )
        ),
    )


def handler400(request, exception):
    response = error_layout(
        request,
        status_code=400,
        status_title=_("Bad request"),
        description=_("The server cannot process the request due to a client error."),
        exception_detail=exception.message if hasattr(exception, "message") else None,
    )
    response.status_code = 400

    return response


def handler403(request, exception):
    response = error_layout(
        request,
        status_code=403,
        status_title=_("Forbidden"),
        description=_("You do not have permission to access this resource."),
        exception_detail=exception.message if hasattr(exception, "message") else None,
    )
    response.status_code = 403

    return response


def handler404(request, exception):
    response = error_layout(
        request,
        status_code=404,
        status_title=_("Page not found"),
        description=hg.BaseElement(
            hg.mark_safe(
                _("The path %s could not be found.")
                % f"<strong>{request.path}</strong>"
            )
        ),
        exception_detail=exception.message if hasattr(exception, "message") else None,
    )
    response.status_code = 404

    return response


def handler500(request):
    exec_info = sys.exc_info()
    response = error_layout(
        request,
        status_code=500,
        status_title=_("Internal Server Error"),
        description=hg.BaseElement(
            hg.mark_safe(
                _(
                    "A problem has occurred while loading the page at %s."
                    "<br>If the problem persists, please contact an administrator."
                )
                % f"<strong>{request.path}</strong>"
            )
        ),
        exception_detail=f"{str(exec_info[0].__name__)}: {exec_info[1]}",
    )
    response.status_code = 500

    return response
