import htmlgenerator
from django.utils.translation import gettext_lazy as _

from ..base import html_id
from .icon import Icon


class Search(htmlgenerator.DIV):
    def __init__(self, size="xl", **kwargs):
        kwargs["_class"] = kwargs.get("_class", "") + f" bx--search bx--search--{size}"
        kwargs["data-search"] = True
        kwargs["role"] = "search"

        inputid = "search__" + html_id(self)
        super().__init__(
            htmlgenerator.LABEL(_("Search"), _class="bx--label", _for=inputid),
            htmlgenerator.INPUT(
                _class="bx--search-input",
                type="text",
                id=inputid,
                placeholder=_("Search"),
            ),
            Icon("search", size=16, _class="bx--search-magnifier", aria_hidden="true"),
            htmlgenerator.BUTTON(
                Icon("close", size=20, _class="bx--search-clear"),
                _class="bx--search-close bx--search-close--hidden",
                title=_("Clear search input"),
                aria_label=_("Clear search input"),
            ),
            **kwargs,
        )
