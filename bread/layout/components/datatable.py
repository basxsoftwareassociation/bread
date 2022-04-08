from typing import Any, Iterable, List, NamedTuple, Optional, Union

import htmlgenerator as hg
from django.db import models
from django.utils.translation import gettext_lazy as _

from bread.utils import filter_fieldlist, pretty_modelname, resolve_modellookup
from bread.utils.links import Link, ModelHref
from bread.utils.urls import link_with_urlparameters

from ..utils import ObjectFieldLabel, ObjectFieldValue, aslink_attributes
from .button import Button
from .icon import Icon
from .overflow_menu import OverflowMenu
from .pagination import Pagination, PaginationConfig
from .search import Search


class DataTable(hg.TABLE):
    """
    A class for displaying a carbon DataTable.

    To give you a simple example, let's say we want to show the table below.

    +-------------+-----------+------------+
    |   Country   | Continent | Population |
    +-------------+-----------+------------|
    | Switzerland |   Europe  |  8,500,000 |
    |   Germany   |   Europe  | 83,000,000 |
    |  Thailand   |    Asia   | 70,000,000 |
    +-------------+-----------+------------+

    You may do it this way

    ```python
    datatable = DataTable(
        columns=[
            DataTableColumn(
                header="Country",
                cell=hg.DIV(hg.C("row.Country")),
            ),
            DataTableColumn(
                header="Continent",
                cell=hg.DIV(hg.C("row.Continent")),
            ),
            DataTableColumn(
                header="Population",
                cell=hg.DIV(hg.C("row.Population")),
            ),
        ],
        row_iterator=[
            {
                "Country": "Switzerland",
                "Continent": "Europe",
                "Population": 8_500_000,
            },
            {
                "Country": "Germany",
                "Continent": "Europe",
                "Population": 83_000_000,
            },
            {
                "Country": "Thailand",
                "Continent": "Asia",
                "Population": 70_000_000,
            },
        ],
    )
    ```

    For readability, we recommend using comprehensions:

    ```python
    headers = ["Country", "Continent", "Population"]
    rows = [
        ["Switzerland", "Europe", 8_500_000],
        ["Germany", "Europe", 83_000_000],
        ["Thailand", "Asia", 70_000_000],
    ]

    datatable = DataTable(
        columns=[
            DataTableColumn(
                header=header,
                cell=hg.DIV(hg.C(f"row.{header}"))
            )
            for header in headers
        ],
        row_iterator=[
            {
                header: content
                for header, content in zip(headers, row)
            }
            for row in rows
        ]
    )
    ```

    There are more ways of using DataTable, which may be added later.
    """

    SPACINGS = ["default", "compact", "short", "tall"]

    def __init__(
        self,
        columns: List["DataTableColumn"],
        row_iterator: Union[hg.Lazy, Iterable, hg.Iterator],
        orderingurlparameter: str = "ordering",
        rowvariable: str = "row",
        spacing: str = "default",
        zebra: bool = False,
        sticky: bool = False,
        **kwargs: Any,
    ):
        """A carbon DataTable element

        :param columns: Column definitions
        :param row_iterator: Iterator which yields row objects. If this is a hg.Iterator instance
                             it will be used for the table body, otherwise a default iterator will
                             be used to render the column cells. This can also be htmlgenerator.Lazy
                             object which returns a Python iterator when beeing evaluated.
        :param rowvariable: Name of the current object passed to childrens context
        :param orderingurlparameter: The name of the GET query parameter which is used to set the
                                     table ordering.
        :param spacing: One of "default", "compact", "short", "tall", according to the carbon styles
        :param zebra: If True alternate row colors
        :param kwargs: HTML element attributes
        """

        self.head = DataTable.headrow(columns, orderingurlparameter)
        if isinstance(row_iterator, hg.Iterator):
            self.iterator = row_iterator
        else:
            self.iterator = hg.Iterator(
                row_iterator, rowvariable, DataTable.row(columns)
            )
        kwargs["_class"] = kwargs.get("_class", "") + " ".join(
            DataTable.tableclasses(spacing, zebra, sticky)
        )
        super().__init__(hg.THEAD(self.head), hg.TBODY(self.iterator), **kwargs)

    def with_toolbar(
        self,
        title: Any,
        helper_text: Any = None,
        primary_button: Optional[Button] = None,
        bulkactions: Iterable[Link] = (),
        pagination_config: Optional[PaginationConfig] = None,
        checkbox_for_bulkaction_name: str = "_selected",
        search_urlparameter: Optional[str] = None,
        settingspanel: Any = None,
    ):
        """
        wrap this datatable with title and toolbar
        title: table title
        helper_text: sub title
        primary_button: bread.layout.button.Button instance
        bulkactions: List of bread.utils.links.Link instances. Will send a post or a get (depending
                     on its "method" attribute) to the target url the sent data will be a form with
                     the selected checkboxes as fields if the head-checkbox has been selected only
                     that field will be selected.
        """
        checkboxallid = f"datatable-check-{hg.html_id(self)}"
        header: List[hg.BaseElement] = [
            hg.H4(title, _class="bx--data-table-header__title")
        ]
        if helper_text is not None:
            header.append(
                hg.P(helper_text, _class="bx--data-table-header__description")
            )
        bulkactionlist = []
        for link in bulkactions:
            bulkactionlist.append(
                Button(
                    link.label,
                    icon=link.iconname,
                    onclick=hg.BaseElement(
                        "submitbulkaction(this.closest('[data-table]'), '",
                        link.href,
                        "', method='GET')",
                    ),
                ),
            )

        if bulkactions:
            self.head.insert(
                0,
                hg.TH(
                    hg.INPUT(
                        data_event="select-all",
                        id=checkboxallid,
                        _class="bx--checkbox",
                        type="checkbox",
                        name=checkbox_for_bulkaction_name,
                        value="all",
                    ),
                    hg.LABEL(
                        _for=checkboxallid,
                        _class="bx--checkbox-label",
                    ),
                    _class="bx--table-column-checkbox",
                ),
            )
            self.iterator[0].insert(
                0,
                hg.TD(
                    hg.INPUT(
                        data_event="select",
                        id=hg.BaseElement(
                            checkboxallid,
                            "-",
                            hg.C(self.iterator.loopvariable + "_index"),
                        ),
                        _class="bx--checkbox",
                        type="checkbox",
                        name=checkbox_for_bulkaction_name,
                        value=hg.If(
                            hg.F(
                                lambda c: hasattr(c[self.iterator.loopvariable], "pk")
                            ),
                            hg.C(f"{self.iterator.loopvariable}.pk"),
                            hg.C(f"{self.iterator.loopvariable}_index"),
                        ),
                    ),
                    hg.LABEL(
                        _for=hg.BaseElement(
                            checkboxallid,
                            "-",
                            hg.C(self.iterator.loopvariable + "_index"),
                        ),
                        _class="bx--checkbox-label",
                        aria_label="Label name",
                    ),
                    _class="bx--table-column-checkbox",
                ),
            )

        return hg.DIV(
            hg.DIV(*header, _class="bx--data-table-header"),
            hg.SECTION(
                hg.DIV(
                    hg.DIV(
                        *(
                            bulkactionlist
                            + [
                                Button(
                                    _("Cancel"),
                                    data_event="action-bar-cancel",
                                    _class="bx--batch-summary__cancel",
                                )
                            ]
                        ),
                        _class="bx--action-list",
                    ),
                    hg.DIV(
                        hg.P(
                            hg.SPAN(0, data_items_selected=True),
                            _(" items selected"),
                            _class="bx--batch-summary__para",
                        ),
                        _class="bx--batch-summary",
                    ),
                    _class="bx--batch-actions",
                    aria_label=_("Table Action Bar"),
                ),
                hg.DIV(
                    searchbar(search_urlparameter) if search_urlparameter else None,
                    Button(
                        icon="settings--adjust",
                        buttontype="ghost",
                        onclick="""
let settings = this.parentElement.parentElement.parentElement.querySelector('.settingscontainer');
settings.style.display = settings.style.display == 'block' ? 'none' : 'block';
event.stopPropagation()""",
                    )
                    if settingspanel
                    else None,
                    primary_button or None,
                    _class="bx--toolbar-content",
                ),
                _class="bx--table-toolbar",
            ),
            hg.DIV(
                hg.DIV(
                    hg.DIV(
                        settingspanel,
                        _class="bx--tile raised",
                        style="margin: 0; padding: 0",
                    ),
                    _class="settingscontainer",
                    style="position: absolute; z-index: 999; right: 0; display: none",
                    onload="document.addEventListener('click', (e) => {this.style.display = 'none'})",
                ),
                style="position: relative",
                onclick="event.stopPropagation()",
            ),
            self,
            Pagination.from_config(pagination_config) if pagination_config else None,
            _class="bx--data-table-container",
            data_table=True,
        )

    @staticmethod
    def from_queryset(
        queryset,
        # column behaviour
        columns: Iterable[Union[str, "DataTableColumn"]] = (),
        prevent_automatic_sortingnames=False,
        # row behaviour
        rowvariable="row",
        rowactions: Iterable[Link] = (),
        rowactions_dropdown=False,
        rowclickaction=None,
        # bulkaction behaviour
        bulkactions: Iterable[Link] = (),
        checkbox_for_bulkaction_name="_selected",
        # toolbar configuration
        title=None,
        primary_button: Optional[Button] = None,
        settingspanel: Any = None,
        pagination_config: Optional[PaginationConfig] = None,
        search_urlparameter: Optional[str] = None,
        model=None,  # required if queryset is Lazy
        **kwargs,
    ):
        """TODO: Write Docs!!!!
        Yeah yeah, on it already...

        :param settingspanel: A panel which will be opened when clicking on the
                              "Settings" button of the datatable, usefull e.g.
                              for showing filter options. Currently only one
                              button and one panel are supported. More buttons
                              and panels could be interesting but may to over-
                              engineered because it is a rare case and it is not
                              difficutl to add another button by modifying the
                              datatable after creation.
        """
        if not isinstance(queryset, hg.Lazy):
            model = queryset.model
        if model is None:
            raise ValueError(
                "Argument for 'model' must be given if 'queryset' is of type hg.Lazy"
            )

        columns = columns or filter_fieldlist(model, ["__all__"])

        title = title or pretty_modelname(model, plural=True)

        if primary_button is None:
            primary_button = Button.from_link(
                Link(
                    href=ModelHref(model, "add"),
                    label=_("Add %s") % pretty_modelname(model),
                    permissions=[
                        f"{model._meta.app_label}.add_{model._meta.model_name}"
                    ],
                ),
                icon=Icon("add", size=20),
            )

        if rowactions_dropdown:
            objectactions_menu: hg.HTMLElement = OverflowMenu(
                rowactions,
                flip=True,
                item_attributes={"_class": "bx--table-row--menu-option"},
            )
        else:
            objectactions_menu = hg.DIV(
                hg.Iterator(
                    rowactions,
                    "link",
                    hg.F(
                        lambda c: Button.from_link(
                            c["link"],
                            notext=True,
                            small=True,
                            buttontype="ghost",
                            _class="bx--overflow-menu",
                        )
                        if isinstance(c["link"], Link)
                        else c["link"]
                    ),
                ),
                style="display: flex; justify-content: flex-end;",
            )

        column_definitions: List[DataTableColumn] = []
        for col in columns:
            if not (isinstance(col, DataTableColumn) or isinstance(col, str)):
                raise ValueError(
                    f"Argument 'columns' needs to be of a List[str] or a List[DataTableColumn], but found {col}"
                )
            td_attributes: Optional[dict] = None
            if rowclickaction and getattr(col, "enable_row_click", True):
                assert isinstance(
                    rowclickaction, Link
                ), "rowclickaction must be of type Link"
                td_attributes = {
                    **aslink_attributes(rowclickaction.href),
                    **(rowclickaction.attributes or {}),
                }
            # convert simple string (modelfield) to column definition
            if isinstance(col, str):

                col = DataTableColumn.from_modelfield(
                    col,
                    model,
                    prevent_automatic_sortingnames,
                    rowvariable,
                    td_attributes=td_attributes,
                )
            else:
                if td_attributes:
                    col = col._replace(td_attributes=td_attributes)  # type: ignore

            column_definitions.append(col)

        return DataTable(
            column_definitions
            + (
                [
                    DataTableColumn(
                        "",
                        objectactions_menu,
                        td_attributes=hg.F(
                            lambda c: {
                                "_class": "bx--table-column-menu"
                                if rowactions_dropdown
                                else ""
                            }
                        ),
                        th_attributes=hg.F(
                            lambda c: {"_class": "bx--table-column-menu"}
                        ),
                    )
                ]
                if rowactions
                else []
            ),
            # querysets are cached, the call to all will make sure a new query is used in every request
            hg.F(lambda c: queryset),
            **kwargs,
        ).with_toolbar(
            title,
            helper_text=hg.format(
                "{} {}",
                hg.F(
                    lambda c: len(hg.resolve_lazy(queryset, c))
                    if pagination_config is None
                    else pagination_config.paginator.count
                ),
                model._meta.verbose_name_plural,
            ),
            primary_button=primary_button,
            bulkactions=bulkactions,
            pagination_config=pagination_config,
            checkbox_for_bulkaction_name=checkbox_for_bulkaction_name,
            search_urlparameter=search_urlparameter,
            settingspanel=settingspanel,
        )

    # A few helper classes to make the composition in the __init__ method easier

    @staticmethod
    def headrow(columns, orderingurlparameter):
        """Returns the head-row element based on the specified columns"""
        return hg.TR(*[c.as_header_cell(orderingurlparameter) for c in columns])

    @staticmethod
    def row(columns):
        """Returns a row element based on the specified columns"""
        return hg.TR(
            *[hg.TD(col.cell, lazy_attributes=col.td_attributes) for col in columns]
        )

    @staticmethod
    def tableclasses(spacing, zebra, sticky):
        if spacing not in DataTable.SPACINGS:
            raise ValueError(
                f"argument 'spacin' is {spacing} but needs to be one of {DataTable.SPACINGS}"
            )
        classes = ["bx--data-table bx--data-table--sort"]
        if spacing != "default":
            classes.append(f" bx--data-table--{spacing}")
        if zebra:
            classes.append(" bx--data-table--zebra")
        if sticky:
            classes.append(" bx--data-table--sticky-header")
        return classes


class DataTableColumn(NamedTuple):
    header: Any
    cell: Any
    sortingname: Optional[str] = None
    enable_row_click: bool = True
    th_attributes: Optional[Union[hg.F, dict]] = None
    td_attributes: Optional[Union[hg.F, dict]] = None

    @staticmethod
    def from_modelfield(
        col,
        model,
        prevent_automatic_sortingnames=False,
        rowvariable="row",
        th_attributes=None,
        td_attributes=None,
    ) -> "DataTableColumn":
        return DataTableColumn(
            ObjectFieldLabel(col, model),
            ObjectFieldValue(col, rowvariable),
            sortingname_for_column(model, col)
            if not prevent_automatic_sortingnames
            else None,
            th_attributes=th_attributes,
            td_attributes=td_attributes,
        )

    def as_header_cell(self, orderingurlparameter="ordering"):
        headcontent = hg.DIV(self.header, _class="bx--table-header-label")
        if self.sortingname:
            headcontent = hg.BUTTON(
                headcontent,
                Icon("arrow--down", _class="bx--table-sort__icon", size=16),
                Icon(
                    "arrows--vertical",
                    _class="bx--table-sort__icon-unsorted",
                    size=16,
                ),
                _class=hg.BaseElement(
                    "bx--table-sort ",
                    sortingclass_for_column(orderingurlparameter, self.sortingname),
                ),
                data_event="sort",
                **sortinglink_for_column(orderingurlparameter, self.sortingname),
            )
        return hg.TH(headcontent, lazy_attributes=self.th_attributes)


def searchbar(search_urlparameter: str):
    """
    Creates a searchbar element for datatables to submit an entered search
    term via a GET url parameter
    """
    searchinput = Search(
        widgetattributes={
            "autofocus": True,
            "name": search_urlparameter,
            "value": hg.F(lambda c: c["request"].GET.get(search_urlparameter, "")),
            "onfocus": "this.setSelectionRange(this.value.length, this.value.length);",
        }
    )
    searchinput.close_button.attributes[
        "onclick"
    ] = "this.closest('form').querySelector('input').value = ''; this.closest('form').submit()"

    return hg.DIV(
        hg.FORM(
            searchinput,
            hg.Iterator(
                hg.C("request").GET.lists(),
                "urlparameter",
                hg.If(
                    hg.F(lambda c: c["urlparameter"][0] != search_urlparameter),
                    hg.Iterator(
                        hg.C("urlparameter")[1],
                        "urlvalue",
                        hg.INPUT(
                            type="hidden",
                            name=hg.C("urlparameter")[0],
                            value=hg.C("urlvalue"),
                        ),
                    ),
                ),
            ),
            method="GET",
        ),
        _class="bx--toolbar-search-container-persistent",
    )


def sortingclass_for_column(orderingurlparameter, columnname):
    def extracturlparameter(context):
        value = context["request"].GET.get(orderingurlparameter, "")
        if not value:
            return ""
        if value == columnname:
            return "bx--table-sort--active"
        if value == "-" + columnname:
            return "bx--table-sort--active bx--table-sort--ascending"
        return ""

    return hg.F(extracturlparameter)


def sortingname_for_column(model, column):
    components = []
    for field in resolve_modellookup(model, column):
        if hasattr(field, "sorting_name"):
            components.append(field.sorting_name)
        elif isinstance(field, (models.Field, models.ForeignObjectRel)):
            components.append(field.name)
        else:
            return None
    return "__".join(components)


def sortinglink_for_column(orderingurlparameter, columnname):
    ORDERING_VALUES = {
        None: columnname,
        columnname: "-" + columnname,
        "-" + columnname: None,
    }

    def extractsortinglink(context):
        currentordering = context["request"].GET.get(orderingurlparameter, None)
        nextordering = ORDERING_VALUES.get(currentordering, columnname)
        ret = link_with_urlparameters(
            context["request"], **{orderingurlparameter: nextordering}
        )
        # workaround to allow reseting session-stored table state
        if nextordering is None and "?" not in ret:
            ret = ret + "?reset"
        return ret

    return aslink_attributes(hg.F(extractsortinglink))
