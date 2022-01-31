import collections

import htmlgenerator as hg
from django.utils.translation import gettext_lazy as _

from bread.layout.components import button, grid, modal, tabs, tile

LOREMS = (
    (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore "
        "magna aliqua. Est lorem ipsum dolor sit amet consectetur adipiscing. Sit amet mattis vulputate enim nulla "
        "aliquet porttitor lacus luctus. Elit ullamcorper dignissim cras tincidunt. Sed risus pretium quam vulputate "
        "dignissim. Quisque sagittis purus sit amet volutpat consequat mauris nunc congue. In eu mi bibendum neque "
        "egestas. Nibh tortor id aliquet lectus proin. Egestas purus viverra accumsan in nisl. Egestas maecenas "
        "pharetra convallis posuere."
    ),
    (
        "Tincidunt augue interdum velit euismod in pellentesque massa. Et malesuada fames ac turpis egestas integer. "
        "Scelerisque varius morbi enim nunc faucibus a pellentesque. Tincidunt vitae semper quis lectus. Nisi "
        "scelerisque eu ultrices vitae auctor eu augue. Fermentum posuere urna nec tincidunt praesent. Odio tempor "
        "orci dapibus ultrices in. Risus commodo viverra maecenas accumsan lacus vel facilisis volutpat est. Lectus "
        "magna fringilla urna porttitor. Adipiscing vitae proin sagittis nisl rhoncus mattis. Consequat id porta nibh "
        "venenatis cras. Urna id volutpat lacus laoreet non curabitur gravida arcu ac."
    ),
    (
        "At ultrices mi tempus imperdiet nulla malesuada pellentesque elit eget. Imperdiet massa tincidunt nunc "
        "pulvinar sapien et ligula ullamcorper malesuada. Mollis nunc sed id semper risus. Erat nam at lectus urna "
        "duis convallis convallis tellus id. Urna condimentum mattis pellentesque id nibh tortor id aliquet. Diam ut "
        "venenatis tellus in metus vulputate eu scelerisque felis. Cursus vitae congue mauris rhoncus. Quis viverra "
        "nibh cras pulvinar mattis nunc sed blandit libero. Imperdiet proin fermentum leo vel. Tincidunt augue "
        "interdum velit euismod in pellentesque massa placerat duis. Pellentesque eu tincidunt tortor aliquam nulla "
        "facilisi."
    ),
    (
        "Interdum varius sit amet mattis vulputate enim. Dolor sit amet consectetur adipiscing elit ut aliquam purus. "
        "Nulla facilisi etiam dignissim diam quis enim. Non odio euismod lacinia at quis risus sed vulputate. Felis "
        "donec et odio pellentesque diam. Sit amet volutpat consequat mauris nunc congue nisi vitae. Elementum tempus "
        "egestas sed sed risus pretium. Lacus sed turpis tincidunt id aliquet risus feugiat. Sed id semper risus in "
        "hendrerit gravida. Habitasse platea dictumst quisque sagittis. In iaculis nunc sed augue. Semper auctor neque "
        "vitae tempus quam pellentesque. Eu lobortis elementum nibh tellus. Amet justo donec enim diam vulputate. Sit "
        "amet commodo nulla facilisi. Laoreet id donec ultrices tincidunt arcu non sodales. Integer eget aliquet nibh "
        "praesent. Feugiat vivamus at augue eget arcu dictum varius duis.",
    ),
    (
        "Enim nunc faucibus a pellentesque sit amet porttitor eget dolor. Adipiscing elit pellentesque habitant morbi "
        "tristique senectus. Sed egestas egestas fringilla phasellus faucibus scelerisque eleifend donec. Imperdiet "
        "sed euismod nisi porta lorem mollis aliquam ut porttitor. Nunc vel risus commodo viverra maecenas accumsan. "
        "Gravida dictum fusce ut placerat orci. Ac turpis egestas integer eget aliquet nibh. Aliquet risus feugiat in ante metus dictum at tempor. Viverra vitae congue eu consequat ac. Quisque sagittis purus sit amet volutpat consequat mauris. Nunc sed blandit libero volutpat sed. Vel pretium lectus quam id leo in. Nisi vitae suscipit tellus mauris a diam maecenas sed. Enim sit amet venenatis urna cursus eget nunc. Odio aenean sed adipiscing diam donec adipiscing tristique. Vivamus at augue eget arcu dictum varius. Feugiat in ante metus dictum at tempor commodo ullamcorper a.",
    ),
)


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
        )

    return ret


def table_of_contents_from_cls(*classes):
    modules = collections.defaultdict(list)
    for cls in classes:
        module_name = cls.__module__.split(".")[-1]
        modules[cls.__module__].append(
            (f"{module_name}-{cls.__name__.lower()}", cls.__name__)
        )

    ret = []
    for module in modules:
        name = module.split(".")[-1]
        ret.extend(((name, module), modules[module]))

    return table_of_contents(ret)


def section_header(header):
    return hg.BaseElement(
        hg.A(name=header.lower()),
        hg.H1(header, style="margin-top: 6rem;"),
        hg.HR(),
    )


def section(cls, *content):
    module_name = cls.__module__.split(".")[-1]

    return hg.BaseElement(
        hg.A(name=f"{module_name}-{cls.__name__.lower()}"),
        hg.H6(cls.__module__, style="margin-top: 2rem;"),
        hg.H4(cls.__name__, style="margin-bottom: 1.5rem;"),
        hg.PRE(cls.__doc__, style="margin-bottom: 1rem;"),
        *content,
    )


def layout():
    return hg.BaseElement(
        table_of_contents_from_cls(
            grid.Grid,
            grid.Row,
            grid.Col,
            tabs.Tabs,
            modal.Modal,
            tile.Tile,
            tile.ExpandableTile,
        ),
        _grid_py(),
        _tabs_py(),
        _modal_py(),
        _tile_py(),
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
        section_header("Grid"),
        section(
            grid.Grid,
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
            grid.Col,
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
                        "Each column is assigned their minimum possible width. If widths are getting less than the ",
                        "minimum width, the rightmost columns will fall as a new row instead. You can learn more ",
                        "about possible widths (number of columns) ",
                        hg.A(
                            "here",
                            href="https://www.carbondesignsystem.com/guidelines/2x-grid/overview/#breakpoints",
                            rel="noreferrer noopener",
                            target="_blank",
                        ),
                        ". You can also resize the window (or, alternatively, zoom in-out) to see how columns will ",
                        "rearrange.",
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


def _tabs_py():
    def sample_tabs(*tabnames):
        return tuple(
            tabs.Tab(
                f"Tab {tabname}",
                hg.BaseElement(
                    hg.P(
                        f"This is the content within tab {tabname}.",
                        style="margin-bottom: 0.5rem;",
                    ),
                    hg.P(dummytxt),
                ),
            )
            for tabname, dummytxt in zip(tabnames, LOREMS)
        )

    return hg.BaseElement(
        section_header("Tabs"),
        section(
            tabs.Tabs,
            grid.Row(
                # Use different tab name to avoid the tab switching confusion.
                grid.Col(
                    tile.Tile(
                        hg.H4("container=False (default)"),
                        tabs.Tabs(*sample_tabs("1", "2", "3"), container=False),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("container=True"),
                        tabs.Tabs(*sample_tabs("A", "B", "C"), container=True),
                    ),
                ),
            ),
            grid.Row(
                grid.Col(),
            ),
        ),
    )


def _modal_py():
    def gen_sample_modal(size):
        return modal.Modal(
            "Modal Heading",
            hg.Iterator(
                LOREMS,
                "dummy_paragraph",
                hg.P(
                    hg.F(lambda c: c["dummy_paragraph"]),
                    style="margin-bottom: 0.5rem;",
                ),
            ),
            label='Sample Label with size="%s"' % size,
            size=size,
            buttons=(
                button.Button("OK"),
                button.Button("Action 1", buttontype="secondary"),
                hg.If(size != "xs", button.Button("Action 2", buttontype="secondary")),
                button.Button("Cancel", buttontype="danger", data_modal_close=True),
            ),
        )

    sizes = "xs", "sm", "md", "lg"
    sample_modal = tuple((size, gen_sample_modal(size)) for size in sizes)

    return hg.BaseElement(
        section_header("Modal"),
        section(
            modal.Modal,
            hg.Iterator(
                sample_modal,
                "sample_modal",
                hg.F(
                    lambda c: button.Button(
                        'Open a modal of size="%s"' % c["sample_modal"][0],
                        style="margin-right: 1rem;",
                        **c["sample_modal"][1].openerattributes,
                    )
                ),
            ),
            hg.Iterator(
                sample_modal, "sample_modal", hg.F(lambda c: c["sample_modal"][1])
            ),
        ),
    )


def _tile_py():
    return hg.BaseElement(
        section_header("Tile"),
        grid.Row(
            grid.Col(
                section(
                    tile.Tile,
                    tile.Tile(
                        hg.P("This is a content in Tile."),
                        hg.P("Almost everything can be put here."),
                    ),
                ),
            ),
            grid.Col(
                section(
                    tile.ExpandableTile,
                    tile.ExpandableTile(
                        hg.DIV(
                            hg.P(
                                "This is the visible part of ExpandableTile. Click to view the hidden one."
                            ),
                        ),
                        hg.DIV(
                            hg.P("This is a hidden part of ExpandableTile."),
                        ),
                        {"style": "height: 100px;"},
                        {"style": "height: 100px;"},
                    ),
                ),
            ),
        ),
    )
