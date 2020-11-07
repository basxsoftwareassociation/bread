from ..base import DIV

# Usage: Grid(Row(Col(elem1, elem2), Col(elem3, elem5)))


class Grid(DIV):
    def __init__(self, *args, grid_mode=None, **kwargs):
        """
        grid_mode can be one of None, "narrow", "condensed"
        """
        kwargs["css_class"] = kwargs.get("css_class", "") + " bx--grid"
        if grid_mode is not None:
            kwargs["css_class"] += f" bx--grid-{grid_mode}"
        super().__init__(*args, **kwargs)


class Row(DIV):
    def __init__(self, *args, **kwargs):
        kwargs["css_class"] = kwargs.get("css_class", "") + " bx--row"
        super().__init__(*args, **kwargs)


class Col(DIV):
    def __init__(self, *args, breakpoint=None, width=None, **kwargs):
        """
        breakpoint: Can be one of "sm", "md", "lg", "xlg", "max"
        """
        colclass = "bx--col"
        if breakpoint is not None:
            assert width is not None, "When breakpoint is given, width is also required"
            colclass += f"-{breakpoint}-{width}"
        kwargs["css_class"] = kwargs.get("css_class", "") + f" {colclass}"
        super().__init__(*args, **kwargs)
