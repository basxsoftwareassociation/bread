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
        kwargs["_class"] = hg.BaseElement(
            kwargs.get("_class", ""),
            " bx--tag",
            hg.If(can_delete, " bx--tag--filter"),
            (f" bx--tag--{tag_color}" if tag_color else ""),
        )

        on_del = kwargs.pop("ondelete", None)
        super().__init__(
            hg.SPAN(*label, _class="bx--tag__label"),
            hg.If(
                can_delete, Icon("close", size=16, onclick=on_del, title=_("Remove"))
            ),
            **kwargs,
        )
