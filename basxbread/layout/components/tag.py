import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .icon import Icon


class Tag(hg.BUTTON):
    def __init__(self, *label, can_delete=False, tag_color=None, **kwargs):
        kwargs.setdefault(
            "type", "button"
        )  # prevents this from trying to submit a form when inside a FORM element
        kwargs["_class"] = (
            kwargs.get("_class", "")
            + " bx--tag"
            + (" bx--tag--filter" if can_delete else "")
            + (f" bx--tag--{tag_color}" if tag_color else "")
        )
        if can_delete:
            kwargs.setdefault("title", _("Remove"))

        super().__init__(
            hg.SPAN(*label, _class="bx--tag__label"),
            *([Icon("close", size=16)] if can_delete else []),
            **kwargs,
        )
