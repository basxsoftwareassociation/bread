from typing import Any, Iterable, List, NamedTuple, Optional, Union

import htmlgenerator as hg
from django.db import models
from django.utils.translation import gettext_lazy as _

from bread.menu import Action
from bread.utils import filter_fieldlist, pretty_modelname, resolve_modellookup
from bread.utils.links import Link
from bread.utils.urls import link_with_urlparameters, reverse_model

from ..base import aslink_attributes, fieldlabel, objectaction
from . import search
from .button import Button
from .icon import Icon
from .overflow_menu import OverflowMenu
from .pagination import Pagination
from .search import Search


class DataTableColumn(NamedTuple):
    header: Any
    cell: Any
    sortingname: Optional[str] = None
    enable_row_click: bool = True
    th_attributes: hg.F = None
    td_attributes: hg.F = None

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
            fieldlabel(model, col),
            hg.C(f"{rowvariable}.{col}"),
            sortingname_for_column(model, col)
            if not prevent_automatic_sortingnames
            else None,
            th_attributes=th_attributes,
            td_attributes=td_attributes,
        )

    def as_header_cell(self, orderingurlparameter="ordering"):
        headcontent = hg.SPAN(self.header, _class="bx--table-header-label")
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
                title=self.header,
                **sortinglink_for_column(orderingurlparameter, self.sortingname),
            )
        return hg.TH(headcontent, lazy_attributes=self.th_attributes)


class DataTable(hg.TABLE):
    SPACINGS = ["default", "compact", "short", "tall"]

    def __init__(
        self,
        columns: List[DataTableColumn],
        row_iterator: Union[hg.Lazy, Iterable, hg.Iterator],
        orderingurlparameter: str = "ordering",
        rowvariable: str = "row",
        spacing: str = "default",
        zebra: bool = False,
        **kwargs: dict,
    ):
        """A carbon DataTable element

        :param columns: Column definitions
        :param row_iterator: Iterator which yields row objects. If this is a hg.Iterator instance it will be used for the table body, otherwise a default Iterator will be used to render the column cells. This can also be htmlgenerator.Lazy object which returns a Python iterator when beeing evaluated.
        :param rowvariable: Name of the current object passed to childrens context
        :param orderingurlparameter: The name of the GET query parameter which is used to set the table ordering
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
            DataTable.tableclasses(spacing, zebra)
        )
        super().__init__(hg.THEAD(self.head), hg.TBODY(self.iterator), **kwargs)

    def with_toolbar(
        self,
        title,
        helper_text=None,
        primary_button=None,
        searchurl=None,
        query_urlparameter=None,
        bulkactions=(),
        pagination_options=(),
        paginator=None,
        page_urlparameter="page",
        itemsperpage_urlparameter="itemsperpage",
        checkbox_for_bulkaction_name="_selected",
        settingspanel=None,
    ):
        """
        wrap this datatable with title and toolbar
        title: table title
        helper_text: sub title
        primary_button: bread.layout.button.Button instance
        searchurl: url to which values entered in the searchfield should be submitted
        query_urlparameter: name of the query field for the searchurl which contains the entered text
        bulkactions: List of bread.menu.Action or bread.menu.Link instances bread.menu.Link will send a post or a get (depending on its "method" attribute) to the target url the sent data will be a form with the selected checkboxes as fields if the head-checkbox has been selected only that field will be selected
        """
        checkboxallid = f"datatable-check-{hg.html_id(self)}"
        header = [hg.H4(title, _class="bx--data-table-header__title")]
        if helper_text:
            header.append(
                hg.P(helper_text, _class="bx--data-table-header__description")
            )
        resultcontainerid = f"datatable-search-{hg.html_id(self)}"
        bulkactionlist = []
        for action in bulkactions:
            if isinstance(action, Link):
                action = Action(
                    js=hg.BaseElement(
                        "submitbulkaction(this.closest('[data-table]'), '",
                        action.href,
                        f"', method='{getattr(action, 'method', 'GET')}')",
                    ),
                    label=action.label,
                    iconname=action.iconname,
                    permissions=action.permissions,
                )
                bulkactionlist.append(Button.fromaction(action))
            elif isinstance(action, Action):
                bulkactionlist.append(Button.fromaction(action))
            else:
                RuntimeError(f"bulkaction needs to be {Action} or {Link}")

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
                    hg.DIV(
                        Search(
                            widgetattributes={"autofocus": True},
                            backend=search.SearchBackendConfig(
                                url=searchurl, query_parameter=query_urlparameter
                            ),
                            resultcontainerid=resultcontainerid,
                            show_result_container=False,
                        ),
                        _class="bx--toolbar-search-container-persistent",
                    )
                    if searchurl
                    else "",
                    Button(
                        icon="settings--adjust",
                        buttontype="ghost",
                        onclick="this.parentElement.parentElement.parentElement.querySelector('.settingscontainer').style.display = this.parentElement.parentElement.parentElement.querySelector('.settingscontainer').style.display == 'block' ? 'none' : 'block'; event.stopPropagation()",
                    )
                    if settingspanel
                    else "",
                    primary_button or "",
                    _class="bx--toolbar-content",
                ),
                _class="bx--table-toolbar",
            ),
            hg.DIV(
                hg.DIV(
                    id=resultcontainerid,
                    style="width: 100%; position: absolute; z-index: 999",
                ),
                style="width: 100%; position: relative",
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
            *(
                [
                    Pagination(
                        paginator,
                        pagination_options,
                        page_urlparameter=page_urlparameter,
                        itemsperpage_urlparameter=itemsperpage_urlparameter,
                    )
                ]
                if paginator
                else []
            ),
            _class="bx--data-table-container",
            data_table=True,
        )

    @staticmethod
    def from_model(
        model,
        queryset=None,
        columns: Union[List[str], List[DataTableColumn]] = None,
        rowactions=None,
        rowactions_dropdown=False,
        bulkactions=(),
        title=None,
        addurl=None,
        backurl: Union[hg.Lazy, str] = None,
        searchurl=None,
        query_urlparameter=None,
        rowclickaction=None,
        prevent_automatic_sortingnames=False,
        with_toolbar=True,
        pagination_options=(),
        paginator=None,
        page_urlparameter="page",
        itemsperpage_urlparameter="itemsperpage",
        checkbox_for_bulkaction_name="_selected",
        settingspanel=None,
        rowvariable="row",
        **kwargs,
    ):
        """TODO: Write Docs!!!!
        Yeah yeah, on it already...

        :param str backurl: sets the "next" parameter for the add-url and row-click actions.
                            In most cases this can be used to return to the current page
                            (default behaviour), stying on the according new page (use "#"
                            as value) or direct to a certain other page. Maybe this parameter
                            is unnecessary powerfull because there are other ways to set
                            these behaviours. However, the option of staying on the new page
                            coming back to the current page should somehow be kept available,
                            it is used very often.
        :param hg.BaseElement settingspanel: A panel which will be opened when clicking on the
                                             "Settings" button of the datatable, usefull e.g.
                                             for showing filter options. Currently only one
                                             button and one panel are supported. More buttons
                                             and panels could be interesting but may to over-
                                             engineered because it is a rare case and it is not
                                             difficutl to add another button by modifying the
                                             datatable after creation.
        """
        for col in columns:
            if not (isinstance(col, DataTableColumn) or isinstance(col, str)):
                raise ValueError(
                    f"Argument 'columns' needs to be of a List[str] or a List[DataTableColumn], but found {col}"
                )

        title = title or pretty_modelname(model, plural=True)

        if addurl is None:
            addurl = hg.F(
                lambda c: reverse_model(
                    model,
                    "add",
                    query={
                        "next": hg.resolve_lazy(backurl, c)
                        or c["request"].get_full_path()
                    },
                )
            )

        if rowactions_dropdown:
            objectactions_menu = OverflowMenu(
                rowactions,
                flip=True,
                item_attributes={"_class": "bx--table-row--menu-option"},
            )
        else:
            objectactions_menu = hg.DIV(
                hg.Iterator(
                    rowactions,
                    "action",
                    hg.F(
                        lambda c: Button.fromaction(
                            c["action"],
                            notext=True,
                            small=True,
                            buttontype="ghost",
                            _class="bx--overflow-menu",
                        )
                    ),
                ),
                style="display: flex",
            )

        queryset = model.objects.all() if queryset is None else queryset
        columns = columns or filter_fieldlist(model, ["__all__"])
        column_definitions: List[DataTableColumn] = []
        for col in columns:
            td_attributes = None
            if rowclickaction and getattr(col, "enable_row_click", True):
                td_attributes = hg.F(
                    lambda c: aslink_attributes(
                        objectaction(c[rowvariable], rowclickaction)
                    )
                )
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
                    col = col._replace(td_attributes=td_attributes)

            column_definitions.append(col)

        table = DataTable(
            column_definitions
            + (
                [
                    DataTableColumn(
                        "",
                        objectactions_menu,
                        td_attributes=hg.F(
                            lambda c: {"_class": "bx--table-column-menu"}
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
        )
        if with_toolbar:
            table = table.with_toolbar(
                title,
                primary_button=Button(
                    _("Add %s") % pretty_modelname(model),
                    icon=Icon("add", size=20),
                    onclick=hg.BaseElement("document.location = '", addurl, "'"),
                ),
                searchurl=searchurl,
                bulkactions=bulkactions,
                pagination_options=pagination_options,
                page_urlparameter=page_urlparameter,
                query_urlparameter=query_urlparameter,
                paginator=paginator,
                itemsperpage_urlparameter=itemsperpage_urlparameter,
                checkbox_for_bulkaction_name=checkbox_for_bulkaction_name,
                settingspanel=settingspanel,
            )
        return table

    @staticmethod
    def from_queryset(
        queryset,
        **kwargs,
    ):
        """TODO: Write Docs!!!!"""
        return DataTable.from_model(
            queryset.model,
            queryset=queryset,
            **kwargs,
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
    def tableclasses(spacing, zebra):
        if spacing not in DataTable.SPACINGS:
            raise ValueError(
                f"argument 'spacin' is {spacing} but needs to be one of {DataTable.SPACINGS}"
            )
        classes = ["bx--data-table bx--data-table--sort"]
        if spacing != "default":
            classes.append(f" bx--data-table--{spacing}")
        if zebra:
            classes.append(" bx--data-table--zebra")
        return classes


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
        elif isinstance(field, models.Field):
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
        return link_with_urlparameters(
            context["request"], **{orderingurlparameter: nextordering}
        )

    return aslink_attributes(hg.F(extractsortinglink))
