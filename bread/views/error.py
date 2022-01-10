import sys

import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.layout import error as layouts


def view400(request, exception):
    response = layouts.error_layout(
        request,
        status_code=400,
        status_title=_("Bad request"),
        description=_(
            "The server cannot process the request due to something that is "
            "perceived to be a client error."
        ),
        exception_detail=exception.message if hasattr(exception, "message") else None,
    )
    response.status_code = 400

    return response


# As I understand, we might not need this page because the website will eventually
# redirect users to the default page. But I'll still make it in case it's necessary.
def view403(request, exception):
    response = layouts.error_layout(
        request,
        status_code=403,
        status_title=_("Forbidden"),
        description=_("You don't have permission to access this resource."),
        exception_detail=exception.message if hasattr(exception, "message") else None,
    )
    response.status_code = 403

    return response


def view404(request, exception):
    response = layouts.error_layout(
        request,
        status_code=404,
        status_title=_("Page not found"),
        description=hg.BaseElement(
            hg.mark_safe(
                _("The path %s does not appear to be any existing page of our website.")
                % f"<strong>{request.path}</strong>"
            )
        ),
        exception_detail=exception.message if hasattr(exception, "message") else None,
    )
    response.status_code = 404

    return response


def view500(request):
    exec_info = sys.exc_info()
    response = layouts.error_layout(
        request,
        status_code=500,
        status_title=_("Internal Server Error"),
        description=hg.BaseElement(
            hg.mark_safe(
                _(
                    "There's a problem occurred within the server related to path %s."
                    "<br>If the problem persists, please contact admin."
                )
                % f"<strong>{request.path}</strong>"
            )
        ),
        exception_detail=f"{str(exec_info[0].__name__)}: {exec_info[1]}",
    )
    response.status_code = 500

    return response
