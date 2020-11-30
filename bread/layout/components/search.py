import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .icon import Icon


class Search(hg.DIV):
    def __init__(self, size="xl", widgetattributes=None, **kwargs):
        kwargs["_class"] = kwargs.get("_class", "") + f" bx--search bx--search--{size}"
        kwargs["data-search"] = True
        kwargs["role"] = "search"

        attributes = {
            "id": "search__" + hg.html_id(self),
            "_class": "bx--search-input",
            "type": "text",
            "placeholder": _("Search"),
            **(widgetattributes or {}),
        }

        super().__init__(
            hg.LABEL(_("Search"), _class="bx--label", _for=attributes["id"]),
            hg.INPUT(**attributes),
            Icon("search", size=16, _class="bx--search-magnifier", aria_hidden="true"),
            hg.BUTTON(
                Icon("close", size=20, _class="bx--search-clear"),
                _class="bx--search-close bx--search-close--hidden",
                title=_("Clear search input"),
                aria_label=_("Clear search input"),
                type="button",
            ),
            **kwargs,
        )
