import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.layout.components.button import Button
from bread.utils import Link, aslayout


def _common(request):
    return hg.BaseElement(
        hg.H1(_("404: Page not found"), style="margin-bottom: 1rem;"),
        hg.P(
            hg.mark_safe(
                _("The path %s does not appear to be any existing page in our website.")
                % str(hg.STRONG(request.path)),
            ),
            style="margin-bottom: 1rem;",
        ),
        Button.fromlink(Link(label="Back to homepage", href="/")),
    )


@aslayout
def layout404(request):
    return hg.BaseElement(
        hg.H1(_("404: Page not found"), style="margin-bottom: 1rem;"),
        hg.P(
            hg.mark_safe(
                _(
                    "The path %s you are looking for does not appear to be any existing page in the website."
                )
                % str(hg.STRONG(request.path)),
            ),
            style="margin-bottom: 1rem;",
        ),
        Button.fromlink(Link(label="Back to homepage", href="/")),
    )
