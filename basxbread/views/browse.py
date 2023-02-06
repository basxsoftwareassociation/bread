from typing import Callable, Iterable, List, NamedTuple, Optional, Union

import django_filters
import htmlgenerator as hg
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from django.views.generic import ListView
from djangoql.exceptions import DjangoQLError
from djangoql.queryset import apply_search
from guardian.mixins import PermissionListMixin

from .. import layout
from ..utils import (
    Link,
    ModelHref,
    filter_fieldlist,
    generate_excel,
    link_with_urlparameters,
    queryset_from_fields,
    resolve_modellookup,
    xlsxresponse,
)
from .util import BaseView

FILTER_PREFIX = "filter_"


class BulkAction(NamedTuple):
    name: str
    label: str
    action: Callable[[HttpRequest, models.query.QuerySet], Optional[HttpResponse]]
    iconname: str = "fade"
    permissions: List[str] = []

    def has_permission(self, request, obj=None):
        return all(
            [
                request.user.has_perm(perm, obj) or request.user.has_perm(perm)
                for perm in self.permissions
            ]
        )


def default_bulkactions(model, columns=["__all__"]):
    return (
        BulkAction(
            "excel",
            label=_("Excel"),
            iconname="download",
            action=lambda request, qs: export(qs, columns),
            permissions=[f"{model._meta.app_label}.view_{model._meta.model_name}"],
        ),
        BulkAction(
            "delete",
            label=_("Delete"),
            iconname="trash-can",
            action=delete,
            permissions=[f"{model._meta.app_label}.add_{model._meta.model_name}"],
        ),
    )


def order_queryset_by_urlparameter(qs, order):
    """Can used to order a queryset by a user-provided string, e.g. through a GET query parameter"""
    if order:
        fieldname = order[1:] if order.startswith("-") else order

        if order.endswith("__int"):
            order = order[: -len("__int")]
            qs = qs.order_by(
                models.functions.Cast(fieldname, models.IntegerField()).desc()
                if order.startswith("-")
                else models.functions.Cast(fieldname, models.IntegerField())
            )
        else:
            try:
                field = resolve_modellookup(
                    qs.model, fieldname.replace(LOOKUP_SEP, ".")
                )[-1]
            except AttributeError:
                # check if the field to order from is an annotation
                field = qs.query.annotations[fieldname]
            if isinstance(field, (models.TextField, models.CharField)):
                qs = qs.order_by(
                    models.functions.Lower(fieldname).desc()
                    if order.startswith("-")
                    else models.functions.Lower(fieldname)
                )
            else:
                qs = qs.order_by(order)
    return qs


class BrowseView(BaseView, LoginRequiredMixin, PermissionListMixin, ListView):
    """TODO: documentation"""

    orderingurlparameter: str = "ordering"

    # see basxbread/static/js/main.js:submitbulkaction and basxbread/layout/components/datatable.py
    objectids_urlparameter: str = "_selected"

    bulkaction_urlparameter: str = "_bulkaction"
    items_per_page_options: Optional[Iterable[int]] = None
    itemsperpage_urlparameter: str = "itemsperpage"
    search_urlparameter: str = "q"

    title: Union[hg.BaseElement, str] = ""
    columns: Iterable[Union[str, layout.datatable.DataTableColumn]] = ("__all__",)
    rowclickaction: Optional[Link] = None
    filterconfig: Optional[tuple] = None
    filterset_class: Optional[django_filters.FilterSet] = None

    # bulkactions: List[(Link, function(request, queryset))]
    # - link.js should be a slug and not a URL
    # - if the function returns a HttpResponse, the response is returned
    #   instead of the browse view result
    bulkactions: Iterable[
        Union[Link, Callable[[HttpRequest, models.QuerySet], Union[None, HttpResponse]]]
    ] = ()

    rowactions: Optional[Iterable[Link]] = None  # list of links
    backurl = None
    primary_button = None

    # if set will be used to save the state of the url parameters and restore them on the next call
    viewstate_sessionkey: Optional[str] = None

    def __init__(self, *args, **kwargs):
        self.orderingurlparameter = (
            kwargs.get("orderingurlparameter") or self.orderingurlparameter
        )
        self.itemsperpage_urlparameter = (
            kwargs.get("itemsperpage_urlparameter") or self.itemsperpage_urlparameter
        )
        self.objectids_urlparameter = (
            kwargs.get("objectids_urlparameter") or self.objectids_urlparameter
        )
        self.bulkaction_urlparameter = (
            kwargs.get("bulkaction_urlparameter") or self.bulkaction_urlparameter
        )
        self.items_per_page_options = (
            kwargs.get("items_per_page_options")
            or self.items_per_page_options
            or getattr(settings, "DEFAULT_PAGINATION_CHOICES")
        )
        self.search_urlparameter = (
            kwargs.get("search_urlparameter") or self.search_urlparameter
        )
        self.title = kwargs.get("title") or self.title
        if self.rowactions is None:
            self.rowactions = (BrowseView.editlink(), BrowseView.deletelink())
        self.rowactions = kwargs.get("rowactions") or self.rowactions
        self.model = kwargs.get("model") or self.model
        self.columns = filter_fieldlist(
            self.model, kwargs.get("columns") or self.columns
        )
        self.rowclickaction = kwargs.get("rowclickaction") or self.rowclickaction
        self.backurl = kwargs.get("backurl") or self.backurl
        self.primary_button = kwargs.get("primary_button") or self.primary_button
        self.viewstate_sessionkey = (
            kwargs.get("viewstate_sessionkey") or self.viewstate_sessionkey
        )
        self.filterconfig = kwargs.get("filterconfig") or self.filterconfig
        self.filterset_class = self.filterset_class or parse_filterconfig(
            self.model,
            self.filterconfig
            or (
                ("AND",)
                + tuple(
                    get_filtername(column)
                    for column in self.columns
                    if get_filtername(column)
                )
            ),
            prefix="f",
        )
        super().__init__(*args, **kwargs)
        self.bulkactions = (
            kwargs.get("bulkactions")
            or self.bulkactions
            or default_bulkactions(self.model, self.columns)
        )

    def get_layout(self, **datatable_kwargs):
        # re-mapping the Links because the URL is not supposed to be a real URL but an identifier
        # for the bulk action
        # TODO: This is a bit ugly but we can reuse the Link type for icon, label and permissions
        bulkactions = [
            Link(
                link_with_urlparameters(
                    self.request, **{self.bulkaction_urlparameter: action.name}
                ),
                label=action.label,
                iconname=action.iconname,
            )
            for action in self.bulkactions
            if action.has_permission(self.request)
        ]
        fullqueryset = self.get_final_queryset()
        paginate_by = self.get_paginate_by(fullqueryset)
        if paginate_by is None:
            paginate_by = fullqueryset.count()
        paged_qs = (
            self.paginate_queryset(fullqueryset, paginate_by)[2]
            if paginate_by > 0
            else fullqueryset
        )

        return layout.datatable.DataTable.from_queryset(
            queryset=paged_qs,
            columns=self.columns,
            bulkactions=bulkactions,
            rowactions=self.rowactions,
            # rowactions_dropdown=len(self.rowactions) > 2,  # recommendation from carbon design
            rowactions_dropdown=False,  # will not work with submit-actions, which trigger a modal
            rowclickaction=self.rowclickaction,
            pagination_config=layout.pagination.PaginationConfig(
                items_per_page_options=self.items_per_page_options,
                page_urlparameter=self.page_kwarg,
                paginator=self.get_paginator(fullqueryset, paginate_by),
                itemsperpage_urlparameter=self.itemsperpage_urlparameter,
            )
            if paginate_by > 0
            else None,
            checkbox_for_bulkaction_name=self.objectids_urlparameter,
            title=self.title,
            settingspanel=self.get_settingspanel(),
            backurl=self.backurl,
            primary_button=self.primary_button,
            search_urlparameter=self.search_urlparameter,
            **datatable_kwargs,
        )

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "layout": self._get_layout_cached(),
            "pagetitle": self.title or self.model._meta.verbose_name_plural,
        }

    def get_settingspanel(self):
        existing_params = {}
        for paramname in self.request.GET:
            if not paramname.startswith(FILTER_PREFIX):
                existing_params[paramname] = forms.CharField(
                    widget=forms.HiddenInput(), required=False
                )

        ExistingParamsForm = type("ExistingParamsForm", (forms.Form,), existing_params)

        return build_filterpanel(
            self.filterset_class(self.request.GET, queryset=self.get_final_queryset()),
            ExistingParamsForm(self.request.GET),
        )

    def get_required_permissions(self, request):
        return [f"{self.model._meta.app_label}.view_{self.model.__name__.lower()}"]

    def get(self, *args, **kwargs):
        if "reset" in self.request.GET:
            if (
                self.viewstate_sessionkey
                and self.viewstate_sessionkey in self.request.session
            ):
                del self.request.session[self.viewstate_sessionkey]
            return redirect(self.request.path)
        if self.bulkaction_urlparameter in self.request.GET:
            bulkactions = {
                action.name: action.action
                for action in self.bulkactions
                if action.has_permission(self.request)
            }
            if self.request.GET[self.bulkaction_urlparameter] not in bulkactions:
                messages.error(
                    self.request,
                    _("Action '%s' is not configured for this view")
                    % self.request.GET[self.bulkaction_urlparameter],
                )
            else:
                ret = bulkactions[self.request.GET[self.bulkaction_urlparameter]](
                    self.request, self.get_final_queryset()
                )
                params = self.request.GET.copy()
                del params[self.bulkaction_urlparameter]
                del params[self.objectids_urlparameter]
                if ret is None:
                    return redirect(self.request.path + "?" + params.urlencode())
                return ret
        # for normal GET requests save query if saving state is enabled or reload last state
        if self.viewstate_sessionkey:
            if not self.request.GET and self.request.session.get(
                self.viewstate_sessionkey, None
            ):
                return redirect(
                    self.request.path
                    + "?"
                    + self.request.session[self.viewstate_sessionkey]
                )
            self.request.session[
                self.viewstate_sessionkey
            ] = self.request.GET.urlencode()

        return super().get(*args, **kwargs)

    def get_paginate_by(self, queryset):
        ret = self.request.GET.get(
            self.itemsperpage_urlparameter, self.items_per_page_options[0]
        )
        if str(ret) == "-1":
            return None

        return int(ret)

    def filter_queryset_by_search(self, qs):
        if self.search_urlparameter and self.search_urlparameter in self.request.GET:
            searchquery = self.request.GET[self.search_urlparameter].strip()
            if searchquery.startswith("="):
                try:
                    qs = apply_search(qs, searchquery[1:])
                except DjangoQLError as e:
                    messages.error(
                        self.request,
                        _("Bad filter string '%s': '%s'") % (searchquery, e),
                    )

            else:
                # distinct clause might be necessary in other places too to prevent duplicates
                qs = qs.filter(
                    queryset_from_fields.get_field_queryset(
                        [*self.model._meta.fields, *self.model._meta.many_to_many],
                        searchquery,
                    )
                ).distinct()
        return qs

    def filter_queryset_by_formfilter(self, qs):
        filterset = self.filterset_class(self.request.GET, queryset=qs)
        return filterset.qs

    def filter_queryset_by_selection(self, qs):
        selectedobjects = self.request.GET.getlist(self.objectids_urlparameter)
        if selectedobjects and "all" not in selectedobjects:
            qs &= self.get_queryset().filter(pk__in=selectedobjects)
        return qs

    def get_filtered_queryset(self, qs):
        """Prefetch related tables to speed up queries. Also order result by get-parameters."""
        qs = self.filter_queryset_by_search(qs)
        qs = self.filter_queryset_by_formfilter(qs)
        qs = self.filter_queryset_by_selection(qs)
        return qs

    def get_ordred_queryset(self, qs):
        return order_queryset_by_urlparameter(
            qs, self.request.GET.get(self.orderingurlparameter)
        )

    def get_final_queryset(self):
        # use this instead of get_queryset so we get the correct queryset when subclassing
        if not hasattr(self, "_final_queryset"):
            self._final_queryset = self.get_ordred_queryset(
                self.get_filtered_queryset(self.get_queryset())
            )
        return self._final_queryset

    @staticmethod
    def gen_rowclickaction(modelaction, **kwargs):
        """
        Shortcut to get a Link to a model view.
        The default models views in basxbread are "read", "edit", "delete".
        :param modelaction: A model view whose name has been generated
                            with ``basxbread.utils.urls.model_urlname``
        """
        return Link(
            label="",
            href=ModelHref.from_object(hg.C("row"), modelaction, **kwargs),
            iconname=None,
        )

    @staticmethod
    def editlink(return_to_current=True, **attributes):
        return Link(
            href=ModelHref.from_object(
                hg.C("row"), "edit", return_to_current=return_to_current
            ),
            label=_("Edit"),
            iconname="edit",
            attributes=attributes,
        )

    @staticmethod
    def deletelink(return_to_current=True, **attributes):
        return Link(
            href=ModelHref.from_object(
                hg.C("row"), "delete", return_to_current=return_to_current
            ),
            label=_("Delete"),
            iconname="delete",
            attributes=attributes,
            is_submit=True,
            confirm_text=hg.format(
                _("Are you sure you want to delete {}?"),
                hg.SPAN(hg.STRONG(hg.C("row"))),
            ),
        )


# helper function to export a queryset to excel
def export(queryset, columns):
    if "__all__" in columns:
        columns = filter_fieldlist(queryset.model, columns)
    columndefinitions = {}
    for column in columns:
        if not (
            isinstance(column, layout.datatable.DataTableColumn)
            or isinstance(column, str)
        ):
            raise ValueError(
                "Argument 'columns' needs to be of a list with items of type str "
                f"or DataTableColumn, but found {column}"
            )
        if isinstance(column, str):
            column = layout.datatable.DataTableColumn(
                layout.ObjectFieldLabel(column, "model"),
                layout.ObjectFieldValue(column, "row"),
            )

        columndefinitions[
            hg.render(hg.BaseElement(column.header), {"model": queryset.model})
        ] = lambda row, column=column: hg.render(
            hg.BaseElement(column.cell), {"row": row}
        )

    workbook = generate_excel(queryset, columndefinitions)
    workbook.title = queryset.model._meta.verbose_name
    return xlsxresponse(workbook, workbook.title)


def delete(request, queryset, softdeletefield=None, required_permissions=None):
    if required_permissions is None:
        required_permissions = [
            f"{queryset.model._meta.app_label}.delete_{queryset.model.__name__.lower()}"
        ]

    deleted = 0
    for instance in queryset:
        try:
            if not request.user.has_perm(required_permissions, instance):
                # we throw an exception here because the user not supposed to
                # see the option to delete an object anyway, if he does not have the permssions
                # the queryset should already be filtered
                raise Exception(
                    _("Your user has not the permissions to delete %s") % instance
                )
            if softdeletefield:
                if not getattr(instance, softdeletefield):
                    setattr(instance, softdeletefield, True)
                    instance.save()
                    deleted += 1
            else:
                instance.delete()
                deleted += 1
        except Exception as e:
            messages.error(
                request,
                _("%s could not be deleted: %s") % (object, e),
            )

    messages.success(
        request,
        _("Deleted %(count)s %(modelname)s")
        % {
            "count": deleted,
            "modelname": queryset.model._meta.verbose_name_plural
            if deleted > 1
            else queryset.model._meta.verbose_name,
        },
    )


def restore(request, queryset, softdeletefield, required_permissions=None):
    if required_permissions is None:
        required_permissions = [
            f"{queryset.model._meta.app_label}.change_{queryset.model.__name__.lower()}"
        ]

    restored = 0
    for instance in queryset:
        try:
            if not request.user.has_perm(required_permissions, instance):
                # we throw an exception here because the user not supposed to
                # see the option to restore an object anyway, if he does not have the permssions
                # the queryset should already be filtered
                raise Exception(
                    _("Your user has not the permissions to restore %s") % instance
                )
            if getattr(instance, softdeletefield, False):
                setattr(instance, softdeletefield, False)
                instance.save()
                restored += 1
        except Exception as e:
            messages.error(
                request,
                _("%s could not be restored: %s") % (object, e),
            )

    messages.success(
        request,
        _("Restored %(count)s %(modelname)s")
        % {
            "count": restored,
            "modelname": queryset.model._meta.verbose_name_plural
            if restored > 1
            else queryset.model._meta.verbose_name,
        },
    )


class AndGroup(django_filters.FilterSet):
    prefix = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subgroups = []
        for group in self.subgroup_classes:
            self.subgroups.append(group(*args, **kwargs))
        self.form_prefix = self.prefix

    def filter_queryset(self, queryset):
        for name, value in self.form.cleaned_data.items():
            queryset = self.filters[name].filter(queryset, value)
            assert isinstance(
                queryset, models.QuerySet
            ), "Expected '%s.%s' to return a QuerySet, but got a %s instead." % (
                type(self).__name__,
                name,
                type(queryset).__name__,
            )

        for group in self.subgroups:
            queryset = group.filter_queryset(queryset)

        return queryset

    @property
    def errors(self):
        ret = django_filters.FilterSet.errors.fget(self)
        for subgroup in self.subgroups:
            ret.update(subgroup.errors)
        return ret


class OrGroup(django_filters.FilterSet):
    prefix = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subgroups = []
        for group in self.subgroup_classes:
            self.subgroups.append(group(*args, **kwargs))
        self.form_prefix = self.prefix

    def filter_queryset(self, queryset):
        if (
            len([i for i in self.subgroups if i.form.has_changed()]) == 0
            and len(self.form.cleaned_data) == 0
        ):
            return queryset
        basefilterset = queryset.none()
        for name, value in self.form.cleaned_data.items():
            basefilterset |= self.filters[name].filter(queryset, value)
            assert isinstance(
                basefilterset, models.QuerySet
            ), "Expected '%s.%s' to return a QuerySet, but got a %s instead." % (
                type(self).__name__,
                name,
                type(basefilterset).__name__,
            )
        for group in self.subgroups:
            if group.form.has_changed():  # ignore subgroup with no changes
                basefilterset |= group.filter_queryset(queryset)
        return basefilterset

    @property
    def errors(self):
        ret = django_filters.FilterSet.errors.fget(self)
        for subgroup in self.subgroups:
            ret.update(subgroup.errors)
        return ret


def parse_filterconfig(basemodel, filterconfig, prefix):
    """
    filterconfig: Tree in the form of
                  ("and"
                      ("or", fieldname1, fieldname2),
                      ("or", fieldname3, fieldname4),
                  )
    """
    FILTERSETTYPE = {"and": AndGroup, "or": OrGroup}
    grouptype, *subfields = filterconfig
    if grouptype.lower() not in FILTERSETTYPE:
        raise ValueError(
            f"Invalid filter group specified '{filterconfig[0]}', must be 'and' or 'or'"
        )

    fields = []
    subgroups = []
    n = 0
    for f in subfields:
        if isinstance(f, str):
            try:
                modelfield = get_field(basemodel, f)
            except FieldDoesNotExist:
                continue
            # ignore filefields
            if not isinstance(
                modelfield, (models.FileField, GenericForeignKey, GenericRelation)
            ):
                fields.append(f)
        elif isinstance(f, Iterable):
            subgroups.append(parse_filterconfig(basemodel, f, prefix + str(n)))
            n += 1
        else:
            raise ValueError(
                f"Declared filter field '{f}' is not of type {(str, OrGroup, AndGroup)} but {type(f)}"
            )

    meta = type(
        "Meta",
        (),
        {
            "model": basemodel,
            "fields": fields,
            "filter_overrides": FILTER_OVERRIDES,
        },
    )

    ret = type(
        f"{basemodel.__name__}FilterSet",
        (FILTERSETTYPE[grouptype.lower()],),
        {
            "Meta": meta,
            "subgroup_classes": subgroups,
            "prefix": f"{FILTER_PREFIX}{prefix}",
        },
    )
    return ret


def get_filtername(column):
    if isinstance(column, str):
        return column.replace(".", LOOKUP_SEP)
    if isinstance(column, layout.datatable.DataTableColumn):
        return column.filtername
    return None


def get_field(basemodel, fieldname):
    if LOOKUP_SEP in fieldname:
        relatedfield, rest = fieldname.split(LOOKUP_SEP, 1)
        return get_field(basemodel._meta.get_field(relatedfield).related_model, rest)
    return basemodel._meta.get_field(fieldname)


def build_filterpanel(filterset, hiddenparams_form):
    return hg.DIV(
        hg.DIV(
            hg.DIV(
                hg.DIV(_("Filter"), style="margin-bottom: 1rem"),
                hg.DIV(
                    layout.components.forms.Form(
                        hiddenparams_form,
                        hg.BaseElement(
                            *[
                                layout.components.forms.FormField(hidden)
                                for hidden in hiddenparams_form.fields
                            ],
                            _build_filter_ui_recursive(filterset),
                        ),
                        _class="filterform",
                        method="GET",
                    ),
                    style="display: flex",
                ),
            ),
            style="display: flex; padding: 24px 32px 0 32px",
        ),
        hg.DIV(
            layout.button.Button(
                _("Cancel"),
                buttontype="ghost",
                onclick="this.closest('.settingscontainer').style.display = 'none'",
            ),
            layout.button.Button.from_link(
                Link(
                    label=_("Reset"),
                    href=hg.format("{}?reset=1", hg.C("request").path),
                    iconname=None,
                ),
                buttontype="secondary",
            ),
            layout.button.Button(
                pgettext_lazy("apply filter", "Filter"),
                onclick="""this.closest('.filterpanel').querySelector('.filterform').submit();""",
            ),
            style="display: flex; justify-content: flex-end; margin-top: 24px",
            _class="bx--modal-footer",
        ),
        _class="filterpanel",
        style="background-color: #fff",
    )


def _build_filter_ui_recursive(filterset):
    flexdir = ""
    if isinstance(filterset, AndGroup):
        flexdir = "column"
    elif isinstance(filterset, OrGroup):
        flexdir = "row"

    return hg.DIV(
        layout.components.forms.Form(
            filterset.form,
            *[
                layout.components.forms.FormField(
                    f, no_wrapper=True, style="margin-bottom: 1rem; margin-right: 1rem"
                )
                for f in filterset.form.fields
            ],
            standalone=False,
            *[_build_filter_ui_recursive(f) for f in filterset.subgroups],
        ),
        style="display: flex; flex-direction: " + flexdir,
    )


FILTER_OVERRIDES = {
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
}
