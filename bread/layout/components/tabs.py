import collections

import htmlgenerator as hg
from django.utils.text import slugify


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
                aria_selected="true" if selected else "false",
                role="tab",
                onclick="window.localStorage.setItem('selected_tab', this.id)",
            ),
            _class="bx--tabs__nav-item"
            + (" bx--tabs__nav-item--selected" if selected else ""),
            data_target="#" + panelid,
            aria_selected="true" if selected else "false",
            role="tab",
        )


class TabPanel(hg.DIV):
    def __init__(self, content, panelid, tabid, selected):
        super().__init__(
            content,
            id=panelid,
            aria_labelledby=tabid,
            role="tabpanel",
            aria_hidden="false" if selected else "true",
            hidden=not selected,
        )


Tab = collections.namedtuple("Tab", "label content")


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

        self.tablabels = hg.UL(_class="bx--tabs__nav bx--tabs__nav--hidden")
        labelcontainer_attributes["class"] += "bx--tabs" + (
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
            **labelcontainer_attributes,
            onload="if(window.localStorage.getItem('selected_tab')) $('#' + window.localStorage.getItem('selected_tab')).click();",
        )
        tabpanel_attributes["_class"] += " bx--tab-content"
        self.tabpanels = hg.DIV(**tabpanel_attributes)

        for i, (label, content) in enumerate(tabs):
            tabid = f"tab-{slugify(label)}-{i}"
            panelid = f"panel-{slugify(label)}-{i}"
            self.tablabels.append(TabLabel(label, tabid, panelid, i == 0))
            self.tabpanels.append(TabPanel(content, panelid, tabid, i == 0))
        super().__init__(
            self.labelcontainer,
            self.tabpanels,
            **attributes,
        )
