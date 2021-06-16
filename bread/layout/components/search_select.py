import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .icon import Icon
from .loading import Loading
from .tag import Tag


class SearchSelect(hg.DIV):
    def __init__(
        self,
        search_url,
        boundfield,
        widgetattributes,
        query_urlparameter="q",
        size="lg",
        searchinput_attributes=None,
        **elementattributes,
    ):
        searchinput_attributes = searchinput_attributes or {}
        current_selection_id = widgetattributes["value"][0]
        # This works inside a formset. Might need to be changed for other usages.
        current_selection = getattr(
            boundfield.form.instance, elementattributes["fieldname"], ""
        )
        elementattributes["_class"] = (
            elementattributes.get("_class", "") + f" bx--search bx--search--{size}"
        )
        elementattributes["data_search"] = True
        elementattributes["role"] = "search"

        resultcontainerid = f"search-result-{hg.html_id((self, search_url))}"

        url = f"{search_url}&target-id-to-store-selected={widgetattributes['id']}"
        search_input_id = "search__" + hg.html_id(self)
        super().__init__(
            Tag(
                current_selection,
                id=widgetattributes["id"] + "-tag",
                style=hg.If(
                    current_selection_id == "",
                    hg.BaseElement("visibility: hidden"),
                ),
                onclick="return false;",
            ),
            hg.INPUT(_type="hidden", **widgetattributes),
            hg.DIV(
                hg.DIV(
                    hg.LABEL(_("Search"), _class="bx--label", _for=search_input_id),
                    hg.INPUT(
                        hx_get=url,
                        hx_trigger="changed, keyup changed delay:500ms",
                        hx_target=f"#{resultcontainerid}",
                        hx_indicator=f"#{resultcontainerid}-indicator",
                        name=query_urlparameter,
                        id=search_input_id,
                        _class="bx--search-input",
                        type="text",
                        **searchinput_attributes,
                    ),
                    Icon(
                        "search",
                        size=16,
                        _class="bx--search-magnifier",
                        aria_hidden="true",
                    ),
                    hg.BUTTON(
                        Icon("close", size=20, _class="bx--search-clear"),
                        _class="bx--search-close bx--search-close--hidden",
                        title=_("Clear search input"),
                        aria_label=_("Clear search input"),
                        type="button",
                        onclick=f"document.getElementById('{resultcontainerid}').innerHTML = '';",
                    ),
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
            ),
            style="display: flex;",
        )
