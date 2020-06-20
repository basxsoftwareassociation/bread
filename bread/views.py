import re
import urllib
from html.parser import HTMLParser

import django_filters
import pygraphviz
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django.views.generic import CreateView
from django.views.generic import DeleteView as DjangoDeleteView
from django.views.generic import DetailView, TemplateView, UpdateView
from django_extensions.management.modelviz import ModelGraph, generate_dot
from django_filters.views import FilterView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from .forms.forms import inlinemodelform_factory
from .utils import get_modelfields, parse_fieldlist, pretty_fieldname, xlsxresponse


class FilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_method = "get"
        self.helper.add_input(Submit("submit", "Filter"))


class BrowseView(LoginRequiredMixin, PermissionListMixin, FilterView):
    template_name = "bread/list.html"
    admin = None
    fields = None

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        self.modelfields = get_modelfields(
            self.model,
            parse_fieldlist(
                self.model, kwargs.get("fields") or self.admin.browsefields
            ),
            admin=self.admin,
        )

        def filterset_fields(field):
            try:
                field = self.model._meta.get_field(field)
            except FieldDoesNotExist:
                return False
            if field.one_to_many:
                return False
            return True

        kwargs["filterset_fields"] = filter(
            filterset_fields,
            parse_fieldlist(
                self.model, kwargs.get("filterfields") or self.admin.filterfields,
            ),
        )
        kwargs["model"] = self.model
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]

    def get(self, *args, **kwargs):
        if "reset" in self.request.GET:
            return redirect(self.request.path)
        if "export" in self.request.GET:
            return self.as_excel()

        return super().get(*args, **kwargs)

    def get_queryset(self):
        # prefetch fields
        ret = super().get_queryset()
        for name, field in self.modelfields.items():
            if field.is_relation and not isinstance(field, GenericForeignKey):
                if field.many_to_one or field.one_to_one:
                    ret = ret.select_related(name)
                elif field.one_to_many and not isinstance(field, GenericRelation):
                    ret = ret.prefetch_related(field.related_name)
                elif field.many_to_many:
                    ret = ret.prefetch_related(name)

        # order fields
        order = self.request.GET.get("order")
        if order:
            fields = order.split(",")
            ordering = [
                Lower(f[1:]).desc() if f.startswith("-") else Lower(f) for f in fields
            ]
            ret = ret.order_by(*ordering)
        return ret

    def get_filterset_class(self):
        # make text-based fields filtering with icontains and datefield as range
        config = {
            "model": self.model,
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
            for f in self.model._meta.get_fields()
            if isinstance(f, models.FileField) or isinstance(f, GenericForeignKey)
        ]
        config["fields"] = self.filterset_fields
        config["form"] = FilterForm

        meta = type("Meta", (object,), config)
        filterset = type(
            f"{self.model._meta.object_name}FilterSet",
            (django_filters.FilterSet,),
            {"Meta": meta},
        )
        return filterset

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
            min_row=1, max_col=len(self.modelfields), max_row=len(items) + 1
        )
        htmlparser = HTMLParser()
        newline_regex = re.compile(
            r"<\s*br\s*/?\s*>"
        )  # replace HTML line breaks with newlines
        for field, col in zip(self.modelfields.values(), header_cells):
            col[0].value = pretty_fieldname(field)
            col[0].font = Font(bold=True)
            for i, cell in enumerate(col[1:]):
                html_value = self.admin.render_field(items[i], field.name)
                cell.value = htmlparser.unescape(
                    strip_tags(newline_regex.sub(r"\n", html_value))
                )

        return xlsxresponse(workbook, workbook.title)


class TreeView(BrowseView):
    template_name = "bread/tree.html"
    parent_accessor = None

    def __init__(self, parent_accessor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_accessor = parent_accessor

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
                ret[node] = None
                if node.pk in children:
                    ret[node] = build_tree(children[node.pk])
            return ret

        return build_tree(children[None])


class ReadView(PermissionRequiredMixin, DetailView):
    template_name = "bread/detail.html"
    admin = None
    accept_global_perms = True

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        super().__init__(*args, **kwargs)
        self.modelfields = get_modelfields(
            self.model,
            parse_fieldlist(self.model, kwargs.get("fields") or self.admin.readfields),
            admin=self.admin,
        )

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]


class CustomFormMixin:
    """This mixin takes care of the following things:
    - Allows to pass initial values for form fields via the GET query
    - Converts n-to-many fields into inline forms
    - Set GenericForeignKey fields before saving (not supported by default in django)
    - If "next" is in the GET query redirect to there on success
    """

    def get_initial(self, *args, **kwargs):
        ret = super().get_initial(*args, **kwargs)
        ret.update(self.request.GET.dict())
        return ret

    def get_form_class(self, form=forms.models.ModelForm):
        return inlinemodelform_factory(
            self.request,
            self.model,
            self.object,
            self.modelfields.values(),
            form,
            self.layout,
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # hide or disable predefined fields passed in GET parameters
        if self.request.method != "POST":
            for field in form.fields:
                if field in self.request.GET:
                    form.fields[field].widget.attrs["readonly"] = True

        # make sure fields appear in original order
        form.order_fields(self.modelfields.keys())
        return form

    def form_valid(self, form):
        with transaction.atomic():
            # set generic foreign key values
            self.object = form.save()
            for name, field in self.modelfields.items():
                if isinstance(field, GenericForeignKey):
                    setattr(self.object, name, form.cleaned_data[name])
            form.save_inline(self.object)
        return super().form_valid(form)

    def get_success_url(self):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return self.admin.reverse("index")


class EditView(
    CustomFormMixin, SuccessMessageMixin, PermissionRequiredMixin, UpdateView
):
    template_name = "bread/custom_form.html"
    admin = None
    accept_global_perms = True

    def get_success_message(self, cleaned_data):
        return f"Saved {self.object}"

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        self.modelfields = get_modelfields(
            self.model,
            parse_fieldlist(
                self.model, kwargs.get("fields") or self.admin.editfields, is_form=True
            ),
            admin=self.admin,
        )
        super().__init__(*args, **kwargs)

    @property
    def layout(self):
        return self.admin.get_editlayout(self.request)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.change_{self.model.__name__.lower()}"]


class AddView(
    CustomFormMixin, SuccessMessageMixin, PermissionRequiredMixin, CreateView
):
    template_name = "bread/custom_form.html"
    admin = None
    accept_global_perms = True

    def get_success_message(self, cleaned_data):
        return f"Added {self.object}"

    def __init__(self, admin, *args, **kwargs):
        self.admin = admin
        self.model = admin.model
        self.modelfields = get_modelfields(
            self.model,
            parse_fieldlist(
                self.model, kwargs.get("fields") or self.admin.addfields, is_form=True
            ),
            admin=self.admin,
        )
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.add_{self.model.__name__.lower()}"]

    @property
    def layout(self):
        return self.admin.get_addlayout(self.request)

    def get_permission_object(self):
        return None


class DeleteView(PermissionRequiredMixin, SuccessMessageMixin, DjangoDeleteView):
    template_name = "bread/confirm_delete.html"
    admin = None
    accept_global_perms = True

    def __init__(self, admin, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin = admin

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.delete_{self.model.__name__.lower()}"]

    def get_success_url(self):
        messages.info(self.request, f"Deleted {self.object}")
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return self.admin.reverse("index")


class Overview(LoginRequiredMixin, TemplateView):
    """Lists all breadapps which have an index url"""

    template_name = "bread/overview.html"
    adminsite = None

    def __init__(self, adminsite, *args, **kwargs):
        self.adminsite = adminsite
        super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_urls"] = {}
        for admin in self.adminsite._registry.values():
            if "index" in admin.get_urls():
                app_label = getattr(admin, "app_label", admin.model._meta.app_label)
                if app_label not in context["app_urls"]:
                    context["app_urls"][app_label] = []
                context["app_urls"][app_label].append(
                    (admin.reverse("index"), admin.verbose_modelname)
                )
                for app, admins in context["app_urls"].items():
                    context["app_urls"][app] = sorted(admins, key=lambda a: a[1])

        context["app_urls"] = {k: v for k, v in sorted(context["app_urls"].items())}

        return context


class DataModel(LoginRequiredMixin, TemplateView):
    """Show the datamodel of the whole application"""

    template_name = "bread/datamodel.html"

    def get(self, request, *args, **kwargs):
        if "download" in request.GET:
            response = HttpResponse(
                self._render_svg().encode(), content_type="image/svg+xml"
            )
            response["Content-Disposition"] = f'inline; filename="datamodel.svg"'
            return response
        return super().get(request, *args, **kwargs)

    def _render_svg(self):
        # TODO: make this display nicer and split by app
        graph_models = ModelGraph(all_applications=True, app_labels=None)
        graph_models.generate_graph_data()
        return (
            pygraphviz.AGraph(
                generate_dot(
                    graph_models.get_graph_data(),
                    template="django_extensions/graph_models/django2018/digraph.dot",
                )
            )
            .draw(format="svg", prog="dot")
            .decode()
        )

    def get_context_data(self, **kwargs):
        ret = super().get_context_data(**kwargs)
        # force SVG to be match page-layout instead of fixed width and height
        ret["datamodel"] = re.sub(
            'svg width="[0-9]*pt" height="[0-9]*pt"', "svg", self._render_svg()
        )
        return ret
