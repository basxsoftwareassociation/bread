import collections
import uuid

import htmlgenerator as hg
from django import forms
from django.contrib import messages
from django.contrib.messages.storage.base import Message as DjangoMessage
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _

from ..utils import Link
from .components import (
    button,
    content_switcher,
    datatable,
    grid,
    icon,
    loading,
    modal,
    notification,
    overflow_menu,
    pagination,
    progress_indicator,
    search,
    tabs,
    tag,
    tile,
    toggle,
    tooltip,
)
from .components.forms import Form, FormField

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
        "Gravida dictum fusce ut placerat orci. Ac turpis egestas integer eget aliquet nibh. Aliquet risus feugiat in "
        "ante metus dictum at tempor. Viverra vitae congue eu consequat ac. Quisque sagittis purus sit amet volutpat "
        "consequat mauris. Nunc sed blandit libero volutpat sed. Vel pretium lectus quam id leo in. Nisi vitae suscipit "
        "tellus mauris a diam maecenas sed. Enim sit amet venenatis urna cursus eget nunc. Odio aenean sed adipiscing "
        "diam donec adipiscing tristique. Vivamus at augue eget arcu dictum varius. Feugiat in ante metus dictum at "
        "tempor commodo ullamcorper a.",
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


def section_header(header, anchor=None):
    return hg.BaseElement(
        hg.A(name=anchor or header.lower()),
        hg.H1(header, style="margin-top: 6rem;"),
        hg.HR(),
    )


def section(cls, *content):
    module_name = cls.__module__.split(".")[-1]

    return hg.BaseElement(
        hg.A(name=f"{module_name}-{cls.__name__.lower()}"),
        hg.H6(cls.__module__, style="margin-top: 2rem;"),
        hg.H4(cls.__name__, style="margin-bottom: 1.5rem;"),
        hg.PRE(hg.CODE(cls.__doc__), style="margin-bottom: 1rem;"),
        *content,
    )


def layout(request):
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


def informational(request):
    return hg.BaseElement(
        table_of_contents_from_cls(
            icon.Icon,
            tag.Tag,
            loading.Loading,
            progress_indicator.ProgressIndicator,
            progress_indicator.ProgressStep,
            tooltip.DefinitionTooltip,
            tooltip.IconTooltip,
            tooltip.InteractiveTooltip,
            notification.InlineNotification,
            notification.ToastNotification,
        ),
        _icon_py(),
        _tag_py(),
        _loading_py(),
        _progress_indicator_py(),
        _tooltip_py(),
        _notification_py(request),
    )


def interactive(request):
    return hg.BaseElement(
        table_of_contents_from_cls(
            button.Button,
            content_switcher.ContentSwitcher,
            toggle.Toggle,
            overflow_menu.OverflowMenu,
            pagination.Pagination,
            search.Search,
        ),
        _button_py(),
        _content_switcher_py(),
        _toggle_py(),
        _overflow_menu_py(),
        _pagination_py(),
        _searchbar_py(),
    )


def datatable_layout(request):
    return hg.BaseElement(
        table_of_contents(
            [
                ("datatable", "basxbread.layout.components.datatable"),
                [
                    ("datatable-datatable", "DataTable"),
                    [
                        ("datatable-datatable-with_toolbar", "with_toolbar method"),
                    ],
                ],
            ]
        ),
        _datatable_py(),
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
                            style="height: 100px;",
                        ),
                    ),
                ),
            ),
        ),
    )


def _icon_py():
    return hg.BaseElement(
        section_header("Icon"),
        section(
            icon.Icon,
            grid.Row(
                hg.Iterator(
                    ("information", "filter", "email"),
                    "iconname",
                    grid.Col(
                        tile.Tile(
                            hg.H4('name="', hg.C("iconname"), '"'),
                            icon.Icon(hg.C("iconname")),
                        )
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("name=[iconname]"),
                        hg.H6("* required"),
                        hg.P("display the icon corresponding to iconname"),
                    )
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("size=None (default)"),
                        hg.H6('* will be interpreted as size="32" (in pixel)'),
                        icon.Icon("information"),
                        icon.Icon("filter"),
                        icon.Icon("email"),
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4('size="16"'),
                        icon.Icon("information", size="16"),
                        icon.Icon("filter", size="16"),
                        icon.Icon("email", size="16"),
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4('size="64"'),
                        icon.Icon("information", size="64"),
                        icon.Icon("filter", size="64"),
                        icon.Icon("email", size="64"),
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("size=[preferred length]"),
                        hg.P("the width and height of the icon"),
                    )
                ),
            ),
        ),
    )


def _tag_py():
    return hg.BaseElement(
        section_header("Tag"),
        section(
            tag.Tag,
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("can_delete=False (default)"),
                        tag.Tag("image", tag_color="warm-gray"),
                        tag.Tag("document", tag_color="cyan"),
                        tag.Tag("important", tag_color="magenta"),
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("can_delete=True"),
                        tag.Tag("image", can_delete=True, tag_color="warm-gray"),
                        tag.Tag("document", can_delete=True, tag_color="cyan"),
                        tag.Tag("important", can_delete=True, tag_color="magenta"),
                    )
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("tag_color=None (default)"),
                        hg.H6('the same as tag_color="gray"'),
                        tag.Tag("image"),
                    ),
                    breakpoint="lg",
                    width=4,
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4('Possible "tag_color" value'),
                        hg.Iterator(
                            (
                                "red",
                                "magenta",
                                "purple",
                                "blue",
                                "cyan",
                                "teal",
                                "green",
                                "gray",
                                "cool-gray",
                                "warm-gray",
                            ),
                            "tag_color",
                            hg.F(
                                lambda c: tag.Tag(
                                    c["tag_color"], tag_color=c["tag_color"]
                                )
                            ),
                        ),
                    ),
                    breakpoint="md",
                    width=6,
                ),
            ),
        ),
    )


def _loading_py():
    return hg.BaseElement(
        section_header("Loading"),
        section(
            loading.Loading,
            grid.Row(
                grid.Col(tile.Tile(hg.H4("small=False (default)"), loading.Loading())),
                grid.Col(tile.Tile(hg.H4("small=True"), loading.Loading(small=True))),
            ),
        ),
    )


def _progress_indicator_py():
    progressstep_demo_optional = progress_indicator.ProgressIndicator(
        (("Another step", "incomplete"),)
    )
    progressstep_demo_optional.extend(
        (
            progress_indicator.ProgressStep("=False", "complete", optional=False),
            progress_indicator.ProgressStep("=True", "current", optional=True),
        )
    )
    progressstep_demo_disabled = progress_indicator.ProgressIndicator(
        (("Another step", "current"),)
    )
    progressstep_demo_disabled.extend(
        (
            progress_indicator.ProgressStep("=False", "complete", disabled=False),
            progress_indicator.ProgressStep("=True", "incomplete", disabled=True),
        )
    )

    return hg.BaseElement(
        section_header("Progress Indicator", "progress_indicator"),
        section(
            progress_indicator.ProgressIndicator,
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4('Possible "status" value'),
                        hg.H6("* required"),
                        progress_indicator.ProgressIndicator(
                            (status, status)
                            for status in (
                                "warning",
                                "current",
                                "complete",
                                "incomplete",
                            )
                        ),
                    )
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("vertical=False (default)"),
                        progress_indicator.ProgressIndicator(
                            (
                                ("Step 1", "complete"),
                                ("Step 2", "current"),
                                ("Step 3", "incomplete"),
                                ("Step 4", "incomplete"),
                            )
                        ),
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("vertical=True"),
                        progress_indicator.ProgressIndicator(
                            (
                                ("Step 1", "complete"),
                                ("Step 2", "current"),
                                ("Step 3", "incomplete"),
                                ("Step 4", "incomplete"),
                            ),
                            vertical=True,
                        ),
                    )
                ),
            ),
        ),
        section(
            progress_indicator.ProgressStep,
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4('Possible "disabled" value'),
                        hg.H6("* default is False"),
                        progressstep_demo_disabled,
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4('Possible "optional" value'),
                        hg.H6("* default is False"),
                        progressstep_demo_optional,
                    )
                ),
                style="margin-bottom: 2rem;",
            ),
        ),
    )


def _tooltip_py():
    return hg.BaseElement(
        section_header("Tooltip"),
        grid.Row(
            grid.Col(
                section(
                    tooltip.DefinitionTooltip,
                    tile.Tile(
                        hg.DIV(
                            tooltip.DefinitionTooltip(
                                "Definition tooltip (left aligned)",
                                "Brief definition of the dotted, underlined word above.",
                                align="left",
                            )
                        ),
                        hg.DIV(
                            tooltip.DefinitionTooltip(
                                "Definition tooltip (center aligned)",
                                "Brief definition of the dotted, underlined word above.",
                                align="center",
                            )
                        ),
                        hg.DIV(
                            tooltip.DefinitionTooltip(
                                "Definition tooltip (right aligned)",
                                "Brief definition of the dotted, underlined word above.",
                                align="right",
                            )
                        ),
                    ),
                ),
                section(
                    tooltip.IconTooltip,
                    tile.Tile(
                        tooltip.IconTooltip(
                            "Help",
                        ),
                        tooltip.IconTooltip(
                            "Filter",
                            icon=icon.Icon("filter"),
                        ),
                        tooltip.IconTooltip(
                            "Email",
                            icon="email",
                        ),
                    ),
                ),
                section(
                    tooltip.InteractiveTooltip,
                    tile.Tile(
                        tooltip.InteractiveTooltip(
                            label="Tooltip label",
                            body=(
                                _(
                                    "This is some tooltip text. This box shows the maximum amount of text that should "
                                    "appear inside. If more room is needed please use a modal instead."
                                )
                            ),
                            heading="Heading within a Tooltip",
                            button=(button.Button("Button")),
                            link=Link(href="#", label="link"),
                        ),
                    ),
                ),
            ),
        ),
    )


class ToastNotificationPreview(notification.ToastNotification):
    """
    The class that override some attributes of ToastNotification for the purpose of component preview.
    It can be used just like ToastNotification, but some functionalities are disabled.
    """

    def __init__(
        self,
        message,
        details,
        kind="info",
        lowcontrast=False,
        hideclosebutton=False,
        hidetimestamp=False,
        autoremove=4.0,
        **attributes,
    ):
        attributes["style"] = hg.BaseElement(
            ";opacity: 1 !important;animation: unset !important;"
        )
        attributes["onload"] = "//"
        super().__init__(
            message,
            details,
            kind,
            lowcontrast,
            hideclosebutton,
            hidetimestamp,
            autoremove,
            **attributes,
        )


def _notification_py(request):
    class TriggerToastMessageForm(forms.Form):
        displaymessage = forms.BooleanField(
            widget=forms.HiddenInput,
            initial=True,
        )

    form: TriggerToastMessageForm
    received_post = False

    if request.method == "POST":
        form = TriggerToastMessageForm(request.POST)
        if form.is_valid() and "displaymessage" in form.cleaned_data:
            received_post = True
            messages.info(
                request, _("This is a server message in the ToastNotification.")
            )

    if not received_post:
        form = TriggerToastMessageForm()

    # for ToastNotification
    message_obj = (DjangoMessage("20", "This is a detail."),)
    notification_kinds = (
        "error",
        "info",
        "info-square",
        "success",
        "warning",
        "warning-alt",
    )
    toast_kinds = (
        hg.Iterator(
            message_obj,
            "message",
            ToastNotificationPreview(
                "This is a message.", hg.C("message.message"), kind=kind
            ),
        )
        for kind in notification_kinds
    )
    toast_demo_kind = hg.BaseElement(
        *(
            grid.Col(
                tile.Tile(
                    hg.H4(f'kind="{kind}"'),
                    toast,
                ),
                style="margin-bottom: 2rem;",
            )
            for kind, toast in zip(notification_kinds, toast_kinds)
        )
    )

    return hg.BaseElement(
        section_header("Notification"),
        section(
            notification.InlineNotification,
            notification.InlineNotification(
                "This is a message.",
                "This is a detail.",
            ),
            notification.InlineNotification(
                "This is an InlineNotification with an action.",
                "Click the link to learn more.",
                action=(
                    "Learn more",
                    "window.alert('This is a possible onclick event for InlineNotification.');",
                ),
            ),
            grid.Row(
                hg.Iterator(
                    notification_kinds,
                    "kind",
                    grid.Col(
                        tile.Tile(
                            hg.H4('kind="', hg.C("kind"), '"'),
                            notification.InlineNotification(
                                "This is a message.",
                                "This is a detail.",
                                kind=hg.C("kind"),
                            ),
                            breakpoint="md",
                            width=4,
                        ),
                        style="margin-bottom: 2rem;",
                    ),
                ),
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("lowcontrast=False (default)"),
                        notification.InlineNotification(
                            "This is a message.",
                            "This is a detail.",
                            lowcontrast=False,
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("lowcontrast=True"),
                        notification.InlineNotification(
                            "This is a message.",
                            "This is a detail.",
                            lowcontrast=True,
                        ),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("hideclosebutton=False (default)"),
                        notification.InlineNotification(
                            "This is a message.",
                            "This is a detail.",
                            hideclosebutton=False,
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("hideclosebutton=True"),
                        notification.InlineNotification(
                            "This is a message.",
                            "This is a detail.",
                            hideclosebutton=True,
                        ),
                    ),
                ),
            ),
        ),
        section(
            notification.ToastNotification,
            hg.Iterator(
                message_obj,
                "message",
                ToastNotificationPreview(
                    "This is a message.",
                    hg.C("message.message"),
                ),
            ),
            Form(
                form,
                FormField("displaymessage"),
                button.Button(
                    _("Click to see ToastNotification in action"), type="submit"
                ),
            ),
            hg.DIV(
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                toast_demo_kind,
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("lowcontrast=False (default)"),
                        hg.Iterator(
                            message_obj,
                            "message",
                            ToastNotificationPreview(
                                "This is a message.",
                                hg.C("message.message"),
                                lowcontrast=False,
                            ),
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("lowcontrast=True"),
                        hg.Iterator(
                            message_obj,
                            "message",
                            ToastNotificationPreview(
                                "This is a message.",
                                hg.C("message.message"),
                                lowcontrast=True,
                            ),
                        ),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("hideclosebutton=False (default)"),
                        hg.Iterator(
                            message_obj,
                            "message",
                            ToastNotificationPreview(
                                "This is a message.",
                                hg.C("message.message"),
                                hideclosebutton=False,
                            ),
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("hideclosebutton=True"),
                        hg.Iterator(
                            message_obj,
                            "message",
                            ToastNotificationPreview(
                                "This is a message.",
                                hg.C("message.message"),
                                hideclosebutton=True,
                            ),
                        ),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("hidetimestamp=False (default)"),
                        hg.Iterator(
                            message_obj,
                            "message",
                            ToastNotificationPreview(
                                "This is a message.",
                                hg.C("message.message"),
                                hidetimestamp=False,
                            ),
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("hidetimestamp=True"),
                        hg.Iterator(
                            message_obj,
                            "message",
                            ToastNotificationPreview(
                                "This is a message.",
                                hg.C("message.message"),
                                hidetimestamp=True,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def _button_py():
    button_types = (
        "primary",
        "secondary",
        "tertiary",
        "danger",
        "ghost",
    )

    return hg.BaseElement(
        section_header("Button"),
        section(
            button.Button,
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4('buttontype="primary" (default)'),
                        button.Button("Button"),
                    ),
                    breakpoint="md",
                    width="3",
                    style="margin-bottom: 2rem;",
                ),
                hg.Iterator(
                    button_types[1 : len(button_types) - 1],
                    "button_type",
                    grid.Col(
                        tile.Tile(
                            hg.H4('buttontype="', hg.C("button_type"), '"'),
                            hg.F(
                                lambda c: button.Button(
                                    "Button", buttontype=c["button_type"]
                                )
                            ),
                            style="margin-bottom: 2rem;",
                        ),
                        breakpoint="md",
                        width="2",
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4('buttontype="ghost"'),
                        hg.H6("* transparent background"),
                        button.Button("Button", buttontype="ghost"),
                    ),
                    breakpoint="md",
                    width="2",
                    style="margin-bottom: 2rem;",
                ),
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("icon=None (default)"),
                        button.Button("Button", icon=None),
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("icon=[icon name or Icon instance]"),
                        hg.H6('(for example, this one is icon="information")'),
                        button.Button("Button", icon="information"),
                    )
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("notext=False (default)"),
                        button.Button(
                            "Button",
                            icon="information",
                            notext=False,
                        ),
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("notext=True"),
                        button.Button(
                            "Button",
                            icon="information",
                            notext=True,
                        ),
                    )
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("small=False (default)"),
                        button.Button("Button", small=False),
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("small=True"),
                        button.Button("Button", small=True),
                    )
                ),
            ),
        ),
    )


def _content_switcher_py():
    return hg.BaseElement(
        section_header("Content Switcher", "content_switcher"),
        section(
            content_switcher.ContentSwitcher,
            grid.Row(
                grid.Col(
                    tile.Tile(
                        content_switcher.ContentSwitcher(
                            ("Mode 1", {}),
                            ("Mode 2", {}),
                            ("Mode 3", {}),
                        )
                    ),
                    style="margin-bottom: 2rem;",
                )
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("selected=0 (default)"),
                        content_switcher.ContentSwitcher(
                            ("Mode 1", {}),
                            ("Mode 2", {}),
                            ("Mode 3", {}),
                        ),
                    ),
                    style="margin-bottom: 2rem;",
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("selected=1"),
                        content_switcher.ContentSwitcher(
                            ("Mode 1", {}), ("Mode 2", {}), ("Mode 3", {}), selected=1
                        ),
                    ),
                    style="margin-bottom: 2rem;",
                ),
                grid.Col(
                    hg.H4("selected=[index of label]"),
                    hg.P("Make the corresponding button selected by default."),
                    style="margin-bottom: 2rem;",
                ),
            ),
        ),
    )


def _toggle_py():
    return hg.BaseElement(
        section_header("Toggle"),
        section(
            toggle.Toggle,
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4('offlabel=_("Off") (default)'),
                        toggle.Toggle(
                            "Label",
                            widgetattributes={"id": uuid.uuid4()},
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("offlabel=[label when toggle is off]"),
                        toggle.Toggle(
                            "Label",
                            offlabel="I'm really off!",
                            widgetattributes={"id": uuid.uuid4()},
                        ),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4('onlabel=_("On") (default)'),
                        toggle.Toggle(
                            "Label",
                            checked=True,
                            widgetattributes={"id": uuid.uuid4(), "checked": True},
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4(
                            "onlabel=[label when toggle is on]",
                        ),
                        toggle.Toggle(
                            "Label",
                            onlabel="I'm really on!",
                            checked=True,
                            widgetattributes={"id": uuid.uuid4(), "checked": True},
                        ),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("help_text=None (default)"),
                        toggle.Toggle(
                            "Label",
                            widgetattributes={"id": uuid.uuid4()},
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("help_text=[text to describe user]"),
                        toggle.Toggle(
                            "Label",
                            help_text="This is the help text.",
                            widgetattributes={"id": uuid.uuid4()},
                        ),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("errors=None (default)"),
                        toggle.Toggle(
                            "Label",
                            widgetattributes={"id": uuid.uuid4()},
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("errors=[list of requirements]"),
                        toggle.Toggle(
                            "Label",
                            widgetattributes={"id": uuid.uuid4()},
                            errors=[
                                "All required fields must be filled.",
                            ],
                        ),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("disabled=None (default)"),
                        toggle.Toggle(
                            "Label",
                            widgetattributes={"id": uuid.uuid4()},
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("disabled=True"),
                        toggle.Toggle(
                            "Label",
                            widgetattributes={"id": uuid.uuid4()},
                            disabled=True,
                        ),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("required=None (default)"),
                        toggle.Toggle(
                            "Label",
                            widgetattributes={"id": uuid.uuid4()},
                        ),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("required=True"),
                        toggle.Toggle(
                            "Label",
                            widgetattributes={"id": uuid.uuid4()},
                            required=True,
                        ),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
        ),
    )


def _overflow_menu_py():
    default_links = (
        Link(href="#overflow_menu-overflowmenu", label="Link 1", iconname=None),
        Link(
            href="#overflow_menu-overflowmenu", label="Link 2", iconname="information"
        ),
        Link(href="#overflow_menu-overflowmenu", label="Link 3"),
    )
    return hg.BaseElement(
        section_header("Overflow Menu", "overflow_menu"),
        section(
            overflow_menu.OverflowMenu,
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.P(
                            "Click the three dots below to see overflow menu in action."
                        ),
                        overflow_menu.OverflowMenu(links=default_links),
                    ),
                    breakpoint="md",
                    width=2,
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("menuname=None (default)"),
                        overflow_menu.OverflowMenu(links=default_links),
                    ),
                    breakpoint="md",
                    width=3,
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("menuname=[name for menu]"),
                        overflow_menu.OverflowMenu(
                            links=default_links, menuname="This is a menu name."
                        ),
                    ),
                    breakpoint="md",
                    width=3,
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4('direction="bottom" (default)'),
                        overflow_menu.OverflowMenu(links=default_links),
                    ),
                    breakpoint="md",
                    width=2,
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4('direction="right"'),
                        overflow_menu.OverflowMenu(
                            links=default_links, direction="right"
                        ),
                    ),
                    breakpoint="md",
                    width=2,
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4('direction="top"'),
                        overflow_menu.OverflowMenu(
                            links=default_links, direction="top"
                        ),
                    ),
                    breakpoint="md",
                    width=2,
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4('direction="left"'),
                        overflow_menu.OverflowMenu(
                            links=default_links, direction="left"
                        ),
                    ),
                    breakpoint="md",
                    width=2,
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("flip=False (default)"),
                        overflow_menu.OverflowMenu(default_links, flip=False),
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("flip=True"),
                        overflow_menu.OverflowMenu(default_links, flip=True),
                    )
                ),
                style="margin-bottom: 2rem;",
            ),
        ),
    )


def _pagination_py():
    return hg.BaseElement(
        section_header("Pagination"),
        section(
            pagination.Pagination,
            grid.Row(
                grid.Col(
                    tile.Tile(
                        pagination.Pagination(
                            Paginator(range(1, 6), 3),
                            (3, 4),
                        ),
                    ),
                ),
            ),
        ),
    )


def _searchbar_py():
    sizes = "sm", "lg", "xl"
    return hg.BaseElement(
        section_header("Search", "search"),
        section(
            search.Search,
            grid.Row(
                hg.Iterator(
                    sizes[:2],
                    "size",
                    grid.Col(
                        tile.Tile(
                            hg.H4('size="', hg.C("size"), '"'),
                            hg.F(lambda c: search.Search(size=c["size"])),
                        ),
                        breakpoint="md",
                        width=4,
                        style="margin-bottom: 2rem;",
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4('size="xl" (default)'),
                        hg.F(lambda c: search.Search(size="xl")),
                    ),
                    breakpoint="md",
                    width=4,
                    style="margin-bottom: 2rem;",
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("placeholder=None (default)"),
                        search.Search(),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("placeholder=[custom placeholder]"),
                        search.Search(placeholder="I'm the custom placeholder."),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("disabled=False (default)"),
                        search.Search(),
                    ),
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("disabled=True"),
                        search.Search(disabled=True),
                    ),
                ),
                style="margin-bottom: 2rem;",
            ),
        ),
    )


def _datatable_py():
    sample_headers = ["Country", "Continent", "Population"]
    sample_rows = [
        ["Switzerland", "Europe", 8_500_000],
        ["Germany", "Europe", 83_000_000],
        ["Thailand", "Asia", 70_000_000],
    ]

    sample_columns = [
        datatable.DataTableColumn(header=header, cell=hg.DIV(hg.C(f"row.{header}")))
        for header in sample_headers
    ]

    sample_row_iterator = [
        {header: content for header, content in zip(sample_headers, row)}
        for row in sample_rows
    ]

    return hg.BaseElement(
        section_header("Data Table", "datatable"),
        section(
            datatable.DataTable,
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4('spacing="default" (default)'),
                        datatable.DataTable(
                            sample_columns,
                            sample_row_iterator,
                        ),
                    ),
                    breakpoint="md",
                    width=4,
                    style="margin-bottom: 2rem;",
                ),
                hg.Iterator(
                    datatable.DataTable.SPACINGS[1:],
                    "spacing",
                    hg.F(
                        lambda c: hg.BaseElement(
                            grid.Col(
                                tile.Tile(
                                    hg.H4('spacing="', c["spacing"], '"'),
                                    datatable.DataTable(
                                        sample_columns,
                                        sample_row_iterator,
                                        spacing=c["spacing"],
                                    ),
                                ),
                                breakpoint="md",
                                width=4,
                                style="margin-bottom: 2rem;",
                            ),
                        ),
                    ),
                ),
            ),
            grid.Row(
                grid.Col(
                    tile.Tile(
                        hg.H4("zebra=False (default)"),
                        datatable.DataTable(
                            sample_columns,
                            sample_row_iterator,
                            zebra=False,
                        ),
                    )
                ),
                grid.Col(
                    tile.Tile(
                        hg.H4("zebra=True"),
                        datatable.DataTable(
                            sample_columns,
                            sample_row_iterator,
                            zebra=True,
                        ),
                    )
                ),
            ),
        ),
        hg.BaseElement(
            hg.A(name="datatable-datatable-with_toolbar"),
            hg.H6("basxbread.layout.components.datatable", style="margin-top: 2rem;"),
            hg.H4("DataTable.with_toolbar(self)", style="margin-bottom: 1.5rem;"),
            hg.PRE(
                hg.CODE(datatable.DataTable.with_toolbar.__doc__),
                style="margin-bottom: 1rem;",
            ),
            datatable.DataTable(sample_columns, sample_row_iterator).with_toolbar(
                title="Data Table Title",
                helper_text="Data Table Subtitle",
                primary_button=button.Button("Primary Button"),
                bulkactions=[
                    Link(href="#", label="action 1"),
                    Link(href="#", label="action 2"),
                    Link(href="#", label="action 3"),
                ],
            ),
        ),
        section(
            datatable.DataTableColumn,
            hg.P("This is a data table column."),
        ),
    )
