import typing

import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .icon import Icon
from .loading import Loading
from .tag import Tag


class SearchBackendConfig(typing.NamedTuple):
    url: typing.Any
    result_selector: str
    result_label_selector: str
    result_value_selector: str
    query_parameter: str = "q"


class SearchSelect(hg.DIV):
    def __init__(
        self,
        backend,
        boundfield,
        widgetattributes,
        **elementattributes,
    ):
        """
        :param SearchBackendConfig backend: Where and how to get search results
        """

        widgetattributes["value"] = widgetattributes["value"][0]
        # This works inside a formset. Might need to be changed for other usages.
        current_selection = getattr(
            boundfield.form.instance, elementattributes["fieldname"], ""
        )

        resultcontainerid = f"search-result-{hg.html_id((self))}"
        widget_id = widgetattributes["id"]
        tag_id = f"{widget_id}-tag"
        super().__init__(
            Tag(
                current_selection,
                id=tag_id,
                style=hg.If(
                    widgetattributes["value"] == "",
                    hg.BaseElement("visibility: hidden"),
                ),
                onclick="return false;",
            ),
            hg.INPUT(_type="hidden", **widgetattributes),  # the actual form field
            Search(
                backend,
                resultcontainerid,
                self._init_js(backend, resultcontainerid, tag_id, widget_id),
                size="lg",
            ),
            style="display: flex;",
            **elementattributes,
        )

    @staticmethod
    def _init_js(backend, resultcontainerid, tag_id, widget_id):
        on_click = f"""function(evt) {{
            let label = $('{backend.result_label_selector}', this).innerHTML;
            let value = $('{backend.result_value_selector}', this).innerHTML;
            $('#{widget_id}').value = value;
            $('#{tag_id}').innerHTML = label;
            }}"""

        return f"""htmx.onLoad(function(target) {{
        $$('#{resultcontainerid} {backend.result_selector}')._
        .addEventListener('click', {on_click});
        }});"""


class Search(hg.DIV):
    def __init__(
        self,
        backend,
        resultcontainerid,
        init_js,
        size,
    ):
        super().__init__(
            hg.DIV(
                hg.INPUT(
                    hx_get=backend.url,
                    hx_trigger="changed, keyup changed delay:500ms",
                    hx_target=f"#{resultcontainerid}",
                    hx_indicator=f"#{resultcontainerid}-indicator",
                    name=backend.query_parameter,
                    _class="bx--search-input",
                    type="text",
                ),
                self._search_icon(),
                self._clear_search(resultcontainerid),
                self._loading_indicator(resultcontainerid),
                _class=f"bx--search bx--search--{size}",
                data_search=True,
                role="search",
            ),
            hg.DIV(
                hg.DIV(
                    id=resultcontainerid,
                    _style="width: 100%; position: absolute; z-index: 999",
                    onload=init_js,
                ),
                style="width: 100%; position: relative",
            ),
        )

    @staticmethod
    def _search_icon():
        return Icon(
            "search",
            size=16,
            _class="bx--search-magnifier",
            aria_hidden="true",
        )

    @staticmethod
    def _loading_indicator(resultcontainerid):
        return hg.DIV(
            Loading(small=True),
            id=f"{resultcontainerid}-indicator",
            _class="htmx-indicator",
            style="position: absolute; right: 2rem",
        )

    @staticmethod
    def _clear_search(resultcontainerid):
        return hg.BUTTON(
            Icon("close", size=20, _class="bx--search-clear"),
            _class="bx--search-close bx--search-close--hidden",
            title=_("Clear search input"),
            aria_label=_("Clear search input"),
            type="button",
            onclick=f"document.getElementById('{resultcontainerid}').innerHTML = '';",
        )
