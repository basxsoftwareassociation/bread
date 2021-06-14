import htmlgenerator as hg
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from .icon import Icon
from .loading import Loading


class SearchSelect(hg.BaseElement):
    def __init__(
        self,
        search_view,
        query_urlparameter="q",
        size="xl",
        placeholder=None,
        searchinput_widgetattributes=None,
        widgetattributes=None,
        **elementattributes,
    ):
        del elementattributes["boundfield"]
        elementattributes = elementattributes or {}
        elementattributes["_class"] = (
            elementattributes.get("_class", "") + f" bx--search bx--search--{size}"
        )
        elementattributes["data_search"] = True
        elementattributes["role"] = "search"

        search_widget_attributes = {
            "id": "search__" + hg.html_id(self),
            "_class": "bx--search-input",
            "type": "text",
            "placeholder": placeholder or _("Search"),
            **(searchinput_widgetattributes or {}),
        }

        resultcontainerid = f"search-result-{hg.html_id((self, search_view))}"

        super().__init__(
            hg.DIV(
                hg.LABEL(
                    _("Search"), _class="bx--label", _for=search_widget_attributes["id"]
                ),
                hg.INPUT(
                    hx_get=reverse_lazy(search_view),
                    hx_trigger="changed, keyup changed delay:500ms",
                    hx_target=f"#{resultcontainerid}",
                    hx_indicator=f"#{resultcontainerid}-indicator",
                    name=query_urlparameter,
                    **search_widget_attributes,
                ),
                Icon(
                    "search", size=16, _class="bx--search-magnifier", aria_hidden="true"
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
