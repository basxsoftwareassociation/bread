from typing import Any, Optional

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


class ExpandableTile(hg.BaseElement):
    """
    Expandable tiles are helpful for hiding and showing large amounts of content to a user.
    When expanded, tiles push content down the page. They allow the user to specifically
    focus on featured content while having access to the rest of the information.
    Expandable tiles can contain internal CTAs (like links to docs) if they are given
    their own click targets and the click target is reduced to only the chevron icon.

    More information: https://www.carbondesignsystem.com/components/tile/usage#expandable
    Demo: https://the-carbon-components.netlify.app/?nav=tile
    """

    def __init__(
        self,
        above: Any,
        below: Any,
        above_attrs: Optional[dict] = None,
        below_attrs: Optional[dict] = None,
        **attributes
    ):
        """
        Parameters
        ----------
        above : Any
            the primary content of the tile that is not hidden under the fold
        below : Any
            the hidden content that only visible when user click to unfold the tile
        above_attrs : dict, optional
            dict representing the specific HTML attributes for the visible element
            container within the above parameter,
            for example, {'style': 'height: 400px'} is usually used if you do not
            want the height to depend on the content inside.
        below_attrs : dict, optional
            dict representing the specific HTML attributes for the hidden element
            container within the below parameter,
            for example, {'style': 'height: 400px'} is usually used if you do not
            want the height to depend on the content inside.
        **attributes : optional
            keyword arguments representing the specific HTML attributes for the tile
        """
        expandable_tile_attrs = {
            "_class": "bx--tile bx--tile--expandable",
            "data_tile": "expandable",
            "tabindex": "0",
        }
        hg.merge_html_attrs(attributes, expandable_tile_attrs)

        above_attrs = above_attrs or {}
        hg.merge_html_attrs(
            above_attrs,
            {"data_tile_atf": True, "_class": "bx--tile-content__above-the-fold"},
        )

        below_attrs = below_attrs or {}
        hg.merge_html_attrs(below_attrs, {"_class": "bx--tile-content__below-the-fold"})

        super().__init__(
            hg.BUTTON(
                hg.DIV(
                    Icon("chevron--down", size="16"),
                    _class="bx--tile__chevron",
                ),
                hg.DIV(
                    hg.SPAN(
                        above,
                        **above_attrs,
                    ),
                    hg.SPAN(
                        below,
                        **below_attrs,
                    ),
                    _class="bx--tile-content",
                ),
                onload=hg.format(
                    (
                        "let thisTile=this;"
                        "window.setExpandableTileMaxHeight(thisTile);"
                    ),
                    autoescape=False,
                ),
                **attributes,
            ),
        )
