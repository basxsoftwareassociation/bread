import htmlgenerator as hg


class Tabs(hg.DIV):
    def __init__(self, *tabs, container=False, **attributes):
        tablabels = hg.DIV(
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
            tablabels.append(
                hg.LI(
                    hg.A(
                        label,
                        tabindex="0",
                        id=tabid,
                        _class="bx--tabs__nav-link",
                        href="javascript:void(0)",
                        aria_controls=panelid,
                    ),
                    _class="bx--tabs__nav-item bx--tabs__nav-item--selected",
                    aria_selected="true",
                    data_target=panelid,
                )
            )
            tabcontents.append(hg.DIV(content, id=panelid, aria_labelledby=tabid))
        super().__init__(
            tablabels,
            tabcontents,
            **attributes,
        )


"""
<div data-tabs class="bx--tabs">
  <ul class="bx--tabs__nav bx--tabs__nav--hidden" role="tablist">
    <li
      class="bx--tabs__nav-item bx--tabs__nav-item--selected "
      data-target=".tab-1-default" role="tab"  aria-selected="true"  >
      <a tabindex="0" id="tab-link-1-default" class="bx--tabs__nav-link" href="javascript:void(0)" role="tab" aria-controls="tab-panel-1-default">Tab label 1</a>
    </li>
    <li
      class="bx--tabs__nav-item "
      data-target=".tab-2-default" role="tab"  >
      <a tabindex="0" id="tab-link-2-default" class="bx--tabs__nav-link" href="javascript:void(0)" role="tab"
        aria-controls="tab-panel-2-default">Tab label 2</a>
    </li>
    <li
      class="bx--tabs__nav-item "
      data-target=".tab-3-default" role="tab"  >
      <a tabindex="0" id="tab-link-3-default" class="bx--tabs__nav-link" href="javascript:void(0)" role="tab"
        aria-controls="tab-panel-3-default">Tab label 3</a>
    </li>
    <li
      class="bx--tabs__nav-item  bx--tabs__nav-item--disabled "
      data-target=".tab-4-default" role="tab"
      aria-disabled="true" >
      <a tabindex="0" id="tab-link-4-default" class="bx--tabs__nav-link" href="javascript:void(0)" role="tab"
        aria-controls="tab-panel-4-default">Tab label 4</a>
    </li>
  </ul>
</div>

<div class="bx--tab-content">
  <div id="tab-panel-1-default" class="tab-1-default" role="tabpanel" aria-labelledby="tab-link-1-default"
    aria-hidden="false" >
    <div>Content for first tab goes here.</div>
  </div>
  <div id="tab-panel-2-default" class="tab-2-default" role="tabpanel" aria-labelledby="tab-link-2-default"
    aria-hidden="true"  hidden>
    <div>Content for second tab goes here.</div>
  </div>
  <div id="tab-panel-3-default" class="tab-3-default" role="tabpanel" aria-labelledby="tab-link-3-default"
    aria-hidden="true"  hidden>
    <div>Content for third tab goes here.</div>
  </div>
  <div id="tab-panel-4-default" class="tab-4-default" role="tabpanel" aria-labelledby="tab-link-4-default"
    aria-hidden="true"  hidden>
    <div>Content for fourth tab goes here.</div>
  </div>
</div>
"""
