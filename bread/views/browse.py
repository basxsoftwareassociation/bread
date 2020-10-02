import copy
import re
from html.parser import HTMLParser

import django_filters
from crispy_forms.layout import Layout
from crispy_forms.utils import TEMPLATE_PACK
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldError
from django.db import models
from django.db.models.functions import Lower
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django_filters.views import FilterView
from guardian.mixins import PermissionListMixin

from ..formatters import render_field
from ..forms.forms import FilterForm
from ..layout import TR, LoopLayout, ObjectActionsDropDown, convert_to_formless_layout
from ..utils import (
    CustomizableClass,
    filter_fieldlist,
    pretty_fieldname,
    resolve_relationship,
    xlsxresponse,
)


class BrowseView(
    CustomizableClass, LoginRequiredMixin, PermissionListMixin, FilterView
):
    template_name = f"{TEMPLATE_PACK}/list.html"
    admin = None
    fields = None
    filterfields = None
    page_kwarg = "browsepage"  # need to use something different than the default "page" because we also filter through kwargs

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        # need a deep copy because convert_to_formless_layout will modify the value
        # which is problematic if we share the same layout-object with an edit view
        self.fields_argument = copy.deepcopy(kwargs.get("fields", self.fields))
        self.wrapper_argument = copy.deepcopy(kwargs.get("wrapper", None))

        # incrementally try to create a filter from the given field and ignore fields which cannot be used
        kwargs["filterset_fields"] = []
        for field in filter_fieldlist(
            self.model, kwargs.get("filterfields", self.filterfields)
        ):
            try:
                generate_filterset_class(
                    self.model, kwargs["filterset_fields"] + [field]
                )
                kwargs["filterset_fields"].append(field)
            except (TypeError, AssertionError) as e:
                print(f"Warning: Specified filter field {field} cannot be used: {e}")

        super().__init__(*args, **kwargs)

    def setup(self, request, *args, **kwargs):
        self.layout = self.get_wrapper_layout(
            request, self.wrapper_argument, self.fields_argument
        )
        self.fields = self.get_fields(
            self.get_inline_layout(request, self.fields_argument)
        )
        return super().setup(request, *args, **kwargs)

    def get_inline_layout(self, request, fields_argument):
        """fields_argument is anything that has been passed as ``fields`` to the as_view function"""

        fields_argument = copy.deepcopy(fields_argument)
        if not isinstance(fields_argument, Layout):
            layoutfields = filter_fieldlist(self.model, fields_argument)
            fields_argument = Layout(
                TR.with_td(ObjectActionsDropDown(), "self", *layoutfields),
            )
        convert_to_formless_layout(fields_argument, show_label=False)
        return fields_argument

    def get_wrapper_layout(self, request, wrapper_argument, fields_argument):
        """wrapper_argument is anything that has been passed as ``wrapper`` to the as_view function"""

        wrapper_argument = copy.deepcopy(wrapper_argument)
        if not isinstance(wrapper_argument, Layout):
            wrapper_argument = Layout(
                LoopLayout(
                    "object_list",
                    "object",
                    self.get_inline_layout(request, fields_argument),
                )
            )
        convert_to_formless_layout(wrapper_argument, show_label=False)
        return wrapper_argument

    def get_fields(self, layout):
        def _get_fields_recursive(l):
            if hasattr(l, "field"):
                if l.field == "self":
                    yield self.admin.verbose_modelname
                else:
                    yield l.field
            else:
                for field in getattr(l, "fields", ()):
                    yield from _get_fields_recursive(field)

        return list(_get_fields_recursive(layout))

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]

    def get_filterset_class(self):
        return generate_filterset_class(self.model, self.filterset_fields)

    def get(self, *args, **kwargs):
        if "reset" in self.request.GET:
            return redirect(self.request.path)
        if "export" in self.request.GET:
            return self.as_excel()

        return super().get(*args, **kwargs)

    def get_queryset(self):
        """Prefetch related tables to speed up queries. Also order result by get-parameters."""
        ret = super().get_queryset()
        # quite a few try-catches because we want to leverage djangos internal checks on the
        # prefetchs instead of implementing it again in our own code
        for accessor in self.fields:
            try:
                list(self.model.objects.none().select_related(accessor))
                ret = ret.select_related(accessor)
            except FieldError:
                # make sure all elements of the accessor path are modelfields
                prefetch_accessors = []
                for model, field in resolve_relationship(self.model, accessor):
                    if not field.is_relation:
                        break
                    prefetch_accessors.append(field.name)
                    ret = ret.prefetch_related(
                        models.constants.LOOKUP_SEP.join(prefetch_accessors)
                    )

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

    def sortnames(self):
        for accessor in self.fields:
            fieldchain = resolve_relationship(self.model, accessor)
            if not fieldchain:
                yield "", accessor.replace("_", " ").title()
            else:
                try:
                    self.model.objects.none().order_by(accessor)
                except FieldError:
                    accessor = ""
                yield accessor, " ".join([pretty_fieldname(f[1]) for f in fieldchain])

    def field_values(self):
        for accessor in self.fields:
            fieldchain = resolve_relationship(self.model, accessor)
            if not fieldchain:
                yield accessor, accessor.replace("_", " ").title()
            else:
                yield accessor, pretty_fieldname(fieldchain[-1][1])


class TreeView(BrowseView):
    template_name = f"{TEMPLATE_PACK}/tree.html"
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
