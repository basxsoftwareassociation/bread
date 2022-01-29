import htmlgenerator as hg

from bread.layout.components import grid, tile


def table_of_contents(anchor_names, prefix=""):
    """Generate a table of content to browse within the webpage."""
    pass


def layout():
    return hg.BaseElement(
        table_of_contents(
            [
                "grid",
                [
                    "grid-grid",
                    "grid-row",
                    "grid-col",
                ],
            ]
        ),
        _grid_py(),
    )


def _grid_py():
    def grid_col_preview(contents, is_short=False, breakpoint="lg", width=None):
        return grid.Col(
            contents,
            style=(
                "align-items: center; "
                "background: #edf5ff; "
                "color: #000000; "
                "display: flex; "
                "justify-content: center; "
                "outline: 1px solid #a6c8ff; "
                "overflow: hidden; "
                "text-align: center; "
            )
            + ("height: 2.5rem; " if is_short else "height: 100px; "),
            breakpoint=breakpoint,
            width=width,
        )

    def grid_content_area_preview(content):
        return hg.DIV(
            content,
            style=(
                "display: flex;"
                "justify-content: center;"
                "align-items: center;"
                "background-color: #9ef0f0;"
                "height: 100px; "
                "text-align: center;"
                "width: 100%; "
            ),
        )

    def row_mode_preview(gridmode):
        return grid.Row(
            hg.Iterator(
                range(4),
                "colindex",
                grid_col_preview(grid_content_area_preview("area")),
            ),
            gridmode=gridmode,
        )

    grid_gutter_preview = hg.BaseElement(
        grid.Row(
            hg.Iterator(
                range(1, 5),
                "colindex",
                grid_col_preview(hg.F(lambda c: str(c["colindex"]) + " of 4")),
            )
        ),
        grid.Row(
            hg.Iterator(
                range(1, 3),
                "colindex",
                grid_col_preview(hg.F(lambda c: str(c["colindex"]) + " of 2")),
            )
        ),
        grid.Row(grid_col_preview("1 of 1")),
    )

    grid_mode_preview = hg.BaseElement(
        grid.Row(
            hg.Iterator(
                range(4),
                "colindex",
                grid_col_preview(grid_content_area_preview("area")),
            )
        ),
        grid.Row(
            hg.Iterator(
                range(2),
                "colindex",
                grid_col_preview(grid_content_area_preview("area")),
            )
        ),
        grid.Row(grid_col_preview(grid_content_area_preview("area"))),
    )

    breakpoints = [
        {
            "name": "sm",
            "size": 320,
            "width": 4,
        },
        {
            "name": "md",
            "size": 672,
            "width": 8,
        },
        {
            "name": "lg",
            "size": 1056,
            "width": 16,
        },
        {
            "name": "xlg",
            "size": 1312,
            "width": 16,
        },
        {
            "name": "max",
            "size": 1584,
            "width": 16,
        },
    ]

    return hg.BaseElement(
        hg.H6("bread.layout.components.grid"),
        hg.H3("Grid", style="margin-bottom: 1.5rem;"),
        hg.PRE(grid.Grid.__doc__, style="margin-bottom: 1rem;"),
        grid.Row(
            grid.Col(
                tile.Tile(
                    hg.H4("gutter=True (default)"),
                    grid.Grid(
                        grid_gutter_preview,
                        gutter=True,
                    ),
                    style="margin-bottom: 1rem;",
                ),
            ),
            grid.Col(
                tile.Tile(
                    hg.H4("gutter=False"),
                    grid.Grid(
                        grid_gutter_preview,
                        gutter=False,
                    ),
                    style="margin-bottom: 1rem;",
                ),
            ),
        ),
        grid.Row(
            grid.Col(
                tile.Tile(
                    hg.H4('gridmode="full-width" (default)'),
                    grid.Grid(
                        grid_mode_preview,
                        gridmode="full-width",
                    ),
                    style="margin-bottom: 1rem;",
                ),
            ),
            grid.Col(
                tile.Tile(
                    hg.H4('gridmode="condensed"'),
                    grid.Grid(
                        grid_mode_preview,
                        gridmode="condensed",
                    ),
                    style="margin-bottom: 1rem;",
                ),
            ),
            grid.Col(
                tile.Tile(
                    hg.H4('gridmode="narrow"'),
                    grid.Grid(
                        grid_mode_preview,
                        gridmode="narrow",
                    ),
                    style="margin-bottom: 1rem;",
                ),
            ),
        ),
        hg.H6("bread.layout.components.grid", style="margin-top: 3rem;"),
        hg.H3("Row", style="margin-bottom: 1.5rem;"),
        hg.PRE(grid.Row.__doc__, style="margin-bottom: 1rem;"),
        grid.Row(
            grid.Col(
                tile.Tile(
                    hg.H4("gridmode=None (default)"),
                    hg.H5('* the same as "full-width"'),
                    row_mode_preview(None),
                    style="margin-bottom: 1rem;",
                ),
            ),
            grid.Col(
                tile.Tile(
                    hg.H4('gridmode="condensed"'),
                    row_mode_preview("condensed"),
                    style="margin-bottom: 1rem;",
                ),
            ),
            grid.Col(
                tile.Tile(
                    hg.H4('gridmode="narrow"'),
                    row_mode_preview("narrow"),
                    style="margin-bottom: 1rem;",
                ),
            ),
        ),
        hg.H6("bread.layout.components.grid", style="margin-top: 3rem;"),
        hg.H3("Col", style="margin-bottom: 1.5rem;"),
        hg.PRE(grid.Col.__doc__, style="margin-bottom: 1rem;"),
        hg.H4(),
        grid.Row(
            grid.Col(
                hg.H4("Flexible width"),
                tile.Tile(
                    hg.H4("width=None (default)"),
                    hg.P(
                        (
                            "Widths are divided equally within the same row regardless of the number of columns "
                            "inside. If the viewport is too narrow, rightmost columns may fall to the new row."
                        ),
                        style="margin-bottom: 2rem;",
                    ),
                    grid.Grid(
                        hg.Iterator(
                            range(8, 3, -1),
                            "rowindex",
                            grid.Row(
                                hg.F(
                                    lambda cout: hg.Iterator(
                                        range(1, cout["rowindex"] + 1),
                                        "colindex",
                                        grid_col_preview(
                                            hg.F(
                                                lambda c: "%d of %d"
                                                % (c["colindex"], c["rowindex"])
                                            ),
                                            is_short=True,
                                        ),
                                    )
                                ),
                            ),
                        ),
                    ),
                    style="margin-bottom: 1rem;",
                ),
            ),
        ),
        grid.Row(
            grid.Col(
                hg.H4("Fixed width"),
                hg.P(
                    "Each column is assigned their minimum possible width. If widths ",
                    "are getting less than the minimum width, the rightmost columns will fall ",
                    "as a new row instead. "
                    "You can learn more about possible widths (number of columns) ",
                    hg.A(
                        "here",
                        href="https://www.carbondesignsystem.com/guidelines/2x-grid/overview/#breakpoints",
                        rel="noreferrer noopener",
                        target="_blank",
                    ),
                    ". You can also resize the window's size to see how columns will rearrange.",
                    style="margin-bottom: 2rem;",
                ),
            ),
        ),
        hg.Iterator(
            breakpoints,
            "bp",
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4(hg.F(lambda c: f'breakpoint="{c["bp"]["name"]}"')),
                        hg.P(
                            hg.F(
                                lambda c: (
                                    f"The minimum viewport width is {c['bp']['size']} px. "
                                    f"The maximum total width for \"{c['bp']['name']}\" is {c['bp']['width']}. "
                                    "Shorter widths of viewport will result in rightmost columns would "
                                    " fall as a new row instead."
                                )
                            ),
                            style="margin-bottom: 2rem;",
                        ),
                        grid.Grid(
                            hg.F(
                                lambda cout: hg.Iterator(
                                    range(cout["bp"]["width"], 0, -1),
                                    "rowindex",
                                    grid.Row(
                                        hg.F(
                                            lambda c: hg.BaseElement(
                                                hg.Iterator(
                                                    range(1, c["rowindex"]),
                                                    "colindex",
                                                    grid_col_preview(
                                                        "width=1",
                                                        is_short=True,
                                                    ),
                                                ),
                                                grid_col_preview(
                                                    "width=%d"
                                                    % (
                                                        c["bp"]["width"]
                                                        - c["rowindex"]
                                                        + 1
                                                    ),
                                                    is_short=True,
                                                    breakpoint=c["bp"]["name"],
                                                    width=c["bp"]["width"]
                                                    - c["rowindex"]
                                                    + 1,
                                                ),
                                            ),
                                        ),
                                    ),
                                )
                            ),
                            style="margin-bottom: 1rem;",
                        ),
                    ),
                ),
                style="margin-bottom: 1rem;",
            ),
        ),
    )
