from typing import Any, Iterable, List, NamedTuple, Optional, Union

import htmlgenerator as hg
from django import forms
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from django_countries.fields import CountryField

from basxbread.utils import filter_fieldlist, get_all_subclasses, resolve_modellookup
from basxbread.utils.links import Link, ModelHref
from basxbread.utils.urls import link_with_urlparameters

from ..utils import ObjectFieldLabel, ObjectFieldValue, aslink_attributes
from .button import Button
from .forms import Form, FormField
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
        primary_button: basxbread.layout.button.Button instance
        bulkactions: List of basxbread.utils.links.Link instances. Will send a post or a get (depending
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
                    style="position: absolute; z-index: 999; right: 0; display: none; max-width: 80%",
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
        prevent_automatic_filternames=False,
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
        filter_urlparameter: Optional[str] = None,
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

        title = title or model._meta.verbose_name_plural

        if primary_button is None:
            primary_button = Button.from_link(
                Link(
                    href=ModelHref(model, "add"),
                    label=_("Add %s") % model._meta.verbose_name,
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
                    col=col,
                    model=model,
                    prevent_automatic_sortingnames=prevent_automatic_sortingnames,
                    prevent_automatic_filternames=prevent_automatic_filternames,
                    rowvariable=rowvariable,
                    td_attributes=td_attributes,
                )
            else:
                if td_attributes:
                    col = col._replace(td_attributes=td_attributes)  # type: ignore

            column_definitions.append(col)

        settingspanel = build_filter_ui(
            model,
            ("AND",)
            + tuple(
                i.filtername for i in column_definitions if i.filtername is not None
            ),
            filter_urlparameter,
        )

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


# Helpers for building columns ###################################################################


class DataTableColumn(NamedTuple):
    header: Any
    cell: Any
    sortingname: Optional[str] = None
    enable_row_click: bool = True
    th_attributes: Optional[Union[hg.F, dict]] = None
    td_attributes: Optional[Union[hg.F, dict]] = None
    filtername: Optional[str] = None

    @staticmethod
    def from_modelfield(
        col,
        model,
        prevent_automatic_sortingnames=False,
        rowvariable="row",
        th_attributes=None,
        td_attributes=None,
        prevent_automatic_filternames=False,
    ) -> "DataTableColumn":
        return DataTableColumn(
            header=ObjectFieldLabel(col, model),
            cell=ObjectFieldValue(col, rowvariable),
            sortingname=sortingname_for_column(model, col)
            if not prevent_automatic_sortingnames
            else None,
            filtername=filtername_for_column(model, col)
            if not prevent_automatic_filternames
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
    return LOOKUP_SEP.join(components)


def filtername_for_column(model, column):
    components = []
    for field in resolve_modellookup(model, column):
        components.append(field.name)
    return LOOKUP_SEP.join(components)


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


# Helpers for building a filter panel #######################################


def build_filter_ui(basemodel, filterconfig, filter_urlparameter):
    return hg.DIV(
        hg.DIV(
            hg.DIV(
                hg.DIV(_("Filter"), style="margin-bottom: 1rem"),
                hg.DIV(
                    Form(
                        _build_form(_build_formclass(basemodel, filterconfig)),
                        _build_filter_ui_recursive(basemodel, filterconfig),
                        _class="filterform",
                    ),
                    style="display: flex",
                ),
                style="border-right: #ccc solid 1px; margin: 0 16px 0 0",
            ),
            style="display: flex; padding: 24px 32px 0 32px",
        ),
        hg.DIV(
            Button(
                _("Cancel"),
                buttontype="ghost",
                onclick="this.closest('.settingscontainer').style.display = 'none'",
            ),
            Button.from_link(
                Link(
                    label=_("Reset"),
                    href=hg.format("{}?reset=1", hg.C("request").path),
                    iconname=None,
                ),
                buttontype="secondary",
            ),
            hg.SCRIPT(
                hg.mark_safe(
                    """
function build_filter_expression(formElement) {
    return build_filter_expression_recursive(formElement, new FormData(formElement));
}
function build_filter_expression_recursive(filterformElement, formdata) {
    grouptype = filterformElement.getAttribute("data-filtergroup");
    var ret = [];
    for(element of filterformElement.querySelectorAll(":scope > div[data-filterfield]")) {
        let key = element.getAttribute("data-filterfield");
        if(formdata.has(key) && formdata.get(key) !== "")
            ret.push(key.replaceAll("__", ".") + " " + element.getAttribute("data-operator") +' "' + formdata.get(key).replaceAll('"', '\\"') + '"');
    }
    for(element of filterformElement.querySelectorAll(":scope > div[data-filtergroup]")) {
        let subgroup = build_filter_expression_recursive(element, formdata);
        if(subgroup !== "")
            ret.push(subgroup);
    }
    if(ret.length > 0)
        return "( " + ret.join(" " + grouptype.toLowerCase() + " ") + " )";
    return ""
}"""
                )
            ),
            hg.FORM(
                Button(
                    pgettext_lazy("apply filter", "Filter"),
                    type="submit",
                    name=filter_urlparameter,
                    value=hg.C("request").GET.get(filter_urlparameter, ""),
                    onclick="""this.value = build_filter_expression(this.closest('.filterpanel').querySelector('.filterform'));""",
                ),
                method="GET",
            ),
            style="display: flex; justify-content: flex-end; margin-top: 24px",
            _class="bx--modal-footer",
        ),
        _class="filterpanel",
        style="background-color: #fff",
    )


def _build_filter_ui_recursive(basemodel, filterconfig):
    """
    filterconfig: Tree in the form of
                  ("and"
                      ("or", fieldname1, fieldname2),
                      ("or", fieldname3, fieldname4),
                  )
    """
    if isinstance(filterconfig, tuple):
        if len(filterconfig) <= 1:
            return None
        if filterconfig[0].lower() not in ("and", "or"):
            raise RuntimeError(
                'Filtergroups need to have "AND" or "OR" as the first argument'
            )
        return hg.DIV(
            data_filtergroup=filterconfig[0].lower(),
            *[_build_filter_ui_recursive(basemodel, i) for i in filterconfig[1:]],
        )
    elif isinstance(filterconfig, str):
        return hg.DIV(
            FormField(filterconfig),
            data_filterfield=filterconfig,
            data_operator=_djangql_operator(basemodel, filterconfig),
        )
    raise RuntimeError(f"Invalid value inside filterconfig: {filterconfig}")


def _build_formclass(basemodel, filterconfig):
    def all_fields(config):
        for i in config:
            if isinstance(i, str):
                if i.lower() not in ("and", "or"):
                    yield i
            else:
                yield from all_fields(i)

    allfields = {
        field: _related_field(basemodel, _without_lookup(field))
        for field in all_fields(filterconfig)
    }

    fields = {
        fieldname: _formfield(fieldname, field)
        for fieldname, field in allfields.items()
    }
    attrs = {**fields}

    return type("CustomFilterForm", (forms.Form,), attrs)


def _build_form(form_class):
    def params(context):
        print(form_class.declared_fields)
        return form_class({})

    return hg.F(params)


def _related_field(model, fieldname):
    if LOOKUP_SEP in fieldname:
        field = model._meta.get_field(fieldname.split(LOOKUP_SEP, 1)[0])
        return _related_field(field.related_model, fieldname.split(LOOKUP_SEP, 1)[1])
    return model._meta.get_field(fieldname)


def _formfield(fieldname, field):
    kwargs = {"required": False}

    # prevent use of TextArea
    if isinstance(field, models.TextField):
        kwargs["widget"] = forms.TextInput()

    return field.formfield(**kwargs)


def _lookup(fieldname):
    lookups = set()
    for cls in get_all_subclasses(models.query_utils.RegisterLookupMixin):
        lookups |= set(cls.get_lookups().keys())

    if any(fieldname.endswith("{LOOKUP_SEP}{lookup}") for lookup in lookups):
        return fieldname.rsplit(LOOKUP_SEP, 1)[1]
    return None


def _djangql_operator(basemodel, fieldname):
    # possible DjangoQL operators:
    # = != < <= > >=
    # startswith, not startswith, endswith, not endswith
    # ~ !~
    # in          not in
    customlookup = {
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "icontains": "~",
        "contains": "~",
        "in": "in",
        "istartswith": "startswith",
        "startswith": "startswith",
        "iendswith": "endswith",
        "endswith": "endswith",
    }.get(_lookup(fieldname), None)
    if customlookup is not None:
        return customlookup

    field = _related_field(basemodel, _without_lookup(fieldname))
    if isinstance(field, CountryField):
        return " = "
    if isinstance(field, (models.CharField, models.TextField)):
        return " ~ "
    return " = "


def _without_lookup(fieldname):
    lookuppart = _lookup(fieldname)
    if lookuppart is not None:
        return fieldname[: -len(lookuppart)]
    return fieldname


# Helper for building a searchbar ##############################################


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
        },
        width="100%",
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
