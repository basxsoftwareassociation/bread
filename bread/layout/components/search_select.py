import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

import bread.utils

from .icon import Icon
from .loading import Loading
from .tag import Tag


class SearchSelect(hg.BaseElement):
    def __init__(
        self,
        search_view,
        query_urlparameter="q",
        size="xl",
        searchinput_widgetattributes=None,
        widgetattributes=None,
        **elementattributes,
    ):
        current_selection_id = widgetattributes["value"][0]
        current_selection = (
            getattr(
                elementattributes["boundfield"].form.instance,
                elementattributes["fieldname"],
            )
            if current_selection_id
            else None
        )
        del elementattributes["boundfield"]
        elementattributes["_class"] = (
            elementattributes.get("_class", "") + f" bx--search bx--search--{size}"
        )
        elementattributes["data_search"] = True
        elementattributes["role"] = "search"

        search_widget_attributes = {
            "id": "search__" + hg.html_id(self),
            "_class": "bx--search-input",
            "type": "text",
            "style": "width: auto;",
            **(searchinput_widgetattributes or {}),
        }

        resultcontainerid = f"search-result-{hg.html_id((self, search_view))}"

        url = bread.utils.reverse(
            search_view,
            query={
                "target-id-to-store-selected": widgetattributes["id"],
            },
        )
        super().__init__(
            hg.DIV(
                hg.LABEL(
                    _("Search"), _class="bx--label", _for=search_widget_attributes["id"]
                ),
                hg.INPUT(
                    hx_get=url,
                    hx_trigger="changed, keyup changed delay:500ms",
                    hx_target=f"#{resultcontainerid}",
                    hx_indicator=f"#{resultcontainerid}-indicator",
                    name=query_urlparameter,
                    **search_widget_attributes,
                ),
                hg.If(
                    current_selection_id == "",
                    Icon(
                        "search",
                        size=16,
                        _class="bx--search-magnifier",
                        aria_hidden="true",
                    ),
                ),
                Tag(
                    current_selection,
                    id=widgetattributes["id"] + "-tag",
                    style=hg.If(
                        current_selection_id == "",
                        hg.BaseElement("visibility: hidden"),
                    ),
                    onclick="return false;",
                ),
                hg.BUTTON(
                    Icon("close", size=20, _class="bx--search-clear"),
                    _class="bx--search-close bx--search-close--hidden",
                    title=_("Clear search input"),
                    aria_label=_("Clear search input"),
                    type="button",
                    onclick=f"document.getElementById('{resultcontainerid}').innerHTML = '';",
                ),
                hg.INPUT(_type="hidden", **widgetattributes),
                hg.DIV(
                    Loading(small=True),
                    id=f"{resultcontainerid}-indicator",
                    _class="htmx-indicator",
                    style="position: absolute; right: 2rem",
                ),
                **elementattributes,
            ),
            hg.DIV(
                hg.DIV(
                    id=resultcontainerid,
                    _style="width: 100%; position: absolute; z-index: 999",
                ),
                style="width: 100%; position: relative",
            ),
        )
