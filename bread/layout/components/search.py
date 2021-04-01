import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .icon import Icon
from .loading import Loading


class Search(hg.DIV):
    def __init__(self, size="xl", placeholder=None, widgetattributes=None, **kwargs):
        kwargs["_class"] = kwargs.get("_class", "") + f" bx--search bx--search--{size}"
        kwargs["data_search"] = True
        kwargs["role"] = "search"

        attributes = {
            "id": "search__" + hg.html_id(self),
            "_class": "bx--search-input",
            "type": "text",
            "placeholder": placeholder or _("Search"),
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

    def withajaxurl(
        self, url, query_urlparameter, resultcontainerid=None, resultcontainer=True
    ):
        resultcontainerid = (
            resultcontainerid or f"search-result-{hg.html_id((self, url))}"
        )
        self[1].attributes["hx_get"] = url
        self[1].attributes["hx_trigger"] = "changed, keyup changed delay:100ms"
        self[1].attributes["hx_target"] = f"#{resultcontainerid}"
        self[1].attributes["hx_indicator"] = f"#{resultcontainerid}-indicator"
        self[1].attributes["name"] = query_urlparameter
        self[3].attributes[
            "onclick"
        ] = f"document.getElementById('{resultcontainerid}').innerHTML = ''"
        self.append(
            hg.DIV(
                Loading(small=True),
                id=f"{resultcontainerid}-indicator",
                _class="htmx-indicator",
                style="position: absolute; right: 2rem",
            ),
        )
        if resultcontainer:
            return hg.BaseElement(
                self,
                hg.DIV(
                    hg.DIV(
                        id=resultcontainerid,
                        _style="width: 100%; position: absolute; z-index: 999",
                    ),
                    style="width: 100%; position: relative",
                ),
            )
        return self
