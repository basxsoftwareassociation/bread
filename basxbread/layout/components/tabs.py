import collections
import typing

import htmlgenerator as hg
from django.utils.text import slugify

from ..utils import HasBasxBreadCookieValue


class TabLabel(hg.LI):
    def __init__(self, label, tabid, panelid, selected):
        super().__init__(
            hg.A(
                label,
                tabindex="0",
                id=tabid,
                _class="bx--tabs__nav-link",
                href="javascript:void(0)",
                aria_controls=panelid,
                aria_selected=hg.If(selected, "true", "false"),
                role="tab",
            ),
            _class=hg.BaseElement(
                "bx--tabs__nav-item",
                hg.If(selected, " bx--tabs__nav-item--selected"),
            ),
            data_target="#" + panelid,
            aria_selected=hg.If(selected, "true", "false"),
            role="tab",
            onclick=hg.BaseElement("setBasxBreadCookie('selected-tab', '", tabid, "')"),
        )


class TabPanel(hg.DIV):
    def __init__(self, content, panelid, tabid, selected):
        super().__init__(
            content,
            id=panelid,
            aria_labelledby=tabid,
            role="tabpanel",
            aria_hidden=hg.If(selected, "false", "true"),
            hidden=hg.If(selected, False, True),
        )


class Tab(typing.NamedTuple):
    label: typing.Any
    content: typing.Any


class Tabs(hg.DIV):
    def __init__(
        self,
        *tabs,
        container=False,
        tabpanel_attributes=None,
        labelcontainer_attributes=None,
        **attributes,
    ):
        tabpanel_attributes = collections.defaultdict(str, tabpanel_attributes or {})
        labelcontainer_attributes = collections.defaultdict(
            str, labelcontainer_attributes or {}
        )

        self.tablabels = hg.UL(
            _class="bx--tabs__nav bx--tabs__nav--hidden", style="flex-wrap: wrap;"
        )
        labelcontainer_attributes["_class"] += " bx--tabs" + (
            " bx--tabs--container" if container else ""
        )
        self.labelcontainer = hg.DIV(
            hg.DIV(
                hg.A(
                    href="javascript:void(0)",
                    _class="bx--tabs-trigger-text",
                    tabindex=-1,
                ),
                _class="bx--tabs-trigger",
                style="display: none",
                tabindex=0,
            ),
            self.tablabels,
            data_tabs=True,
            **hg.merge_html_attrs(
                {
                    "onload": "if( $('.bx--tabs__nav-item--selected', this) == null ) "
                    "(new CarbonComponents.Tab(this)).setActive($('.bx--tabs__nav-item', this))",
                },
                labelcontainer_attributes,
            ),
        )
        tabpanel_attributes["_class"] += " bx--tab-content"
        self.tabpanels = hg.DIV(**tabpanel_attributes)

        firsttab = None
        for i, (label, content) in enumerate(tabs):
            tabid = f"tab-{slugify(label)}-{i}"
            panelid = f"panel-{slugify(label)}-{i}"
            if firsttab is None:
                firsttab = tabid
            self.tablabels.append(
                TabLabel(
                    label,
                    tabid,
                    panelid,
                    HasBasxBreadCookieValue("selected-tab", tabid, firsttab),
                )
            )
            self.tabpanels.append(
                TabPanel(
                    content,
                    panelid,
                    tabid,
                    HasBasxBreadCookieValue("selected-tab", tabid, firsttab),
                )
            )
        super().__init__(
            self.labelcontainer,
            self.tabpanels,
        )
