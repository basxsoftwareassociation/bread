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
        item_selector,
        item_label_selector,
        item_value_selector,
        query_urlparameter="q",
        size="lg",
        **elementattributes,
    ):
        widgetattributes["value"] = widgetattributes["value"][0]
        # This works inside a formset. Might need to be changed for other usages.
        current_selection = getattr(
            boundfield.form.instance, elementattributes["fieldname"], ""
        )

        resultcontainerid = f"search-result-{hg.html_id((self, search_url))}"
        search_input_id = "search__" + hg.html_id(self)
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
            hg.INPUT(_type="hidden", **widgetattributes),
            _search_input(
                query_urlparameter,
                search_url,
                widget_id,
                search_input_id,
                resultcontainerid,
                size,
                tag_id,
                item_selector,
                item_label_selector,
                item_value_selector,
            ),
            style="display: flex;",
            **elementattributes,
        )


def _search_input(
    query_urlparameter,
    search_url,
    widget_id,
    search_input_id,
    resultcontainerid,
    size,
    tag_id,
    item_selector,
    item_label_selector,
    item_value_selector,
):
    return hg.DIV(
        hg.DIV(
            hg.INPUT(
                hx_get=search_url,
                hx_trigger="changed, keyup changed delay:500ms",
                hx_target=f"#{resultcontainerid}",
                hx_indicator=f"#{resultcontainerid}-indicator",
                name=query_urlparameter,
                id=search_input_id,
                _class="bx--search-input",
                type="text",
            ),
            _search_icon(),
            _clear_search_input_button(resultcontainerid),
            _loading_indicator(resultcontainerid),
            _class=f"bx--search bx--search--{size}",
            data_search=True,
            role="search",
        ),
        hg.DIV(
            hg.DIV(
                id=resultcontainerid,
                _style="width: 100%; position: absolute; z-index: 999",
                onload="htmx.onLoad(function(target) { "
                f"$$('#{resultcontainerid} {item_selector}')._"
                f".addEventListener('click', {_click_on_result_handler(widget_id, tag_id, item_label_selector, item_value_selector)});"
                "});",
            ),
            style="width: 100%; position: relative",
        ),
    )


def _click_on_result_handler(
    widget_id,
    tag_id,
    item_label_selector,
    item_value_selector,
):
    return (
        "function(evt) { "
        f"let label = $('{item_label_selector}', this).innerHTML;"
        f"let value = $('{item_value_selector}', this).innerHTML;"
        f"$('#{widget_id}').value = value;"
        f"$('#{tag_id}').innerHTML = label;"
        "}"
    )


def _search_icon():
    return Icon(
        "search",
        size=16,
        _class="bx--search-magnifier",
        aria_hidden="true",
    )


def _loading_indicator(resultcontainerid):
    return hg.DIV(
        Loading(small=True),
        id=f"{resultcontainerid}-indicator",
        _class="htmx-indicator",
        style="position: absolute; right: 2rem",
    )


def _clear_search_input_button(resultcontainerid):
    return hg.BUTTON(
        Icon("close", size=20, _class="bx--search-clear"),
        _class="bx--search-close bx--search-close--hidden",
        title=_("Clear search input"),
        aria_label=_("Clear search input"),
        type="button",
        onclick=f"document.getElementById('{resultcontainerid}').innerHTML = '';",
    )
