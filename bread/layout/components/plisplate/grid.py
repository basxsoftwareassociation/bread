import plisplate


class Grid(plisplate.DIV):
    def __init__(self, *children, grid_mode=None, **attributes):
        """
        grid_mode can be one of None, "narrow", "condensed", "full-width"
        """
        attributes["_class"] = attributes.get("_class", "") + " bx--grid"
        if grid_mode is not None:
            attributes["_class"] += f" bx--grid-{grid_mode}"
        super().__init__(*children, **attributes)


class Row(plisplate.DIV):
    def __init__(self, *children, **attributes):
        attributes["_class"] = attributes.get("_class", "") + " bx--row"
        super().__init__(*children, **attributes)


class Col(plisplate.DIV):
    def __init__(self, *children, breakpoint=None, width=None, **attributes):
        """
        breakpoint: Can be one of "sm", "md", "lg", "xlg", "max"
        """
        colclass = "bx--col"
        if breakpoint is not None:
            assert width is not None, "When breakpoint is given, width is also required"
            colclass += f"-{breakpoint}-{width}"
        attributes["_class"] = attributes.get("_class", "") + f" {colclass}"
        super().__init__(*children, **attributes)
