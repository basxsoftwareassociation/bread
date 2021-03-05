import django_filters
import htmlgenerator as hg
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.shortcuts import redirect
from django_filters.views import FilterView
from guardian.mixins import PermissionListMixin

from .. import layout as _layout  # prevent name clashing
from ..formatters import render_field
from ..forms.forms import FilterForm
from ..utils import generate_excel, pretty_modelname, xlsxresponse
from ..utils.model_helpers import _expand_ALL_constant
from .util import BreadView


class BrowseView(BreadView, LoginRequiredMixin, PermissionListMixin, FilterView):
    template_name = "bread/layout.html"
    orderingurlparameter = "ordering"
    itemsperpage_urlparameter = "itemsperpage"
    pagination_choices = ()
    columns = ["__all__"]
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
        self.filterset_fields = kwargs.get("filterset_fields") or self.filterset_fields
        self.searchurl = kwargs.get("searchurl") or self.searchurl
        self.queryfieldname = kwargs.get("queryfieldname") or self.queryfieldname
        self.rowclickaction = kwargs.get("rowclickaction") or self.rowclickaction
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
            queryfieldname=self.queryfieldname,
            rowclickaction=self.rowclickaction,
            pagination_options=self.pagination_choices,
            page_urlparameter=self.page_kwarg,
            paginator=self.get_paginator(qs, self.get_paginate_by(qs)),
            itemsperpage_urlparameter=self.itemsperpage_urlparameter,
        )

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]

    def get_filterset_class(self):
        return generate_filterset_class(self.model, self.filterset_fields)

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


def generate_filterset_class(model, fields):
    # make text-based fields filtering with icontains and datefield as range
    config = {
        "model": model,
        "filter_overrides": {
            models.CharField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {"lookup_expr": "icontains"},
            },
            models.TextField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {"lookup_expr": "icontains"},
            },
            models.EmailField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {"lookup_expr": "icontains"},
            },
            models.URLField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {"lookup_expr": "icontains"},
            },
            models.DateField: {
                "filter_class": django_filters.DateFromToRangeFilter,
                "extra": lambda f: {
                    "widget": django_filters.widgets.DateRangeWidget(
                        attrs={"type": "text", "class": "validate datepicker"}
                    )
                },
            },
            models.DateTimeField: {
                "filter_class": django_filters.DateFromToRangeFilter,
                "extra": lambda f: {
                    "widget": django_filters.widgets.DateRangeWidget(
                        attrs={"type": "text", "class": "validate datepicker"}
                    )
                },
            },
        },
    }
    config["exclude"] = [
        f.name
        for f in model._meta.get_fields()
        if isinstance(f, models.FileField) or isinstance(f, GenericForeignKey)
    ]
    config["fields"] = fields
    config["form"] = FilterForm
    filterset = type(
        f"{model._meta.object_name}FilterSet",
        (django_filters.FilterSet,),
        {"Meta": type("Meta", (object,), config)},
    )
    return filterset


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
        fields = {field: render_field for field in fields}

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
