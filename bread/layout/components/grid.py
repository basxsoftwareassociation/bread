import htmlgenerator


class Grid(htmlgenerator.DIV):
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


class Row(htmlgenerator.DIV):
    def __init__(self, *children, gridmode=None, **attributes):
        attributes["_class"] = attributes.get("_class", "") + " bx--row"
        if gridmode is not None:
            attributes["_class"] += f" bx--row--{gridmode}"
        super().__init__(*children, **attributes)


class Col(htmlgenerator.DIV):
    def __init__(self, *children, breakpoint="lg", width=None, **attributes):
        """
        breakpoint: Can be one of "sm", "md", "lg", "xlg", "max"
        """
        colclass = "bx--col"
        if width is not None:
            colclass += f"-{breakpoint}-{width}"
        attributes["_class"] = attributes.get("_class", "") + f" {colclass}"
        super().__init__(*children, **attributes)
