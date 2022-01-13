import typing

import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from .icon import Icon
from .loading import Loading


class SearchBackendConfig(typing.NamedTuple):
    """Describes an endpoint for auto-complete searches"""

    url: typing.Any
    result_selector: str = ""
    result_label_selector: str = ""
    result_value_selector: str = ""
    query_parameter: str = "q"


class Search(hg.DIV):
    def __init__(
        self,
        size="xl",
        placeholder=None,
        widgetattributes=None,
        backend=None,
        resultcontainerid=None,
        show_result_container=True,
        resultcontainer_onload_js=None,
        disabled=False,
        **kwargs,
    ):
        """
        :param SearchBackendConfig backend: Where and how to get search results
        """
        kwargs["_class"] = kwargs.get("_class", "") + f" bx--search bx--search--{size}"
        kwargs["data_search"] = True
        kwargs["role"] = "search"
        width = kwargs.get("width", None)
        if width:
            kwargs["style"] = kwargs.get("style", "") + f"width:{width};"

        widgetattributes = {
            "id": "search__" + hg.html_id(self),
            "_class": "bx--search-input",
            "type": "text",
            "placeholder": placeholder or _("Search"),
            "autocomplete": "off",
            **(widgetattributes or {}),
        }
        if backend:
            if resultcontainerid is None:
                resultcontainerid = f"search-result-{hg.html_id((self, backend.url))}"
            widgetattributes["hx_get"] = backend.url
            widgetattributes["hx_trigger"] = "changed, click, keyup changed delay:500ms"
            widgetattributes["hx_target"] = hg.format("#{}", resultcontainerid)
            widgetattributes["hx_indicator"] = hg.format(
                "#{}-indicator", resultcontainerid
            )
            widgetattributes["name"] = backend.query_parameter

        self.close_button = _close_button(resultcontainerid, widgetattributes)

        super().__init__(
            hg.DIV(
                hg.LABEL(_("Search"), _class="bx--label", _for=widgetattributes["id"]),
                hg.INPUT(**widgetattributes),
                _search_icon(),
                self.close_button,
                hg.If(backend is not None, _loading_indicator(resultcontainerid)),
                **kwargs,
            ),
            hg.If(
                backend is not None and show_result_container,
                _result_container(resultcontainerid, resultcontainer_onload_js, width),
            ),
            style=hg.If(disabled, hg.BaseElement("display: none")),
        )


def _result_container(_id, onload_js, width="100%"):
    return hg.DIV(
        hg.DIV(
            id=_id,
            style="width: 100%; position: absolute; z-index: 999",
            onload=onload_js,
        ),
        style=f"width: {width}; position: relative",
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
        id=hg.format("{}-indicator", resultcontainerid),
        _class="htmx-indicator",
        style="position: absolute; right: 2rem",
    )


def _close_button(resultcontainerid, widgetattributes):
    kwargs = {
        "_class": hg.BaseElement(
            "bx--search-close",
            hg.If(widgetattributes.get("value"), None, " bx--search-close--hidden"),
        ),
        "title": _("Clear search input"),
        "aria_label": _("Clear search input"),
        "type": "button",
    }
    if resultcontainerid is not None:
        kwargs["onclick"] = hg.format(
            "document.getElementById('{}').innerHTML = '';", resultcontainerid
        )
    return hg.BUTTON(Icon("close", size=20, _class="bx--search-clear"), **kwargs)
