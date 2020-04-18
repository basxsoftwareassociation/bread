import urllib
from html.parser import HTMLParser

import pkg_resources

import django_filters
from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models, transaction
from django.forms import HiddenInput
from django.forms.models import ModelForm
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    TemplateView,
    UpdateView,
)
from django_filters.views import FilterView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from .forms.forms import inlinemodelform_factory
from .utils import (
    get_modelfields,
    listurl,
    modelname,
    parse_fieldlist,
    pretty_fieldname,
    xlsxresponse,
)


class BrowseView(PermissionListMixin, FilterView):
    template_name = "bread/list.html"
    fields = None

    def __init__(self, admin, fields=["__all__"], *args, **kwargs):
        if "filterset_fields" not in kwargs:
            kwargs["filterset_fields"] = parse_fieldlist(self.model, fields)
        super().__init__(*args, **kwargs)
        self.modelfields = get_modelfields(
            self.model, parse_fieldlist(self.model, fields)
        )

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]

    def get(self, *args, **kwargs):
        if "reset" in self.request.GET:
            return redirect(self.request.path)
        if "export" in self.request.GET:
            return self.as_excel()

        return super().get(*args, **kwargs)

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

        workbook = openpyxl.Workbook()
        workbook.title = modelname(self.model, plural=True)
        header_cells = workbook.active.iter_cols(
            min_row=1, max_col=len(self.modelfields), max_row=len(items) + 1
        )
        htmlparser = HTMLParser()
        for field, col in zip(self.modelfields, header_cells):
            col[0].value = pretty_fieldname(field)
            col[0].font = Font(bold=True)
            for i, cell in enumerate(col[1:]):
                cell.value = htmlparser.unescape(
                    strip_tags(getattr(items[i], f"get_{field.name}_display")())
                )

        return xlsxresponse(workbook, workbook.title)

    def get_queryset(self):
        # prefetch fields
        ret = super().get_queryset()
        for field in self.modelfields:
            if field.is_relation and not isinstance(field, GenericForeignKey):
                if field.many_to_one or field.one_to_one:
                    ret = ret.select_related(field.name)
                elif field.one_to_many:
                    ret = ret.prefetch_related(field.related_name)
                elif field.many_to_many:
                    ret = ret.prefetch_related(field.name)

        # order fields
        order = self.request.GET.get("order")
        if order:
            ret = ret.order_by(*order.split(","))
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
                            attrs={"type": "date", "class": "validate datepicker"}
                        )
                    },
                },
            },
        }
        config["exclude"] = [
            f.name
            for f in self.model._meta.get_fields()
            if isinstance(f, models.FileField)
        ]
        config["fields"] = self.filterset_fields

        meta = type("Meta", (object,), config)
        filterset = type(
            f"{self.model._meta.object_name}FilterSet",
            (django_filters.FilterSet,),
            {"Meta": meta},
        )
        return filterset


class ReadView(PermissionRequiredMixin, DetailView):
    template_name = "bread/detail.html"
    fields = None
    accept_global_perms = True

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]

    def __init__(self, admin, fields=["__all__"], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modelfields = get_modelfields(
            self.model, parse_fieldlist(self.model, fields)
        )


class CustomFormMixin:
    """Allows to pass initial parameters via GET parameters and
    converts n-to-many fields into inline forms
    """

    def get_initial(self, *args, **kwargs):
        ret = super().get_initial(*args, **kwargs)
        ret.update(self.request.GET.dict())
        return ret

    def get_form_class(self, form=ModelForm):
        return inlinemodelform_factory(
            self.request, self.model, self.object, self.modelfields, form
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # hide predefined fields passed in GET parameters
        for field in form.fields:
            if field in self.request.GET:
                form.fields[field].widget = HiddenInput()

        # make sure fields appear in original order
        form.order_fields([field.name for field in self.modelfields])
        return form

    def form_valid(self, form):
        with transaction.atomic():
            # set generic foreign key values
            for field in self.modelfields:
                if isinstance(field, GenericForeignKey):
                    setattr(self.object, field.name, form.cleaned_data[field.name])
            self.object = form.save()
            form.save_inline(self.object)
        return super().form_valid(form)

    def get_success_url(self):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return listurl(self.model)


class AddView(CustomFormMixin, PermissionRequiredMixin, CreateView):
    template_name = "bread/custom_form.html"
    accept_global_perms = True

    def __init__(self, admin, fields=["__all__"], *args, **kwargs):
        self.modelfields = get_modelfields(
            self.model, parse_fieldlist(kwargs["model"], fields, is_form=True)
        )
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.add_{self.model.__name__.lower()}"]

    def get_permission_object(self):
        return None


class GeneralUpdate(CustomFormMixin, PermissionRequiredMixin, UpdateView):
    template_name = "bread/custom_form.html"
    accept_global_perms = True

    def __init__(self, admin, fields=["__all__"], *args, **kwargs):
        self.modelfields = get_modelfields(
            self.model, parse_fieldlist(kwargs["model"], fields, is_form=True)
        )
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.change_{self.model.__name__.lower()}"]


class GeneralDelete(PermissionRequiredMixin, DeleteView):
    template_name = "bread/confirm_delete.html"
    accept_global_perms = True

    def __init__(self, admin, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.delete_{self.model.__name__.lower()}"]

    def get_success_url(self):
        if self.request.GET.get("next"):
            return urllib.parse.unquote(self.request.GET["next"])
        return listurl(self.model)


class Overview(LoginRequiredMixin, TemplateView):
    """Lists all breadapps which have an index url"""

    template_name = "bread/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_urls"] = []

        for entrypoint in pkg_resources.iter_entry_points(
            group="breadapp", name="appname"
        ):
            fullappname = entrypoint.load()
            appname = fullappname.split(".")[-1]
            label = apps.get_app_config(appname).verbose_name
            context["app_urls"].append((reverse(f"bread:{appname}:index"), label))
        context["app_urls"] = sorted(context["app_urls"], key=lambda a: a[1])

        return context
