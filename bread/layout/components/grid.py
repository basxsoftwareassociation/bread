import htmlgenerator as hg


class Grid(hg.DIV):
    """
    Grid is a system uses a series of rows, and columns to layout and align content.
    Grid was built with flexbox and is fully responsive based on the IBM Design's 2x Grid System.

    Grid is usually combined with Row and Col, but not Grid itself alone.
    """

    MODES = ("narrow", "condensed", "full-width")

    def __init__(self, *children, gridmode="full-width", gutter=True, **attributes):
        attributes["_class"] = attributes.get("_class", "") + " bx--grid"
        if gridmode is not None:
            if gridmode not in Grid.MODES:
                raise ValueError(f"argument 'gridmode' must be one of {Grid.MODES}")
            attributes["_class"] += f" bx--grid--{gridmode}"
        if not gutter:
            attributes["_class"] += " bx--no-gutter"
        super().__init__(*children, **attributes)


class Row(hg.DIV):
    """
    Row is a container of a series of columns. Row itself can act as an area of columns,
    or as a part of Grid. In other words, Row is not required to be inside a Grid.
    """

    def __init__(self, *children, gridmode=None, **attributes):
        attributes["_class"] = hg.BaseElement(attributes.get("_class", ""), " bx--row")
        if gridmode is not None:
            attributes["_class"] = hg.BaseElement(
                f" bx--row--{gridmode}", attributes["_class"]
            )
        super().__init__(*children, **attributes)


class Col(hg.DIV):
    """
    Col is a container used within Rows. Col can come with both flexible width and fixed one
    by assigning the width property.
    """

    def __init__(self, *children, breakpoint="lg", width=None, **attributes):
        """
        breakpoint: Can be one of "sm", "md", "lg", "xlg", "max"
        """
        colclass = "bx--col"
        if width is not None:
            colclass += f"-{breakpoint}-{width}"
        attributes["_class"] = attributes.get("_class", "") + f" {colclass}"
        super().__init__(*children, **attributes)
