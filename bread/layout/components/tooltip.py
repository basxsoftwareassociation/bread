from typing import Optional, Union

import htmlgenerator as hg

from bread.layout.components.button import Button
from bread.layout.components.icon import Icon
from bread.utils import Link


def _get_icon(icon):
    """Return a proper Icon instance"""
    if isinstance(icon, str):
        icon = Icon(icon, size="16")
    else:
        icon.attributes["_class"] = icon.attributes.get("_class", "") + " bx--btn__icon"
        icon.attributes["width"] = "16"
        icon.attributes["height"] = "16"

    return icon


def _merge_attributes(dest, source):
    """Bring the class in 'source' inte 'dest'"""
    if "_class" in source:
        if source["_class"]:
            dest["_class"] += source["_class"]
        del source["_class"]

    # for other attributes, if there exist on both dicts,
    # just replace them.
    for attr in dest.keys() & source.keys():
        dest[attr] = source[attr]


class DefinitionTooltip(hg.BaseElement):
    """Definition tooltip is for regular use case of tooltip, e.g. giving the user more
    text information about something, like defining a word.

    This works better than the interactive tooltip in regular use cases because
    the info icon used in interactive tooltip can be repetitive when it’s shown several times
    on a page. Definition tooltip does not use any JavaScript.

    Reference: https://the-carbon-components.netlify.app/?nav=tooltip
    """

    def __init__(
        self,
        label: str,
        description: str,
        align: str = "center",
        position: str = "bottom",
        **attributes,
    ):
        """
        Parameters
        ----------
        label : str
            Text to be displayed
        description : str
            One line of string defining the label
        align : str, optional
            Specify where the arrow pointing the icon should align to the text.
            It can be either start, center, or end.
            The default value is 'center'.
        position : str
            Where should the tooltip appear besides the tooltip icon.
            It can be either top, left, right, or bottom.
            The default value is 'bottom'.
        """
        tooltip_attributes = {
            "_class": ("bx--tooltip--definition " "bx--tooltip--a11y "),
            "data_tooltip_definition": True,
        }

        _merge_attributes(tooltip_attributes, attributes)
        asst_txt_id = hg.html_id(self, "bx--tooltip--definition-id")

        super().__init__(
            hg.DIV(
                hg.BUTTON(
                    label,
                    _class=(
                        "bx--tooltip__trigger "
                        "bx--tooltip--a11y "
                        "bx--tooltip__trigger--definition "
                        "bx--tooltip--%s "
                        "bx--tooltip--align-%s"
                    )
                    % (position, align),
                    aria_describedby=asst_txt_id,
                ),
                hg.DIV(
                    description,
                    _class="bx--assistive-text",
                    id=asst_txt_id,
                    role="tooltip",
                ),
                **tooltip_attributes,
            )
        )


class IconTooltip(hg.BaseElement):
    """Icon tooltip is for short single line of text describing an icon. Icon tooltip
    does not use any JavaScript. No label should be added to this variation. If there
    are actions a user can take in the tooltip (e.g. a link or a button),
    use interactive tooltip.

    Reference: https://the-carbon-components.netlify.app/?nav=tooltip
    """

    def __init__(
        self,
        description: str,
        icon: Union[Icon, str] = "information",
        align: str = "center",
        position: str = "bottom",
        **attributes,
    ):
        """
        Parameters
        ----------
        description : str
            One line of string describing an icon.
        icon : Icon, str, optional
            Specify an icon for the tooltip.
            The default value is 'information'.
        align : str, optional
            Specify where the arrow pointing the icon should align to the text.
            It can be either start, center, or end.
            The default value is 'center'.
        position : str
            Where should the tooltip appear besides the tooltip icon.
            It can be either top, left, right, or bottom.
            The default value is 'bottom'.
        """
        tooltip_attributes = {
            "_class": (
                "bx--tooltip__trigger "
                "bx--tooltip--a11y "
                "bx--tooltip--%s "
                "bx--tooltip--align-%s"
            )
            % (position, align),
            "data_tooltip_icon": True,
        }

        _merge_attributes(tooltip_attributes, attributes)
        icon = _get_icon(icon)

        super().__init__(
            hg.BUTTON(
                hg.SPAN(description, _class="bx--assistive-text"),
                icon,
                **tooltip_attributes,
            )
        )


class InteractiveTooltip(hg.BaseElement):
    """Interactive tooltip should be used if there are actions a user can take in
    the tooltip (e.g. a link or a button). For more regular use case, e.g. giving
    the user more text information about something, use definition tooltip or icon
    tooltip.

    Reference: https://the-carbon-components.netlify.app/?nav=tooltip
    """

    base_class = "bx--tooltip"
    suffix_label = "label"

    def __init__(
        self,
        label: Union[hg.BaseElement, str],
        body: str,
        heading: Optional[str] = None,
        link: Optional[Link] = None,
        button: Optional[Button] = None,
        icon: Union[Icon, str] = "information",
        menudirection: str = "bottom",
        **attributes,
    ):
        """
        Parameters
        ----------
        label : str
            Label for a tooltip
        body : str
            The content inside a tooltip
        heading : str, optional
            A heading for a tooltip.
        link : Link, optional
            Bread's Link NamedTuple in case you want to bring users to a specific webpage.
        button : Button, optional
            Insert the Bread's Button onto the tooltip.
        icon : Icon, str, optional
            Specify an icon for the tooltip
            The default value is "information".
        menudirection : str
            Where should the tooltip appear besides the tooltip icon.
            It can be either top, left, right, or bottom.
            The default value is "bottom".
        """
        footer = (
            hg.BaseElement(
                hg.If(bool(link), hg.A(link.label, href=link.href, _class="bx--link")),
                hg.If(bool(button), button),
            )
            if link or button
            else None
        )

        base_id = hg.html_id(self, self.base_class + "-id")
        label_id = "-".join([base_id, self.suffix_label])

        trigger_attributes = {
            "_class": self.base_class + "__trigger",
            "aria_controls": base_id,
            "aria_expanded": "false",
            "aria_haspopup": "true",
            "aria_labelledby": label_id,
            "data_tooltip_target": "#" + base_id,
            "data_tooltip_trigger": True,
        }

        tooltip_attributes = {
            "_class": self.base_class,
            "aria_hidden": "true",
            "data_floating_menu_direction": menudirection,
            "id": base_id,
        }

        tooltip_content_attributes = {
            "_class": self.base_class + "__content",
            "aria_describedby": base_id + "-body",
            "aria_labelledby": label_id,
            "role": "dialog",
            "tabindex": "-1",
        }

        _merge_attributes(tooltip_attributes, attributes)
        icon = _get_icon(icon)

        super().__init__(
            # tooltip label
            hg.DIV(
                label,
                # cannot use bread's Button class because
                # only the class bx--tooltip__trigger can be used
                hg.BUTTON(
                    icon,
                    **trigger_attributes,
                ),
                id=label_id,
                _class=self.base_class + "__label",
            ),
            # the real tooltip goes here
            hg.DIV(
                hg.SPAN(_class=self.base_class + "__caret"),
                hg.DIV(
                    hg.If(
                        bool(heading),
                        hg.H4(
                            heading,
                            id=base_id + "-heading",
                            _class=self.base_class + "__heading",
                        ),
                    ),
                    hg.P(body, id=base_id + "-body"),
                    hg.If(
                        bool(footer),
                        hg.DIV(
                            footer,
                            _class=self.base_class + "__footer",
                        ),
                    ),
                    **tooltip_content_attributes,
                ),
                hg.SPAN(tabindex="0"),
                **tooltip_attributes,
            ),
        )
