import html
import re

import django_filters
import htmlgenerator as hg
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models.functions import Lower
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django_filters.views import FilterView
from guardian.mixins import PermissionListMixin

from .. import layout as _layout  # prevent name clashing
from ..fields.queryfield import parsequeryexpression
from ..formatters import render_field
from ..forms.forms import FilterForm
from ..utils import pretty_fieldname, pretty_modelname, xlsxresponse
from .util import BreadView


class BrowseView(BreadView, LoginRequiredMixin, PermissionListMixin, FilterView):
    template_name = "bread/layout.html"
    fields = None
    filterfields = None
    page_kwarg = "browsepage"  # need to use something different than the default "page" because we also filter through kwargs
    bulkactions = ()  # list of links

    def __init__(self, *args, **kwargs):
        self.bulkactions = kwargs.get("bulkactions", getattr(self, "bulkactions", ()))
        self.fields = kwargs.get("fields", getattr(self, "fields", ["__all__"]))
        self.filterset_fields = kwargs.get("filterset_fields", self.filterset_fields)
        self.searchurl = kwargs.get("searchurl", getattr(self, "searchurl", ()))
        self.queryfieldname = kwargs.get(
            "queryfieldname", getattr(self, "queryfieldname", ())
        )
        super().__init__(*args, **kwargs)

    def layout(self, request):
        return _layout.datatable.DataTable.from_model(
            self.model,
            hg.C("object_list"),
            fields=self.fields,
            bulkactions=self.bulkactions,
            searchurl=self.searchurl,
            queryfieldname=self.queryfieldname,
        )

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]

    def get_filterset_class(self):
        return generate_filterset_class(self.model, self.filterset_fields)

    def get_paginate_by(self, queryset=None):
        return int(
            self.request.GET.get(
                "paginate_by",
                getattr(self, "paginate_by") or settings.DEFAULT_PAGINATION,
            )
        )

    def get_pagination_choices(self):
        return sorted(
            set(
                getattr(self, "pagination_choices", settings.DEFAULT_PAGINATION_CHOICES)
            )
            | set((self.get_paginate_by(),))
        )

    def get(self, *args, **kwargs):
        if "reset" in self.request.GET:
            return redirect(self.request.path)

        return super().get(*args, **kwargs)

    def get_queryset(self):
        """Prefetch related tables to speed up queries. Also order result by get-parameters."""
        ret = super().get_queryset()

        # order fields
        order = self.request.GET.get("order")
        if order:
            fields = order.split(",")
            ordering = [
                Lower(f[1:]).desc() if f.startswith("-") else Lower(f) for f in fields
            ]
            ret = ret.order_by(*ordering)
        return ret

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
    filterstr: a django-style filter str which will lazy evaluated, see bread.fields.queryfield.parsequeryexpression
    """
    import openpyxl
    from openpyxl.styles import Font

    model = queryset.model

    if not isinstance(fields, dict):
        fields = {field: render_field for field in fields}

    def excelview(request):
        items = queryset
        if isinstance(filterstr, str):
            items = parsequeryexpression(model.objects.all(), filterstr).queryset
        if "selected" in request.GET:
            items = items.filter(
                pk__in=[int(i) for i in request.GET.getlist("selected")]
            )
        items = list(items.all())

        workbook = openpyxl.Workbook()
        workbook.title = pretty_modelname(model)
        header_cells = workbook.active.iter_cols(
            min_row=1, max_col=len(fields) + 1, max_row=len(items) + 1
        )
        newline_regex = re.compile(
            r"<\s*br\s*/?\s*>"
        )  # replace HTML line breaks with newlines
        for field, col in zip(
            [(field, pretty_fieldname(field)) for field in fields],
            header_cells,
        ):
            col[0].value = field[1]
            col[0].font = Font(bold=True)
            for i, cell in enumerate(col[1:]):
                html_value = str(fields[field[0]](items[i], field[0]))
                cleaned = html.unescape(
                    newline_regex.sub(r"\n", strip_tags(html_value))
                )
                cell.value = cleaned

        return xlsxresponse(workbook, workbook.title)

    return excelview
