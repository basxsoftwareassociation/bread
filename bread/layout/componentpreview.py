import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.layout.components import button, grid, tile


def table_of_contents(menu_list: list, show_header=True):
    """Generate a table of content to browse within the webpage."""
    ret = hg.UL(
        _class=f"bx--list--unordered {'' if show_header else 'bx--list--nested'}",
    )

    latest_list = hg.LI(_class="bx--list__item")
    for item in menu_list:
        if isinstance(item, list):
            latest_list.append(table_of_contents(item, False))
        else:
            anchor, title = item
            if len(latest_list) > 0:
                ret.append(latest_list)
                latest_list = hg.LI(_class="bx--list__item")
            latest_list.append(hg.A(title, href=f"#{anchor}"))

    if len(ret) < len(menu_list):
        ret.append(latest_list)

    if show_header:
        return grid.Row(
            hg.STYLE(
                hg.mark_safe(
                    """
                    .componentpreview-toc {
                        padding: 2rem;
                        margin-bottom: 2rem;
                    }
                    .componentpreview-toc>ul {
                        margin: 1.75rem 1.5rem;
                    }
                    .componentpreview-toc>ul>::before {
                        display: none;
                    }
                    """
                )
            ),
            grid.Col(
                tile.Tile(
                    hg.H4(_("Table of Contents")),
                    ret,
                    _class="componentpreview-toc",
                ),
                breakpoint="lg",
                width=8,
            ),
            grid.Col(breakpoint="lg", width=8),
            grid.Col(),
        )

    return ret


def section_header(header, anchor):
    return hg.BaseElement(
        hg.A(name=anchor),
        hg.H1(header),
        hg.HR(),
    )


def section(classInstance, anchor, *content):
    return hg.BaseElement(
        hg.If(anchor, hg.A(name=anchor)),
        hg.H6(classInstance.__module__),
        hg.H4(classInstance.__name__, style="margin-bottom: 1.5rem;"),
        hg.PRE(classInstance.__doc__, style="margin-bottom: 1rem;"),
        *content,
    )


def layout():
    return hg.BaseElement(
        table_of_contents(
            [
                ("grid", "bread.layout.components.grid (grid.py)"),
                [
                    ("grid-grid", "Grid"),
                    ("grid-row", "Row"),
                    ("grid-col", "Col"),
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
        section_header("grid.py", "grid"),
        section(
            grid.Grid,
            "grid-grid",
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
        ),
        section(
            grid.Row,
            "grid-row",
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
        ),
        section(
            grid.Row,
            "grid-row",
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
                        ". You can also resize the window to see how columns will rearrange.",
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
        ),
    )
