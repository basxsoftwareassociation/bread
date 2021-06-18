import htmlgenerator as hg
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.shortcuts import redirect
from django.views.generic import ListView
from djangoql.queryset import apply_search
from guardian.mixins import PermissionListMixin

from bread.utils import expand_ALL_constant, filter_fieldlist

from .. import layout as _layout  # prevent name clashing
from ..layout.base import fieldlabel
from ..utils import generate_excel, pretty_modelname, xlsxresponse
from .util import BreadView


class BrowseView(BreadView, LoginRequiredMixin, PermissionListMixin, ListView):
    """TODO: documentation"""

    template_name = "bread/base.html"
    orderingurlparameter = "ordering"
    itemsperpage_urlparameter = "itemsperpage"
    objectids_urlparameter = "_selected"  # see bread/static/js/main.js:submitbulkaction and bread/layout/components/datatable.py
    pagination_choices = ()
    columns = ["__all__"]
    searchurl = None
    query_urlparameter = "q"
    rowclickaction = None
    bulkactions = ()  # list of links
    rowactions = ()  # list of links
    backurl = None
    asexcel = False

    def __init__(self, *args, **kwargs):
        self.bulkactions = kwargs.get("bulkactions") or self.bulkactions
        self.orderingurlparameter = (
            kwargs.get("orderingurlparameter") or self.orderingurlparameter
        )
        self.itemsperpage_urlparameter = (
            kwargs.get("itemsperpage_urlparameter") or self.itemsperpage_urlparameter
        )
        self.objectids_urlparameter = (
            kwargs.get("objectids_urlparameter") or self.objectids_urlparameter
        )
        self.pagination_choices = (
            kwargs.get("pagination_choices")
            or self.pagination_choices
            or getattr(settings, "DEFAULT_PAGINATION_CHOICES", [25, 100, 500])
        )
        self.rowactions = kwargs.get("rowactions") or self.rowactions
        self.columns = expand_ALL_constant(
            kwargs["model"], kwargs.get("columns") or self.columns
        )
        self.searchurl = kwargs.get("searchurl") or self.searchurl
        self.query_urlparameter = (
            kwargs.get("query_urlparameter") or self.query_urlparameter
        )
        self.rowclickaction = kwargs.get("rowclickaction") or self.rowclickaction
        self.backurl = kwargs.get("backurl") or self.backurl
        super().__init__(*args, **kwargs)

    def get_layout(self):
        qs = self.get_queryset()
        return _layout.datatable.DataTable.from_model(
            self.model,
            hg.C("object_list"),
            columns=self.columns,
            bulkactions=self.bulkactions,
            rowactions=self.rowactions,
            searchurl=self.searchurl,
            query_urlparameter=self.query_urlparameter,
            rowclickaction=self.rowclickaction,
            pagination_options=self.pagination_choices,
            page_urlparameter=self.page_kwarg,
            paginator=self.get_paginator(qs, self.get_paginate_by(qs)),
            itemsperpage_urlparameter=self.itemsperpage_urlparameter,
            checkbox_for_bulkaction_name=self.objectids_urlparameter,
            settingspanel=self.get_settingspanel(),
            backurl=self.backurl,
        )

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "layout": self._get_layout_cached(),
            "pagetitle": pretty_modelname(self.model, plural=True),
        }

    def get_settingspanel(self):
        return None

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]

    def get(self, *args, **kwargs):
        if "reset" in self.request.GET:
            return redirect(self.request.path)
        if self.asexcel:
            return self.export(*args, **kwargs)

        return super().get(*args, **kwargs)

    def get_paginate_by(self, queryset):
        return self.request.GET.get(
            self.itemsperpage_urlparameter, self.pagination_choices[0]
        )

    def get_queryset(self):
        """Prefetch related tables to speed up queries. Also order result by get-parameters."""
        qs = super().get_queryset()
        if self.query_urlparameter in self.request.GET:
            qs = apply_search(
                qs,
                "("
                + ") and (".join(self.request.GET.getlist(self.query_urlparameter))
                + ")",
            )

        selectedobjects = self.request.GET.getlist(self.objectids_urlparameter)
        if selectedobjects and "all" not in selectedobjects:
            qs &= super().get_queryset().filter(pk__in=selectedobjects)

        order = self.request.GET.get(self.orderingurlparameter)
        if order:
            if order.endswith("__int"):
                order = order[: -len("__int")]
                qs = qs.order_by(
                    models.functions.Cast(order[1:], models.IntegerField()).desc()
                    if order.startswith("-")
                    else models.functions.Cast(order, models.IntegerField())
                )
            else:
                qs = qs.order_by(
                    models.functions.Lower(order[1:]).desc()
                    if order.startswith("-")
                    else models.functions.Lower(order)
                )
        return qs

    def export(self, *args, columns=None, **kwargs):
        columns = columns or self.columns
        if "__all__" in columns:
            columns = filter_fieldlist(self.model, columns)
        columndefinitions = {}
        for column in columns:
            if not (
                isinstance(column, _layout.datatable.DataTableColumn)
                or isinstance(column, str)
            ):
                raise ValueError(
                    f"Argument 'columns' needs to be of a list with items of type str or DataTableColumn, but found {column}"
                )
            if isinstance(column, str):
                column = _layout.datatable.DataTableColumn(
                    fieldlabel(self.model, column), hg.C(f"row.{column}")
                )

            columndefinitions[column.header] = lambda row, column=column: hg.render(
                hg.BaseElement(column.cell), {"row": row}
            )

        workbook = generate_excel(self.get_queryset(), columndefinitions)
        workbook.title = pretty_modelname(self.model)
        return xlsxresponse(workbook, workbook.title)
