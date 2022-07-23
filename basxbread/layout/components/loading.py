import htmlgenerator as hg
from django.utils.html import mark_safe

LOADING_ICON = """
<svg class="bx--loading__svg" viewBox="-75 -75 150 150">
    <circle class="bx--loading__stroke" cx="0" cy="0" r="37.5" />
</svg>
"""
LOADING_ICON_SMALL = """
<svg class="bx--loading__svg" viewBox="-75 -75 150 150">
    <circle class="bx--loading__background" cx="0" cy="0" r="26.8125" />
    <circle class="bx--loading__stroke" cx="0" cy="0" r="26.8125" />
</svg>
"""


class Loading(hg.DIV):
    def __init__(self, small=False, **kwargs):
        kwargs["_class"] = kwargs.get("_class", "") + (
            " bx--loading bx--loading--small" if small else " bx--loading"
        )
        super().__init__(
            mark_safe(LOADING_ICON_SMALL if small else LOADING_ICON),
            data_loading=True,
            **kwargs
        )
