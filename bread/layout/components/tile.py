from typing import Any

import htmlgenerator as hg

from bread.layout.components.icon import Icon


class Tile(hg.DIV):
    """
    Tiles are a highly flexible component for displaying a wide variety of content,
    including information, getting started, how-to, next steps, and more.

    More information: https://www.carbondesignsystem.com/components/tile/usage/
    Demo: https://the-carbon-components.netlify.app/?nav=tile
    """

    def __init__(self, *children, **attributes):
        """
        Parameters
        ----------
        *children
            content within the tile
        **attributes : optional
            keyword arguments representing the specific HTML attributes for the tile
        """
        hg.merge_html_attrs(attributes, {"_class": "bx--tile"})
        super().__init__(*children, **attributes)


class ExpandableTile(hg.DIV):
    """
    Expandable tiles are helpful for hiding and showing large amounts of content to a user.
    When expanded, tiles push content down the page. They allow the user to specifically
    focus on featured content while having access to the rest of the information.
    Expandable tiles can contain internal CTAs (like links to docs) if they are given
    their own click targets and the click target is reduced to only the chevron icon.

    More information: https://www.carbondesignsystem.com/components/tile/usage#expandable
    Demo: https://the-carbon-components.netlify.app/?nav=tile
    """

    def __init__(self, header: Any, content: Any, **attributes):
        """
        Parameters
        ----------
        header : Any
            the header of the tile that is not hidden under the fold
        content : Any
            the hidden content that only visible when user click to unfold the tile
        **attributes : optional
            keyword arguments representing the specific HTML attributes for the tile
        """

        super().__init__(
            hg.BUTTON(Icon("chevron--down", size="16"), _class="bx--tile__chevron"),
            hg.DIV(
                hg.SPAN(
                    header,
                    data_tile_atf=True,
                    _class="bx--tile-content__above-the-fold",
                ),
                hg.SPAN(
                    content,
                    _class="bx--tile-content__below-the-fold",
                    onclick="event.stopPropagation();",
                    style="cursor: initial",
                ),
                _class="bx--tile-content",
            ),
            **hg.merge_html_attrs(
                attributes,
                {
                    "_class": "bx--tile bx--tile--expandable",
                    "data_tile": "expandable",
                    "tabindex": "0",
                },
            )
        )
