from typing import Optional, Union

import htmlgenerator as hg

from bread.layout.components.button import Button
from bread.layout.components.icon import Icon


class DefinitionTooltip(hg.DIV):
    # tag = "bx-tooltip-definition"
    pass


class IconTooltip(hg.DIV):
    # tag = "bx-tooltip-icon"
    pass


class InteractiveTooltip(hg.DIV):
    base_class = "bx--tooltip"
    suffix_label = "label"
    suffix_trigger = "trigger"

    def __init__(
        self,
        label: Union[hg.BaseElement, str],
        body: Union[hg.BaseElement, str],
        footer: Optional[Union[hg.BaseElement, str]] = None,
        icon: Union[Icon, str] = "information",
        **attributes,
    ):
        if footer is None:
            footer = hg.BaseElement()

        base_id = hg.html_id(self, self.base_class + "-id")

        label_id = "-".join([base_id, self.suffix_label])
        label_class = "__".join([self.base_class, self.suffix_label])

        trigger_attributes = {
            "aria_expanded": "false",
            "aria_labelledby": label_id,
            "aria_haspopup": "true",
            "data_tooltip_trigger": True,
            "data_tooltip_target": "#" + base_id,
        }

        tooltip_attributes = {
            "_class": self.base_class,
            "id": base_id,
            "aria_hidden": "true",
        }

        if icon is not None:
            if isinstance(icon, str):
                icon = Icon(icon)
            if isinstance(icon, Icon):
                icon.attributes["_class"] = (
                    icon.attributes.get("_class", "") + " bx--btn__icon"
                )

        super().__init__(
            # tooltip label
            hg.DIV(
                label,
                Button(
                    buttontype="ghost",
                    icon=icon,
                    notext=True,
                    small=True,
                    **trigger_attributes,
                ),
                id=label_id,
                _class=label_class,
            ),
            # the real tooltip goes here
            hg.DIV(
                hg.SPAN(_class=self.base_class + "__caret"),
                hg.DIV(body, _class=self.base_class + "__body"),
                hg.DIV(footer, _class=self.base_class + "__footer"),
                hg.SPAN(tabindex="0"),
                tabindex="-1",
                role="dialog",
                aria_describedby=base_id + "__body",
                aria_labelledby=base_id + "__label",
                **tooltip_attributes,
            ),
            **attributes,
        )
