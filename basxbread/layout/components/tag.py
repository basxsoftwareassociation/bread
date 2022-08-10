import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .icon import Icon

TAG_COLORS = (
    "red",
    "magenta",
    "purple",
    "blue",
    "cyan",
    "teal",
    "green",
    "gray",
    "cool-gray",
    "warm-gray",
)


class Tag(hg.BUTTON):
    def __init__(self, *label, can_delete=False, tag_color=None, **kwargs):
        if tag_color is not None and tag_color not in TAG_COLORS:
            raise ValueError(
                f"Argument 'tag_color' was '{tag_color}' but must be one of '{TAG_COLORS}'"
            )

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
