from dataclasses import dataclass
from typing import Any, List, Union

import htmlgenerator as hg
from django.db import models
from django.utils.translation import gettext_lazy as _

from bread.menu import Action, Link
from bread.utils import filter_fieldlist, pretty_modelname, resolve_modellookup
from bread.utils.urls import link_with_urlparameters, reverse_model

from ..base import aslink_attributes, fieldlabel, objectaction
from .button import Button
from .icon import Icon
from .overflow_menu import OverflowMenu
from .pagination import Pagination
from .search import Search


def sortingclass_for_column(orderingurlparameter, columnname):
    def extracturlparameter(context, element):
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

    def extractsortinglink(context, element):
        currentordering = context["request"].GET.get(orderingurlparameter, None)
        nextordering = ORDERING_VALUES.get(currentordering, columnname)
        return link_with_urlparameters(
            context["request"], **{orderingurlparameter: nextordering}
        )

    return aslink_attributes(hg.F(extractsortinglink))


@dataclass
class DataTableColumn:
    header: Any
    cell: Any
    sortingname: str = None
    enable_row_click: bool = True


class DataTable(hg.BaseElement):
    SPACINGS = ["default", "compact", "short", "tall"]

    def __init__(
        self,
        columns: List[DataTableColumn],
        row_iterator,
        rowvariable="row",
        spacing="default",
        orderingurlparameter="ordering",
        zebra=False,
    ):
        """columns: list of DataTableColumn(header, cell, sortingname, enable_row_click)
        row_iterator: python iterator of htmlgenerator.Lazy object which returns an iterator
        rowvariable: name of the current object passed to childrens context
        if the header_expression/row_expression has an attribute td_attributes it will be used as attributes for the TH/TD elements (necessary because sometimes the content requires additional classes on the parent element)
        sortingname: value for the URL parameter 'orderingurlparameter', None if sorting is not allowed
        spacing: one of "default", "compact", "short", "tall"
        zebra: alternate row colors
        """
        if spacing not in DataTable.SPACINGS:
            raise ValueError(
                f"argument 'spacin' is {spacing} but needs to be one of {DataTable.SPACINGS}"
            )
        classes = ["bx--data-table bx--data-table--sort"]
        if spacing != "default":
            classes.append(f" bx--data-table--{spacing}")
        if zebra:
            classes.append(" bx--data-table--zebra")

        self.head = hg.TR()
        for col in columns:
            headcontent = hg.SPAN(col.header, _class="bx--table-header-label")
            if col.sortingname:
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
                        sortingclass_for_column(orderingurlparameter, col.sortingname),
                    ),
                    data_event="sort",
                    title=col.header,
                    **sortinglink_for_column(orderingurlparameter, col.sortingname),
                )

            self.head.append(
                hg.TH(headcontent, **getattr(col.header, "td_attributes", {}))
            )

        self.iterator = hg.Iterator(
            row_iterator,
            rowvariable,
            hg.TR(
                *[
                    hg.TD(col.cell, **getattr(col.cell, "td_attributes", {}))
                    for col in columns
                ]
            ),
        )
        super().__init__(
            hg.TABLE(
                hg.THEAD(self.head),
                hg.TBODY(self.iterator),
                _class=" ".join(classes),
            )
        )

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
                        action.url,
                        f"', method='{getattr(action, 'method', 'GET')}')",
                    ),
                    label=action.label,
                    icon=action.icon,
                    permissions=action._permissions,
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
                        name="selected",
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
                        name="selected",
                        value=hg.If(
                            hg.F(
                                lambda c, e: hasattr(
                                    c[self.iterator.loopvariable], "pk"
                                )
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
                        Search(widgetattributes={"autofocus": True}).withajaxurl(
                            url=searchurl,
                            query_urlparameter=query_urlparameter,
                            resultcontainerid=resultcontainerid,
                            resultcontainer=False,
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
        columns=None,
        rowactions=None,
        rowactions_dropdown=False,
        bulkactions=(),
        title=None,
        addurl=None,
        backurl=None,
        searchurl=None,
        query_urlparameter=None,
        rowclickaction=None,
        preven_automatic_sortingnames=False,
        with_toolbar=True,
        pagination_options=(),
        paginator=None,
        page_urlparameter="page",
        itemsperpage_urlparameter="itemsperpage",
        settingspanel=None,
        **kwargs,
    ):
        """TODO: Write Docs!!!!"""
        title = title or pretty_modelname(model, plural=True)
        rowvariable = kwargs.get("rowvariable", "row")

        backquery = {"next": backurl} if backurl else {}
        if addurl is None:
            addurl = reverse_model(model, "add", query=backquery)

        if rowactions_dropdown:
            objectactions_menu = OverflowMenu(
                rowactions,
                flip=True,
                item_attributes={"_class": "bx--table-row--menu-option"},
            )
        else:
            objectactions_menu = hg.Iterator(
                rowactions,
                "action",
                hg.F(
                    lambda c, e: Button.fromaction(
                        c["action"],
                        notext=True,
                        small=True,
                        buttontype="ghost",
                        _class="bx--overflow-menu",
                    )
                ),
            )

        action_menu_header = hg.BaseElement()
        action_menu_header.td_attributes = {"_class": "bx--table-column-menu"}
        queryset = model.objects.all() if queryset is None else queryset
        columns = columns or filter_fieldlist(model, ["__all__"])
        column_definitions: List[DataTableColumn] = []
        for col in columns:
            if not (isinstance(col, DataTableColumn) or isinstance(col, str)):
                raise ValueError(
                    f"Argument 'columns' needs to be of a List[str] or a List[DataTableColumn], but found {col}"
                )
            # convert simple string (modelfield) to column definition
            if isinstance(col, str):
                col = DataTableColumn(
                    fieldlabel(model, col),
                    hg.C(f"{rowvariable}.{col}"),
                    sortingname_for_column(model, col)
                    if not preven_automatic_sortingnames
                    else None,
                )

            if rowclickaction and col.enable_row_click:
                col.cell.td_attributes = aslink_attributes(
                    hg.F(
                        lambda c, e: objectaction(
                            c[rowvariable], rowclickaction, query=backquery
                        )
                    )
                )
            column_definitions.append(col)

        table = DataTable(
            column_definitions
            + (
                [DataTableColumn(action_menu_header, objectactions_menu)]
                if rowactions
                else []
            ),
            # querysets are cached, the call to all will make sure a new query is used in every request
            hg.F(lambda c, e: queryset),
            **kwargs,
        )
        if with_toolbar:
            table = table.with_toolbar(
                title,
                primary_button=Button(
                    _("Add %s") % pretty_modelname(model),
                    icon=Icon("add", size=20),
                    onclick=f"document.location = '{addurl}'",
                ),
                searchurl=searchurl,
                bulkactions=bulkactions,
                pagination_options=pagination_options,
                page_urlparameter=page_urlparameter,
                query_urlparameter=query_urlparameter,
                paginator=paginator,
                itemsperpage_urlparameter=itemsperpage_urlparameter,
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
