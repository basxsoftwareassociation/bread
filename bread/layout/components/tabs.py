import htmlgenerator as hg


class Tabs(hg.DIV):
    def __init__(self, *tabs, container=False, **attributes):
        tablabels = hg.DIV(
            hg.DIV(
                hg.A(
                    href="javascript:void(0)",
                    _class="bx--tabs-trigger-text",
                    tabindex=-1,
                ),
                hg.SVG(),
                _class="bx--tabs-trigger",
                style="display: none",
                tabindex=0,
            ),
            hg.UL(_class="bx--tabs__nav bx--tabs__nav--hidden"),
            data_tabs=True,
            _class="bx--tabs" + (" bx--tabs--container" if container else ""),
        )
        tabcontents = hg.DIV(_class="bx--tab-content")

        tabid_template = f"tab-{hg.html_id(self)}-label-%s"
        panelid_template = f"tab-{hg.html_id(self)}-panel-%s"

        for i, (label, content) in enumerate(tabs):
            tabid = tabid_template % i
            panelid = panelid_template % i
            tablabels[1].append(
                hg.LI(
                    hg.A(
                        label,
                        tabindex="0",
                        id=tabid,
                        _class="bx--tabs__nav-link",
                        href="javascript:void(0)",
                        aria_controls=panelid,
                        aria_selected="true" if i == 0 else "false",
                        role="tab",
                    ),
                    _class="bx--tabs__nav-item"
                    + (" bx--tabs__nav-item--selected" if i == 0 else ""),
                    data_target="#" + panelid,
                    aria_selected="true" if i == 0 else "false",
                    role="tab",
                )
            )
            tabcontents.append(
                hg.DIV(
                    content,
                    id=panelid,
                    aria_labelledby=tabid,
                    role="tabpanel",
                    aria_hidden="false" if i == 0 else "true",
                )
            )
        super().__init__(
            tablabels,
            tabcontents,
            **attributes,
        )
