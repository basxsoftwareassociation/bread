import htmlgenerator as hg
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from djangoql.queryset import apply_search
from guardian.mixins import PermissionListMixin

from .. import layout as _layout  # prevent name clashing
from ..formatters import format_value
from ..menu import Action
from ..utils import (
    generate_excel,
    link_with_urlparameters,
    pretty_modelname,
    xlsxresponse,
)
from ..utils.model_helpers import _expand_ALL_constant
from .util import BreadView


class BrowseView(BreadView, LoginRequiredMixin, PermissionListMixin, ListView):
    template_name = "bread/layout.html"
    orderingurlparameter = "ordering"
    itemsperpage_urlparameter = "itemsperpage"
    pagination_choices = ()
    columns = ["__all__"]
    searchurl = None
    query_urlparameter = "q"
    rowclickaction = None
    filteroptions = ()
    filterfields = None
    bulkactions = ()  # list of links
    rowactions = ()  # list of links

    def __init__(self, *args, **kwargs):
        self.bulkactions = kwargs.get("bulkactions") or self.bulkactions
        self.orderingurlparameter = (
            kwargs.get("orderingurlparameter") or self.orderingurlparameter
        )
        self.itemsperpage_urlparameter = (
            kwargs.get("itemsperpage_urlparameter") or self.itemsperpage_urlparameter
        )
        self.pagination_choices = (
            kwargs.get("pagination_choices")
            or self.pagination_choices
            or settings.DEFAULT_PAGINATION_CHOICES
        )
        self.rowactions = kwargs.get("rowactions") or self.rowactions
        self.columns = kwargs.get("columns") or self.columns
        self.searchurl = kwargs.get("searchurl") or self.searchurl
        self.query_urlparameter = (
            kwargs.get("query_urlparameter") or self.query_urlparameter
        )
        self.rowclickaction = kwargs.get("rowclickaction") or self.rowclickaction
        self.filteroptions = kwargs.get("filteroptions") or self.filteroptions
        super().__init__(*args, **kwargs)

    def layout(self, request):
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
            toolbar_action_menus=[
                (
                    "filter",
                    [
                        Action(
                            js=hg.BaseElement(
                                "document.location ='",
                                hg.F(
                                    lambda c, e, filter=filter: link_with_urlparameters(
                                        c["request"],
                                        **{
                                            self.query_urlparameter: filter,
                                            self.page_kwarg: None,
                                        },
                                    )
                                ),
                                "'",
                            ),
                            label=name,
                        )
                        for name, filter in self.filteroptions
                    ]
                    + [
                        Action(
                            js=hg.BaseElement(
                                "document.location ='",
                                hg.F(
                                    lambda c, e: link_with_urlparameters(
                                        c["request"],
                                        **{
                                            self.query_urlparameter: None,
                                            self.page_kwarg: None,
                                        },
                                    )
                                ),
                                "'",
                            ),
                            icon="filter--remove",
                            label=_("Reset"),
                        )
                    ],
                )
            ]
            if self.filteroptions
            else [],
        )

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]

    def get(self, *args, **kwargs):
        if "reset" in self.request.GET:
            return redirect(self.request.path)

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
        order = self.request.GET.get(self.orderingurlparameter)
        if order:
            if order.endswith("__int"):
                order = order[:-5]
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

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["pagetitle"] = pretty_modelname(self.model, plural=True)
        return context


class TreeView(BrowseView):
    template_name = "bread/tree.html"
    parent_accessor = None
    label_function = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_accessor = kwargs.get("parent_accessor", self.parent_accessor)
        self.label_function = kwargs.get("label_function", lambda o: str(o))

    def nodes(self):
        # we do this here a bit more complicated in order to hit database only once
        # and to make use of the filtered queryset
        objects = list(self.object_list)

        # first pass: get child relationships
        children = {None: []}
        for object in objects:
            parent_pk = None
            parent = getattr(object, self.parent_accessor)
            if parent is not None and parent in objects:
                parent_pk = parent.pk
            if parent_pk not in children:
                children[parent_pk] = []
            children[parent_pk].append(object)

        # second pass: build tree recursively
        def build_tree(nodes):
            ret = {}
            for node in nodes:
                node.tree_label = self.label_function(node)
                ret[node] = None
                if node.pk in children:
                    ret[node] = build_tree(children[node.pk])
            return ret

        return build_tree(children[None])


def generate_excel_view(queryset, fields, filterstr=None):
    """
    Generates an excel file from the given queryset with the specified fields.
    fields: list [<fieldname1>, <fieldname2>, ...] or dict with {<fieldname>: formatting_function(object, fieldname)}
    filterstr: a djangoql filter string which will lazy evaluated, see bread.fields.queryfield.parsequeryexpression
    """

    model = queryset.model

    if isinstance(fields, list):
        fields = _expand_ALL_constant(model, fields)

    if not isinstance(fields, dict):
        fields = {
            field: lambda inst: format_value(getattr(inst, field)) for field in fields
        }

    def excelview(request):
        from bread.contrib.reports.fields.queryfield import parsequeryexpression

        items = queryset
        if isinstance(filterstr, str):
            items = parsequeryexpression(model.objects.all(), filterstr)
        if "selected" in request.GET:
            items = items.filter(
                pk__in=[int(i) for i in request.GET.getlist("selected")]
            )
        items = list(items.all())
        workbook = generate_excel(items, fields)
        workbook.title = pretty_modelname(model)

        return xlsxresponse(workbook, workbook.title)

    return excelview
