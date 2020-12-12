import re
from html.parser import HTMLParser

import django_filters
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models.functions import Lower
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView
from guardian.mixins import PermissionListMixin

from .. import layout as _layout  # prevent name clashing
from ..formatters import render_field
from ..forms.forms import FilterForm
from ..utils import (
    CustomizableClass,
    filter_fieldlist,
    pretty_fieldname,
    resolve_relationship,
    title,
    xlsxresponse,
)
from ..utils.urls import reverse_model


class BrowseView(
    CustomizableClass, LoginRequiredMixin, PermissionListMixin, FilterView
):
    template_name = "bread/layout.html"
    fields = None
    filterfields = None
    page_kwarg = "browsepage"  # need to use something different than the default "page" because we also filter through kwargs
    layout = None
    object_actions = ()  # list of links

    def __init__(self, *args, **kwargs):
        model = kwargs["model"]
        self.filterset_fields = kwargs.get("filterset_fields", self.filterset_fields)
        layout = kwargs.get("layout", self.layout)
        layout = layout() if callable(layout) else layout
        self.object_actions = kwargs.get("object_actions", self.object_actions)

        object_actions_menu = _layout.overflow_menu.OverflowMenu(
            _layout.F(self.get_object_actions),
            menucontext=_layout.ObjectContext,
            flip=True,
            item_attributes={"_class": "bx--table-row--menu-option"},
        )
        # the data-table object will check child elements for td_attributes to fill in attributes for TD-elements
        object_actions_menu.td_attributes = {"_class": "bx--table-column-menu"}
        action_menu_header = _layout.BaseElement()
        action_menu_header.td_attributes = {"_class": "bx--table-column-menu"}
        if not isinstance(layout, _layout.BaseElement):
            if not isinstance(layout, list) and layout is not None:
                raise RuntimeError(
                    "layout needs to be a BaseElement instance or a list of fieldnames"
                )
            print(layout)
            fields = layout
            layout = _layout.datatable.DataTable.full(
                _layout.ModelName(plural=True),
                _layout.datatable.DataTable(
                    [
                        (_layout.ModelFieldLabel(field), _layout.ModelFieldValue(field))
                        for field in list(filter_fieldlist(model, fields))
                    ]
                    + [(None, object_actions_menu)],
                    _layout.C("object_list"),
                    _layout.ObjectContext,
                ),
                _layout.button.Button(
                    _("Add %s") % title(model._meta.verbose_name),
                    icon=_layout.icon.Icon("add", size=20),
                    onclick=f"document.location = '{reverse_model(model, 'add')}'",
                ),
            )
        # makes the model available to bound elements like ModelFieldValue and ModelFieldLabel
        self.layout = _layout.ModelContext(model, layout)
        super().__init__(*args, **kwargs)

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
        if "export" in self.request.GET:
            return self.as_excel()

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

    def as_excel(self):
        # openpyxl is an extra dependency
        import openpyxl
        from openpyxl.styles import Font

        items = []
        # from django_filters.views.BaseFilterView.get in order to apply filter to excel export
        self.filterset = self.get_filterset(self.get_filterset_class())
        if (
            not self.filterset.is_bound
            or self.filterset.is_valid()
            or not self.get_strict()
        ):
            items = list(self.filterset.qs)
        items = list(self.filterset.qs)

        workbook = openpyxl.Workbook()
        workbook.title = self.admin.verbose_modelname_plural
        header_cells = workbook.active.iter_cols(
            min_row=1, max_col=len(self.fields) + 1, max_row=len(items) + 1
        )
        htmlparser = HTMLParser()
        newline_regex = re.compile(
            r"<\s*br\s*/?\s*>"
        )  # replace HTML line breaks with newlines
        for field, col in zip(
            [("self", self.admin.modelname.title())] + list(self.field_values()),
            header_cells,
        ):
            col[0].value = field[1]
            col[0].font = Font(bold=True)
            for i, cell in enumerate(col[1:]):
                html_value = render_field(items[i], field[0], self.admin)
                cleaned = htmlparser.unescape(
                    newline_regex.sub(r"\n", strip_tags(html_value))
                )
                cell.value = cleaned

        return xlsxresponse(workbook, workbook.title)

    def get_object_actions(self, context, element):
        return self.object_actions

    def field_values(self):
        for accessor in self.fields:
            fieldchain = resolve_relationship(self.model, accessor)
            if not fieldchain:
                yield accessor, accessor.replace("_", " ").title()
            else:
                yield accessor, pretty_fieldname(fieldchain[-1][1])


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
